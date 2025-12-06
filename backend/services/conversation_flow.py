"""
Conversation flow manager for language matching workflow
"""
import logging
import random
from datetime import datetime
from backend.db.accessors import (
    add_language_for_user,
    add_to_user_table,
    get_user_given_language,
    set_last_agent_message,
    get_last_agent_context,
    get_latest_voice_message_language,
    clear_last_agent_context,
)
from backend.db.database import get_db_session
from backend.db.models import Language, User
from backend.api.series_api_client import send_message, create_group_chat
from backend.services.language_mapper import get_language_name

logger = logging.getLogger(__name__)

# In-memory conversation state store (per-process)
_CONVERSATION_STATES = {}


def is_new_language_for_user(phone_number: str, language_name: str):
    """
    Check if a language is new for a user by querying the Language database table.
    The agent remembers what languages the user has from the database.
    """
    session = get_db_session()
    try:
        logger.info(f"🔍 CHECKING DATABASE: Querying Language table to see if user {phone_number} already has language '{language_name}'")
        existing = session.query(Language).filter_by(
            phone_number=phone_number,
            language_name=language_name
        ).first()
        
        if existing:
            logger.info(f"✅ LANGUAGE FOUND IN DATABASE: User {phone_number} already has '{language_name}' in Language table")
            logger.info(f"   Agent remembers this language from database - will use existing language workflow")
        else:
            logger.info(f"🆕 NEW LANGUAGE: User {phone_number} does not have '{language_name}' in Language table - this is a new language")
        
        return existing is None
    except Exception as e:
        logger.error(f"Error checking language in database: {e}", exc_info=True)
        return True  # Default to new language if error
    finally:
        session.close()


def get_conversation_state(phone_number: str):
    """Get current conversation state for a user (stored in a simple way)"""
    # In production, persist to DB/redis; here we keep per-process memory
    return _CONVERSATION_STATES.get(phone_number)


def set_conversation_state(phone_number: str, state: str, language_name: str = None, matched_user_phone: str = None, shown_user_phones: list = None):
    """Set conversation state for a user"""
    existing_state = _CONVERSATION_STATES.get(phone_number) or {}
    if shown_user_phones is None:
        shown_user_phones = existing_state.get('shown_user_phones', [])

    _CONVERSATION_STATES[phone_number] = {
        'state': state,
        'language_name': language_name,
        'matched_user_phone': matched_user_phone,
        'shown_user_phones': shown_user_phones
    }


def clear_conversation_state(phone_number: str):
    """Clear conversation state for a user"""
    if phone_number in _CONVERSATION_STATES:
        del _CONVERSATION_STATES[phone_number]


def reset_conversation(phone_number: str):
    """
    Clear in-memory and persisted agent context to restart workflows cleanly.
    """
    clear_conversation_state(phone_number)
    try:
        clear_last_agent_context(phone_number)
    except Exception:
        logger.exception(f"Failed clearing persisted agent context for {phone_number}")


def handle_new_language_detected(phone_number: str, language_name: str, chat_id: int):
    """
    Handle when a new language is detected for a user
    
    Args:
        phone_number: User's phone number
        language_name: Detected language name
        chat_id: Current chat ID
    """
    # Check if this is a new language
    if not is_new_language_for_user(phone_number, language_name):
        logger.debug(f"Language {language_name} already exists for {phone_number}")
        return
    
    # Set conversation state
    set_conversation_state(phone_number, 'asking_add_language', language_name)
    
    # Send message asking if they want to add the language
    # phone_number is the user who sent the message (from_phone from event)
    message = "I noticed this is a new language for you. Do you want me to add this language to our table for future matching?"
    
    # Log that agent is automatically responding to voice message
    logger.info(f"🤖 AGENT AUTO-RESPONSE TRIGGERED: Agent number (+16463230991) is automatically sending message to user {phone_number}")
    logger.info(f"   Reason: New language '{language_name}' detected from voice message")
    logger.info(f"   Message: '{message[:50]}...'")
    
    send_message(phone_number, message, chat_id)
    # Persist context so we can rebuild state across events/restarts
    set_last_agent_message(
        phone_number,
        message,
        state='asking_add_language',
        language_name=language_name,
        matched_user_phone=None,
        shown_user_phones=[],
    )
    
    logger.info(f"✅ Agent (+16463230991) sent message to user {phone_number} about adding language {language_name}")


