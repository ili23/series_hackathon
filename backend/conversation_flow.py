"""
Conversation flow manager for language matching workflow
"""
import logging
import random
from datetime import datetime
from db.accessors import (
    add_language_for_user, add_to_user_table, get_user_given_language
)
from db.database import get_db_session
from db.models import Language, User
from series_api_client import send_message, create_group_chat

logger = logging.getLogger(__name__)


def is_new_language_for_user(phone_number: str, language_name: str):
    """Check if a language is new for a user"""
    session = get_db_session()
    try:
        existing = session.query(Language).filter_by(
            phone_number=phone_number,
            language_name=language_name
        ).first()
        return existing is None
    except Exception as e:
        logger.error(f"Error checking language: {e}")
        return True
    finally:
        session.close()


def get_conversation_state(phone_number: str):
    """Get current conversation state for a user (stored in a simple way)"""
    # For simplicity, we'll use a dictionary to track states
    # In production, you might want to use a database table
    if not hasattr(get_conversation_state, 'states'):
        get_conversation_state.states = {}
    return get_conversation_state.states.get(phone_number)


def set_conversation_state(phone_number: str, state: str, language_name: str = None, matched_user_phone: str = None):
    """Set conversation state for a user"""
    if not hasattr(set_conversation_state, 'states'):
        set_conversation_state.states = {}
    set_conversation_state.states[phone_number] = {
        'state': state,
        'language_name': language_name,
        'matched_user_phone': matched_user_phone
    }


def clear_conversation_state(phone_number: str):
    """Clear conversation state for a user"""
    if hasattr(clear_conversation_state, 'states'):
        if phone_number in clear_conversation_state.states:
            del clear_conversation_state.states[phone_number]


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
        logger.info(f"Language {language_name} already exists for {phone_number}")
        return
    
    # Set conversation state
    set_conversation_state(phone_number, 'asking_add_language', language_name)
    
    # Send message asking if they want to add the language
    message = "I noticed this is a new language for you. Do you want me to add this language proficiency to our table for future matching?"
    send_message(phone_number, message, chat_id)
    
    logger.info(f"Asked user {phone_number} about adding language {language_name}")


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
        
        # Ask about matching
        set_conversation_state(phone_number, 'asking_matching', language_name)
        message = "Do you want to be matched with people who know this language?"
        send_message(phone_number, message, chat_id)
        
        logger.info(f"User {phone_number} added language {language_name}, asking about matching")
    else:
        # User declined
        clear_conversation_state(phone_number)
        message = "No problem! Let me know if you change your mind."
        send_message(phone_number, message, chat_id)
        logger.info(f"User {phone_number} declined to add language {language_name}")


def get_users_with_language(language_name: str):
    """Get users who have a specific language in their Language table"""
    session = get_db_session()
    try:
        languages = session.query(Language).filter_by(language_name=language_name).all()
        users = []
        for lang in languages:
            user = lang.user
            users.append({
                'phone_number': user.phone_number,
                'f_name': user.f_name,
                'l_name': user.l_name,
                'bio': user.bio
            })
        return users
    except Exception as e:
        logger.error(f"Error getting users with language {language_name}: {e}")
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
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah']:
        # Find matching users (users who have this language in Language table)
        matching_users = get_users_with_language(language_name)
        
        # Filter out the requesting user
        matching_users = [u for u in matching_users if u['phone_number'] != phone_number]
        
        if not matching_users:
            # No matching users found
            clear_conversation_state(phone_number)
            message = "Unfortunately, there are no other users who know this language currently."
            send_message(phone_number, message, chat_id)
            logger.info(f"No matching users found for {phone_number} with language {language_name}")
        else:
            # Show first matching user
            matched_user = random.choice(matching_users)
            set_conversation_state(phone_number, 'showing_profile', language_name, matched_user['phone_number'])
            
            # Send profile information
            profile_text = f"Here's a user who knows {language_name}:\n\n"
            profile_text += f"Name: {matched_user.get('f_name', '')} {matched_user.get('l_name', '')}\n"
            if matched_user.get('bio'):
                profile_text += f"Bio: {matched_user['bio']}\n"
            profile_text += f"\nWould you like a group chat created with this user?"
            
            send_message(phone_number, profile_text, chat_id)
            logger.info(f"Showing profile of {matched_user['phone_number']} to {phone_number}")
    else:
        # User declined matching
        clear_conversation_state(phone_number)
        message = "No problem! Let me know if you change your mind."
        send_message(phone_number, message, chat_id)
        logger.info(f"User {phone_number} declined matching for language {language_name}")