def send_random_matching_user(phone_number: str, language_name: str, chat_id: int):
    """
    Automatically find and send a random matching user from the database.
    This is called automatically without waiting for user response.
    
    Args:
        phone_number: User's phone number (sender)
        language_name: Language to match on
        chat_id: Current chat ID
    """
    logger.info(f"🔍 AUTO-MATCHING: Agent (+16463230991) automatically finding matching user for {phone_number} with language '{language_name}'")
    logger.info(f"   Querying Language database table...")
    
    # Find matching users (users who have this language in Language table)
    matching_users = get_users_with_language(language_name)
    logger.info(f"📊 Found {len(matching_users)} total users with language '{language_name}' in database")
    
    # Filter out the requesting user
    matching_users = [u for u in matching_users if u['phone_number'] != phone_number]
    logger.info(f"📊 After filtering out requesting user ({phone_number}), {len(matching_users)} matching users available")
    
    if not matching_users:
        # No matching users found
        message = "Unfortunately, there are no other users who know this language currently."
        logger.info(f"❌ No matching users found for {phone_number} with language {language_name}")
        send_message(phone_number, message, chat_id)
        return
    
    # Show random matching user from database
    matched_user = random.choice(matching_users)
    matched_phone = matched_user.get('phone_number', 'N/A')
    matched_name = f"{matched_user.get('f_name', '')} {matched_user.get('l_name', '')}".strip() or 'Not provided'
    
    logger.info(f"🎲 RANDOM SELECTION: Agent (+16463230991) randomly selected user from Language table:")
    logger.info(f"   Selected User Phone: {matched_phone}")
    logger.info(f"   Selected User Name: {matched_name}")
    logger.info(f"   Selected User Bio: {'Yes' if matched_user.get('bio') else 'No'}")
    
    shown_phones = [matched_phone]
    set_conversation_state(phone_number, 'showing_profile', language_name, matched_phone, shown_phones)
    logger.info(f"💾 CONVERSATION STATE UPDATED: User {phone_number} → state='showing_profile', matched_user={matched_phone}")
    
    # Format profile information - MUST include phone, first name, last name from database
    profile_text = f"Here's a user who knows {language_name}:\n\n"
    
    # Always include phone number (REQUIRED)
    profile_text += f"Phone: {matched_phone}\n"
    
    # Build name - MUST include first name and last name separately
    f_name = matched_user.get('f_name', '').strip()
    l_name = matched_user.get('l_name', '').strip()
    
    # Always show first name and last name separately
    if f_name:
        profile_text += f"First Name: {f_name}\n"
    else:
        profile_text += f"First Name: Not provided\n"
    
    if l_name:
        profile_text += f"Last Name: {l_name}\n"
    else:
        profile_text += f"Last Name: Not provided\n"
    
    # Also include full name for clarity
    if f_name or l_name:
        profile_text += f"Full Name: {f_name} {l_name}".strip() + "\n"
    
    # Always include bio (even if empty)
    bio = matched_user.get('bio', '')
    if bio:
        profile_text += f"Bio: {bio}\n"
    else:
        profile_text += f"Bio: Not provided\n"
    
    profile_text += f"\nWould you like a group chat created with this user?"
    
    logger.info(f"📤 SENDING USER PROFILE FROM DATABASE:")
    logger.info(f"   FROM: Agent (+16463230991)")
    logger.info(f"   TO: User {phone_number}")
    logger.info(f"   PROFILE DATA (from Language table):")
    logger.info(f"      - Phone: {matched_phone}")
    logger.info(f"      - Name: {' '.join([f_name, l_name]) if f_name or l_name else 'Not provided'}")
    logger.info(f"      - Bio: {bio if bio else 'Not provided'}")
    logger.info(f"   Language: {language_name}")
    
    send_message(phone_number, profile_text, chat_id)
    set_last_agent_message(
        phone_number,
        profile_text,
        state='showing_profile',
        language_name=language_name,
        matched_user_phone=matched_phone,
        shown_user_phones=shown_phones,
    )
    logger.info(f"✅ PROFILE SENT SUCCESSFULLY: Agent (+16463230991) sent profile of {matched_phone} to user {phone_number}")


def handle_existing_language_detected(phone_number: str, language_name: str, chat_id: int):
    """
    Handle when a user sends a voice message in a language they already have in the table.
    Asks if they want to be matched.
    
    Args:
        phone_number: User's phone number
        language_name: Detected language name (already exists for user)
        chat_id: Current chat ID
    """
    # Set conversation state to ask about matching
    set_conversation_state(phone_number, 'asking_matching', language_name)
    logger.info(f"💾 CONVERSATION STATE SET: User {phone_number} → state='asking_matching', language='{language_name}'")
    
    # Send message asking if they want to be matched
    message = "We have your language on file, do you want to be matched with other person who know this language?"
    
    # Log that agent is automatically responding to voice message
    logger.info(f"🤖 AGENT AUTO-RESPONSE TRIGGERED: Agent number (+16463230991) is automatically sending message to user {phone_number}")
    logger.info(f"   Reason: Existing language '{language_name}' detected from voice message")
    logger.info(f"   Message: '{message[:50]}...'")
    
    send_message(phone_number, message, chat_id)
    set_last_agent_message(
        phone_number,
        message,
        state='asking_matching',
        language_name=language_name,
        matched_user_phone=None,
        shown_user_phones=[],
    )
    
    logger.info(f"✅ Agent (+16463230991) sent message to user {phone_number} about matching for existing language {language_name}")



def handle_add_language_response(phone_number: str, response_text: str, language_name: str, chat_id: int):
    """
    Handle user's response to adding language question
    
    Args:
        phone_number: User's phone number
        response_text: User's response (should be "yes" or "no")
        language_name: Language being discussed
        chat_id: Current chat ID
    """
    response_lower = response_text.lower().strip()
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah']:
        # Add language to database
        add_language_for_user(language_name, phone_number)
        logger.info(f"✅ User {phone_number} added language {language_name} to database")
        
        # Automatically send a random matching user (no need to ask)
        logger.info(f"🤖 AUTO-MATCHING: Agent (+16463230991) automatically finding and sending matching user for {phone_number}")
        send_random_matching_user(phone_number, language_name, chat_id)
        
        logger.info(f"✅ User {phone_number} added language {language_name}, automatically sent matching user profile")
    else:
        # User declined
        clear_conversation_state(phone_number)
        message = "No problem! Let me know if you change your mind."
        send_message(phone_number, message, chat_id)
        set_last_agent_message(
            phone_number,
            message,
            state=None,
            language_name=None,
            matched_user_phone=None,
            shown_user_phones=[],
        )
        logger.debug(f"User {phone_number} declined to add {language_name}")


def get_users_with_language(language_name: str):
    """
    Get users who have a specific language in their Language table.
    Queries the database Language table to find all users who speak the given language.
    
    Returns:
        List of user dictionaries with phone_number, f_name, l_name, bio from database
    """
    session = get_db_session()
    try:
        logger.info(f"🔍 DATABASE QUERY: Querying Language table for language_name='{language_name}'")
        # Query Language table to find users with this language
        languages = session.query(Language).filter_by(language_name=language_name).all()
        logger.info(f"   Found {len(languages)} language records in Language table")
        
        users = []
        for lang in languages:
            user = lang.user
            # Get all user information from database: phone, first name, last name, bio
            user_data = {
                'phone_number': user.phone_number,
                'f_name': user.f_name,
                'l_name': user.l_name,
                'bio': user.bio
            }
            users.append(user_data)
            logger.debug(f"   User found: {user.phone_number} ({user.f_name} {user.l_name})")
        
        logger.info(f"✅ DATABASE QUERY RESULT: Found {len(users)} users in Language table with language '{language_name}'")
        return users
    except Exception as e:
        logger.error(f"❌ DATABASE QUERY ERROR: Error getting users with language {language_name} from Language table: {e}", exc_info=True)
        return []
    finally:
        session.close()