def handle_group_chat_response(phone_number: str, response_text: str, language_name: str, matched_user_phone: str, chat_id: int):
    """
    Handle user's response to group chat question
    
    Args:
        phone_number: User's phone number
        response_text: User's response (should be "yes" or "no")
        language_name: Language being discussed
        matched_user_phone: Phone number of matched user
        chat_id: Current chat ID
    """
    response_lower = response_text.lower().strip()
    
    if response_lower in ['yes', 'y', 'sure', 'ok', 'okay', 'yeah']:
        # Create group chat
        group_name = f"{language_name} Language Exchange"
        new_chat_id = create_group_chat(
            [phone_number, matched_user_phone],
            display_name=group_name,
            initial_message=f"Welcome! This group was created for {language_name} language exchange."
        )
        
        if new_chat_id:
            clear_conversation_state(phone_number)
            message = f"Great! I've created a group chat for you."
            send_message(phone_number, message, chat_id)
            logger.info(f"Created group chat {new_chat_id} for {phone_number} and {matched_user_phone}")
        else:
            message = "Sorry, I couldn't create the group chat. Please try again later."
            send_message(phone_number, message, chat_id)
            logger.error(f"Failed to create group chat for {phone_number} and {matched_user_phone}")
    else:
        # User declined, ask if they want another match
        set_conversation_state(phone_number, 'asking_another_match', language_name)
        message = "Would you like me to match you with another user who knows this language?"
        send_message(phone_number, message, chat_id)
        logger.info(f"User {phone_number} declined group chat, asking for another match")


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
        shown_phones = [state['matched_user_phone']] if state and state.get('matched_user_phone') else []
        
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
            logger.info(f"No more matching users for {phone_number} with language {language_name}")
        else:
            # Show another matching user
            matched_user = random.choice(available_users)
            set_conversation_state(phone_number, 'showing_profile', language_name, matched_user['phone_number'])
            
            # Send profile information
            profile_text = f"Here's another user who knows {language_name}:\n\n"
            profile_text += f"Name: {matched_user.get('f_name', '')} {matched_user.get('l_name', '')}\n"
            if matched_user.get('bio'):
                profile_text += f"Bio: {matched_user['bio']}\n"
            profile_text += f"\nWould you like a group chat created with this user?"
            
            send_message(phone_number, profile_text, chat_id)
            logger.info(f"Showing another profile of {matched_user['phone_number']} to {phone_number}")
    else:
        # User declined
        clear_conversation_state(phone_number)
        message = "No problem! Feel free to ask for matches anytime."
        send_message(phone_number, message, chat_id)
        logger.info(f"User {phone_number} declined another match for language {language_name}")


def process_conversation(phone_number: str, message_text: str, chat_id: int):
    """
    Process incoming text message and handle conversation flow
    
    Args:
        phone_number: User's phone number
        message_text: Message text
        chat_id: Current chat ID
    """
    state = get_conversation_state(phone_number)
    
    if not state:
        # No active conversation state
        return
    
    state_name = state['state']
    language_name = state.get('language_name')
    
    if state_name == 'asking_add_language':
        handle_add_language_response(phone_number, message_text, language_name, chat_id)
    elif state_name == 'asking_matching':
        handle_matching_response(phone_number, message_text, language_name, chat_id)
    elif state_name == 'showing_profile':
        handle_group_chat_response(phone_number, message_text, language_name, state.get('matched_user_phone'), chat_id)
    elif state_name == 'asking_another_match':
        handle_another_match_response(phone_number, message_text, language_name, chat_id)
    else:
        logger.warning(f"Unknown conversation state: {state_name}")