def handle_matching_response(phone_number: str, response_text: str, language_name: str, chat_id: int):
    """
    Handle user's response to matching question
    
    Args:
        phone_number: User's phone number
        response_text: User's response (should be "yes" or "no")
        language_name: Language being discussed
        chat_id: Current chat ID
    """
    response_lower = response_text.lower().strip()
    
    logger.info(f"📥 PROCESSING MATCHING RESPONSE: User {phone_number} responded '{response_text}' to matching question for language {language_name}")
    logger.info(f"   Current conversation state: asking_matching")
    logger.info(f"   Agent (+16463230991) will now query Language database table and send matching user profile")
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah', 'yea', 'yep', 'yup']:
        logger.info(f"✅ USER RESPONDED 'YES': User {phone_number} wants to be matched for language {language_name}")
        logger.info(f"🔍 QUERYING DATABASE: Agent (+16463230991) querying Language table for users who know '{language_name}'...")
        
        # Find matching users (users who have this language in Language table)
        matching_users = get_users_with_language(language_name)
        logger.info(f"📊 DATABASE QUERY RESULT: Found {len(matching_users)} total users with language '{language_name}' in Language table")
        
        # Filter out the requesting user
        original_count = len(matching_users)
        matching_users = [u for u in matching_users if u['phone_number'] != phone_number]
        logger.info(f"📊 FILTERED RESULT: After filtering out requesting user ({phone_number}), {len(matching_users)} matching users available (removed {original_count - len(matching_users)} user)")
        
        if not matching_users:
            # No matching users found
            clear_conversation_state(phone_number)
            message = "Unfortunately, there are no other users who know this language currently."
            logger.info(f"❌ No matching users found for {phone_number} with language {language_name}")
            send_message(phone_number, message, chat_id)
            logger.info(f"No matches found for {phone_number} ({language_name})")
        else:
            # Show first matching user from database
            matched_user = random.choice(matching_users)
            matched_phone = matched_user.get('phone_number', 'N/A')
            matched_name = f"{matched_user.get('f_name', '')} {matched_user.get('l_name', '')}".strip() or 'Not provided'
            
            logger.info(f"🎲 RANDOM SELECTION: Agent (+16463230991) randomly selected user from Language table:")
            logger.info(f"   Selected User Phone: {matched_phone}")
            logger.info(f"   Selected User Name: {matched_name}")
            logger.info(f"   Selected User Bio: {'Yes' if matched_user.get('bio') else 'No'}")
            
            shown_phones = [matched_phone]
            set_conversation_state(phone_number, 'showing_profile', language_name, matched_phone, shown_phones)
            logger.info(f"💾 CONVERSATION STATE UPDATED: User {phone_number} → state='showing_profile', matched_user={matched_phone}")
            
            # Format profile information - MUST include phone, first name, last name from database
            profile_text = f"Here's a user who knows {language_name}:\n\n"
            
            # Always include phone number (REQUIRED)
            profile_text += f"Phone: {matched_phone}\n"
            
            # Build name - MUST include first name and last name separately
            f_name = matched_user.get('f_name', '').strip()
            l_name = matched_user.get('l_name', '').strip()
            name_parts = [p for p in [f_name, l_name] if p]
            
            # Always show first name and last name separately
            if f_name:
                profile_text += f"First Name: {f_name}\n"
            else:
                profile_text += f"First Name: Not provided\n"
            
            if l_name:
                profile_text += f"Last Name: {l_name}\n"
            else:
                profile_text += f"Last Name: Not provided\n"
            
            # Also include full name for clarity
            if f_name or l_name:
                profile_text += f"Full Name: {f_name} {l_name}".strip() + "\n"
            
            # Always include bio (even if empty)
            bio = matched_user.get('bio', '')
            if bio:
                profile_text += f"Bio: {bio}\n"
            else:
                profile_text += f"Bio: Not provided\n"
            
            profile_text += f"\nWould you like a group chat created with this user?"
            
            logger.info(f"📤 SENDING USER PROFILE FROM DATABASE:")
            logger.info(f"   FROM: Agent (+16463230991)")
            logger.info(f"   TO: User {phone_number}")
            logger.info(f"   PROFILE DATA (from Language table):")
            logger.info(f"      - Phone: {matched_phone}")
            logger.info(f"      - Name: {' '.join(name_parts) if name_parts else 'Not provided'}")
            logger.info(f"      - Bio: {bio if bio else 'Not provided'}")
            logger.info(f"   Language: {language_name}")
            
            send_message(phone_number, profile_text, chat_id)
            logger.info(f"✅ PROFILE SENT SUCCESSFULLY: Agent (+16463230991) sent profile of {matched_phone} to user {phone_number}")
    else:
        # User declined matching
        clear_conversation_state(phone_number)
        message = "No problem! Let me know if you change your mind."
        send_message(phone_number, message, chat_id)
        logger.debug(f"User {phone_number} declined match for {language_name}")


def handle_group_chat_response(phone_number: str, response_text: str, language_name: str, matched_user_phone: str, chat_id: int):
    """
    Handle user's response to group chat question.
    When user says "Yes", creates a group chat with:
    - The sender phone number (original user)
    - The matched user phone number
    - The agent number (+16463230991)
    
    Args:
        phone_number: User's phone number (sender/original user)
        response_text: User's response (should be "yes" or "no")
        language_name: Language being discussed
        matched_user_phone: Phone number of matched user
        chat_id: Current chat ID
    """
    response_lower = response_text.lower().strip()
    
    logger.info(f"📥 PROCESSING GROUP CHAT RESPONSE: User {phone_number} responded '{response_text}' to group chat question")
    logger.info(f"   Matched user: {matched_user_phone}")
    logger.info(f"   Language: {language_name}")
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah', 'yea', 'yep', 'yup']:
        logger.info(f"✅ USER RESPONDED 'YES': User {phone_number} wants to create group chat")
        logger.info(f"📱 PREPARING GROUP CHAT: Will include 3 participants:")
        logger.info(f"   1. Sender (original user): {phone_number}")
        logger.info(f"   2. Matched user: {matched_user_phone}")
        logger.info(f"   3. Agent number: +16463230991")
        
        # Import agent number from config
        from config import SERIES_API_CONFIG
        agent_number = SERIES_API_CONFIG['sender_number']  # +16463230991
        
        # Ensure phone numbers are in E.164 format (with +)
        # Include: sender, matched user, and agent number
        phone_numbers = []
        for pn in [phone_number, matched_user_phone, agent_number]:
            if not pn.startswith('+'):
                # Try to format as E.164 (assuming US number if 10 digits)
                if len(pn) == 10:
                    phone_numbers.append(f"+1{pn}")
                else:
                    phone_numbers.append(f"+{pn}")
            else:
                phone_numbers.append(pn)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_phone_numbers = []
        for pn in phone_numbers:
            if pn not in seen:
                seen.add(pn)
                unique_phone_numbers.append(pn)
        
        logger.info(f"📋 GROUP CHAT PARTICIPANTS (normalized): {unique_phone_numbers}")
        
        # Create group chat with all three participants
        group_name = f"{language_name} Language Exchange"
        logger.info(f"🔨 CREATING GROUP CHAT: Using iMessage API to create group chat...")
        logger.info(f"   Group name: {group_name}")
        logger.info(f"   Participants: {unique_phone_numbers}")
        
        new_chat_id = create_group_chat(
            unique_phone_numbers,
            display_name=group_name,
            initial_message=f"Welcome! This group was created for {language_name} language exchange."
        )
        
        if new_chat_id:
            clear_conversation_state(phone_number)
            message = f"Great! I've created a group chat for you with {matched_user_phone}."
            logger.info(f"✅ GROUP CHAT CREATED SUCCESSFULLY:")
            logger.info(f"   Chat ID: {new_chat_id}")
            logger.info(f"   Participants: {unique_phone_numbers}")
            logger.info(f"   Group name: {group_name}")
            send_message(phone_number, message, chat_id)
            logger.info(f"✅ Confirmation message sent to user {phone_number}")
        else:
            message = "Sorry, I couldn't create the group chat. Please try again later."
            logger.error(f"❌ FAILED TO CREATE GROUP CHAT:")
            logger.error(f"   Sender: {phone_number}")
            logger.error(f"   Matched user: {matched_user_phone}")
            logger.error(f"   Agent: {agent_number}")
            send_message(phone_number, message, chat_id)
    else:
        # User declined, ask if they want another match
        # Preserve shown_user_phones in state
        state = get_conversation_state(phone_number)
        shown_phones = state.get('shown_user_phones', []) if state else []
        set_conversation_state(phone_number, 'asking_another_match', language_name, None, shown_phones)
        message = "Would you like me to match you with another user who knows this language?"
        send_message(phone_number, message, chat_id)
        logger.debug(f"User {phone_number} declined group chat, requesting another match")


def handle_another_match_response(phone_number: str, response_text: str, language_name: str, chat_id: int):
    """
    Handle user's response to another match question
    
    Args:
        phone_number: User's phone number
        response_text: User's response (should be "yes" or "no")
        language_name: Language being discussed
        chat_id: Current chat ID
    """
    response_lower = response_text.lower().strip()
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah']:
        # Find another matching user (excluding previously shown ones)
        state = get_conversation_state(phone_number)
        shown_phones = state.get('shown_user_phones', []) if state else []
        
        matching_users = get_users_with_language(language_name)
        # Filter out requesting user and already shown users
        available_users = [
            u for u in matching_users 
            if u['phone_number'] != phone_number and u['phone_number'] not in shown_phones
        ]
        
        if not available_users:
            clear_conversation_state(phone_number)
            message = "Sorry, there are no more users available who know this language."
            send_message(phone_number, message, chat_id)
            logger.info(f"No more matches for {phone_number} ({language_name})")
        else:
            # Show another matching user
            matched_user = random.choice(available_users)
            # Add to shown list
            shown_phones.append(matched_user['phone_number'])
            set_conversation_state(phone_number, 'showing_profile', language_name, matched_user['phone_number'], shown_phones)
            
            # Format profile information - MUST include phone, first name, last name from database
            profile_text = f"Here's another user who knows {language_name}:\n\n"
            
            matched_phone_another = matched_user.get('phone_number', 'N/A')
            # Always include phone number (REQUIRED)
            profile_text += f"Phone: {matched_phone_another}\n"
            
            # Build name - MUST include first name and last name separately
            f_name = matched_user.get('f_name', '').strip()
            l_name = matched_user.get('l_name', '').strip()
            
            # Always show first name and last name separately
            if f_name:
                profile_text += f"First Name: {f_name}\n"
            else:
                profile_text += f"First Name: Not provided\n"
            
            if l_name:
                profile_text += f"Last Name: {l_name}\n"
            else:
                profile_text += f"Last Name: Not provided\n"
            
            # Also include full name for clarity
            if f_name or l_name:
                profile_text += f"Full Name: {f_name} {l_name}".strip() + "\n"
            
            # Always include bio (even if empty)
            bio = matched_user.get('bio', '')
            if bio:
                profile_text += f"Bio: {bio}\n"
            else:
                profile_text += f"Bio: Not provided\n"
            
            profile_text += f"\nWould you like a group chat created with this user?"
            
            send_message(phone_number, profile_text, chat_id)
            logger.info(f"Showing another match to {phone_number}: {matched_user['phone_number']}")
    else:
        # User declined
        clear_conversation_state(phone_number)
        message = "No problem! Feel free to ask for matches anytime."
        send_message(phone_number, message, chat_id)
        logger.debug(f"User {phone_number} declined another match for {language_name}")


def is_yes_response(text: str) -> bool:
    """
    Parse text response to check if it contains "yes".
    Returns True if text contains yes variations, False otherwise.
    """
    if not text:
        return False
    
    text_lower = text.lower().strip()
    yes_variations = ['yes', 'y', 'sure', 'ok', 'okay', 'yeah', 'yea', 'yep', 'yup', 'yess', 'yesss']
    
    # Check if text is exactly a yes variation
    if text_lower in yes_variations:
        return True
    
    # Check if text contains "yes" as a word (not part of another word)
    import re
    if re.search(r'\byes\b', text_lower) or re.search(r'\by\b', text_lower):
        return True
    
    return False


def is_no_response(text: str) -> bool:
    """Check if text response is a 'no'"""
    return text.lower().strip() in ['no', 'n', 'nope', 'nah', 'not', "don't", "dont"]


def process_conversation(phone_number: str, message_text: str, chat_id: int):
    """
    Process incoming text message using switch-case state machine logic.
    Workflow continues until:
    - User says "yes" to add language (adds to table, sends profile, workflow continues)
    - User says "yes" to group chat (creates group chat, workflow exits)
    - User says "no" at any point (workflow exits)
    
    Args:
        phone_number: User's phone number
        message_text: Message text
        chat_id: Current chat ID
    """
    logger.info(f"💬 PROCESSING TEXT MESSAGE: From user {phone_number}, text: '{message_text[:50]}...'")
    
    state = get_conversation_state(phone_number)
    
    if not state:
        # Attempt to rebuild state from persisted agent context
        last_ctx = get_last_agent_context(phone_number)
        if last_ctx and last_ctx.get("state"):
            logger.info(f"🔄 Rehydrating conversation state from last_agent_sent_message for {phone_number}")
            set_conversation_state(
                phone_number,
                last_ctx.get("state"),
                last_ctx.get("language"),
                last_ctx.get("matched_user_phone"),
                last_ctx.get("shown_user_phones"),
            )
            state = get_conversation_state(phone_number)
        # Guard: if still no state after rehydration, bail out safely
        if not state:
            # Fallback: infer from latest voice message and restart the flow
            latest_lang_code = get_latest_voice_message_language(phone_number)
            language_name = get_language_name(latest_lang_code) if latest_lang_code else None

            if language_name:
                is_new = is_new_language_for_user(phone_number, language_name)
                if is_new:
                    logger.info(f"No state; restarting flow as new language for {phone_number} ({language_name})")
                    handle_new_language_detected(phone_number, language_name, chat_id)
                else:
                    logger.info(f"No state; restarting flow as existing language for {phone_number} ({language_name})")
                    handle_existing_language_detected(phone_number, language_name, chat_id)
            else:
                logger.debug(f"No active conversation state and no voice history for user {phone_number}, ignoring message")
            return
    
    state_name = state['state']
    language_name = state.get('language_name')
    matched_user_phone = state.get('matched_user_phone')
    
    logger.info(f"🔄 SWITCH-CASE STATE MACHINE: Current state='{state_name}', language='{language_name}'")
    logger.info(f"   Parsing response: text='{message_text}', from_phone='{phone_number}'")
    
    # Parse the response to check if it's "yes"
    is_yes = is_yes_response(message_text)
    is_no = is_no_response(message_text)
    logger.info(f"   Response parsed: is_yes={is_yes}, is_no={is_no}")
    
    # Switch-case logic flow structure
    # Workflow continues through states until "yes" completes an action:
    #   - "yes" to add language → adds to database, continues to matching
    #   - "yes" to matching → sends profile, continues to group chat question
    #   - "yes" to group chat → creates group chat, exits workflow
    # Workflow exits if "no" at any point
    logger.info(f"   → Processing state: {state_name}")
    
    if state_name == 'asking_add_language':
        # CASE 1: Asking if user wants to add language to table
        logger.info(f"   CASE: asking_add_language - User response: '{message_text}'")
        
        if is_yes_response(message_text):
            # YES: Add language to table, ask if they want to be matched
            logger.info(f"   ✅ YES: Adding language '{language_name}' to table for {phone_number}")
            add_language_for_user(language_name, phone_number)
            logger.info(f"   ✅ Language added. Asking if user wants to be matched...")
            
            # Ask if they want to be matched (workflow continues to asking_matching)
            set_conversation_state(phone_number, 'asking_matching', language_name)
            message = "Do you want to be matched with people who know this language?"
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state='asking_matching',
                language_name=language_name,
                matched_user_phone=None,
                shown_user_phones=[],
            )
            logger.info(f"   → Workflow continues to 'asking_matching' state (waiting for next message)")
            return  # Exit switch-case, workflow continues in asking_matching state
            
        elif is_no_response(message_text):
            # NO: Exit workflow
            logger.info(f"   ❌ NO: User declined to add language. Exiting workflow.")
            clear_conversation_state(phone_number)
            message = "No problem! Let me know if you change your mind."
            send_message(phone_number, message, chat_id)
            return  # Exit workflow
        else:
            # Invalid response, ask again
            logger.info(f"   ⚠️  Invalid response. Asking again...")
            message = "Please respond with 'yes' or 'no'. Do you want me to add this language to our table for future matching?"
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state='asking_add_language',
                language_name=language_name,
                matched_user_phone=None,
                shown_user_phones=[],
            )
            return  # Wait for next response
    
    elif state_name == 'asking_matching':
        # CASE 2: Asking if user wants to be matched
        logger.info(f"   CASE: asking_matching - User response: '{message_text}'")
        
        if is_yes_response(message_text):
            # YES: Send random matching user profile
            logger.info(f"   ✅ YES: User wants to be matched. Sending matching user profile...")
            send_random_matching_user(phone_number, language_name, chat_id)
            logger.info(f"   → Workflow continues to 'showing_profile' state (waiting for next message)")
            return  # Exit switch-case, workflow continues in showing_profile state
            
        elif is_no_response(message_text):
            # NO: Exit workflow
            logger.info(f"   ❌ NO: User declined matching. Exiting workflow.")
            clear_conversation_state(phone_number)
            message = "No problem! Let me know if you change your mind."
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state=None,
                language_name=None,
                matched_user_phone=None,
                shown_user_phones=[],
            )
            return  # Exit workflow
        else:
            # Invalid response, ask again
            logger.info(f"   ⚠️  Invalid response. Asking again...")
            message = "Please respond with 'yes' or 'no'. Do you want to be matched with people who know this language?"
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state='asking_matching',
                language_name=language_name,
                matched_user_phone=None,
                shown_user_phones=[],
            )
            return  # Wait for next response
    
    elif state_name == 'showing_profile':
            # CASE 2: Showing profile, asking if user wants group chat
            logger.info(f"   CASE: showing_profile - User response: '{message_text}'")
            logger.info(f"   Matched user: {matched_user_phone}")
            
            if is_yes_response(message_text):
                # YES: Create group chat, exit workflow
                logger.info(f"   ✅ YES: User wants to create group chat. Creating group chat...")
                
                # Import agent number from config
                from config import SERIES_API_CONFIG
                agent_number = SERIES_API_CONFIG['sender_number']  # +16463230991
                
                # Ensure phone numbers are in E.164 format
                phone_numbers = []
                for pn in [phone_number, matched_user_phone, agent_number]:
                    if not pn.startswith('+'):
                        if len(pn) == 10:
                            phone_numbers.append(f"+1{pn}")
                        else:
                            phone_numbers.append(f"+{pn}")
                    else:
                        phone_numbers.append(pn)
                
                # Remove duplicates
                seen = set()
                unique_phone_numbers = []
                for pn in phone_numbers:
                    if pn not in seen:
                        seen.add(pn)
                        unique_phone_numbers.append(pn)
                
                logger.info(f"   📋 Creating group chat with participants: {unique_phone_numbers}")
                group_name = f"{language_name} Language Exchange"
                new_chat_id = create_group_chat(
                    unique_phone_numbers,
                    display_name=group_name,
                    initial_message=f"Welcome! This group was created for {language_name} language exchange."
                )
                
                if new_chat_id:
                    clear_conversation_state(phone_number)
                    message = f"Great! I've created a group chat for you with {matched_user_phone}."
                    send_message(phone_number, message, chat_id)
                    set_last_agent_message(
                        phone_number,
                        message,
                        state=None,
                        language_name=None,
                        matched_user_phone=None,
                        shown_user_phones=[],
                    )
                    logger.info(f"   ✅ Group chat created successfully. Workflow EXITS.")
                else:
                    message = "Sorry, I couldn't create the group chat. Please try again later."
                    send_message(phone_number, message, chat_id)
                    set_last_agent_message(
                        phone_number,
                        message,
                        state=None,
                        language_name=None,
                        matched_user_phone=None,
                        shown_user_phones=[],
                    )
                    logger.error(f"   ❌ Failed to create group chat. Workflow EXITS.")
                
                return  # Exit workflow
                
            elif is_no_response(message_text):
                # NO: Ask if they want another match, continue workflow
                logger.info(f"   ❌ NO: User declined group chat. Asking for another match...")
                
                state = get_conversation_state(phone_number)
                shown_phones = state.get('shown_user_phones', []) if state else []
                shown_phones.append(matched_user_phone)
                
                set_conversation_state(phone_number, 'asking_another_match', language_name, None, shown_phones)
                message = "Would you like me to match you with another user who knows this language?"
                send_message(phone_number, message, chat_id)
                set_last_agent_message(
                    phone_number,
                    message,
                    state='asking_another_match',
                    language_name=language_name,
                    matched_user_phone=None,
                    shown_user_phones=shown_phones,
                )
                logger.info(f"   → Workflow continues to 'asking_another_match' state (waiting for next message)")
                return  # Continue to next state
            else:
                # Invalid response, ask again
                logger.info(f"   ⚠️  Invalid response. Asking again...")
                message = "Please respond with 'yes' or 'no'. Would you like a group chat created with this user?"
                send_message(phone_number, message, chat_id)
                set_last_agent_message(
                    phone_number,
                    message,
                    state='showing_profile',
                    language_name=language_name,
                    matched_user_phone=matched_user_phone,
                    shown_user_phones=get_conversation_state(phone_number).get('shown_user_phones', []) if get_conversation_state(phone_number) else [],
                )
                return  # Wait for next response
    
    elif state_name == 'asking_another_match':
        # CASE 3: Asking if user wants another match
        logger.info(f"   CASE: asking_another_match - User response: '{message_text}'")
        
        if is_yes_response(message_text):
            # YES: Send another matching user, continue workflow
            logger.info(f"   ✅ YES: User wants another match. Finding another user...")
            
            state = get_conversation_state(phone_number)
            shown_phones = state.get('shown_user_phones', []) if state else []
            
            matching_users = get_users_with_language(language_name)
            available_users = [
                u for u in matching_users 
                if u['phone_number'] != phone_number and u['phone_number'] not in shown_phones
            ]
            
            if not available_users:
                clear_conversation_state(phone_number)
                message = "Sorry, there are no more users available who know this language."
                send_message(phone_number, message, chat_id)
                logger.info(f"   ❌ No more users. Workflow EXITS.")
                return  # Exit workflow
            else:
                # Show another matching user
                matched_user = random.choice(available_users)
                matched_phone = matched_user.get('phone_number', 'N/A')
                shown_phones.append(matched_phone)
                
                set_conversation_state(phone_number, 'showing_profile', language_name, matched_phone, shown_phones)
                
                # Format and send profile
                profile_text = f"Here's another user who knows {language_name}:\n\n"
                profile_text += f"Phone: {matched_phone}\n"
                
                f_name = matched_user.get('f_name', '').strip()
                l_name = matched_user.get('l_name', '').strip()
                
                if f_name:
                    profile_text += f"First Name: {f_name}\n"
                else:
                    profile_text += f"First Name: Not provided\n"
                
                if l_name:
                    profile_text += f"Last Name: {l_name}\n"
                else:
                    profile_text += f"Last Name: Not provided\n"
                
                if f_name or l_name:
                    profile_text += f"Full Name: {f_name} {l_name}".strip() + "\n"
                
                bio = matched_user.get('bio', '')
                if bio:
                    profile_text += f"Bio: {bio}\n"
                else:
                    profile_text += f"Bio: Not provided\n"
                
                profile_text += f"\nWould you like a group chat created with this user?"
                
                send_message(phone_number, profile_text, chat_id)
                set_last_agent_message(
                    phone_number,
                    profile_text,
                    state='showing_profile',
                    language_name=language_name,
                    matched_user_phone=matched_phone,
                    shown_user_phones=shown_phones,
                )
                logger.info(f"   ✅ Another profile sent. Workflow continues to 'showing_profile' state (waiting for next message)")
                return  # Continue to showing_profile state
                
        elif is_no_response(message_text):
            # NO: Exit workflow
            logger.info(f"   ❌ NO: User declined another match. Exiting workflow.")
            clear_conversation_state(phone_number)
            message = "No problem! Feel free to ask for matches anytime."
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state=None,
                language_name=None,
                matched_user_phone=None,
                shown_user_phones=[],
            )
            return  # Exit workflow
        else:
            # Invalid response, ask again
            logger.info(f"   ⚠️  Invalid response. Asking again...")
            message = "Please respond with 'yes' or 'no'. Would you like me to match you with another user who knows this language?"
            send_message(phone_number, message, chat_id)
            set_last_agent_message(
                phone_number,
                message,
                state='asking_another_match',
                language_name=language_name,
                matched_user_phone=None,
                shown_user_phones=get_conversation_state(phone_number).get('shown_user_phones', []) if get_conversation_state(phone_number) else [],
            )
            return  # Wait for next response
    
    else:
        # Unknown state
        logger.warning(f"   ⚠️  Unknown conversation state: {state_name}")
    
    logger.info(f"✅ SWITCH-CASE STATE MACHINE: Completed processing for state '{state_name}'")
