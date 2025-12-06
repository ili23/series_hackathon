"""
Series API client for sending messages and creating chats
"""
import logging
import requests
from backend.config import SERIES_API_CONFIG

logger = logging.getLogger(__name__)

SERIES_API_BASE_URL = SERIES_API_CONFIG['base_url']
API_KEY = SERIES_API_CONFIG['api_key']
SENDER_NUMBER = SERIES_API_CONFIG['sender_number']


def send_message(to_phone_number: str, message_text: str, chat_id: int = None):
    """
    Send a message using Series API
    ALWAYS uses agent number (+16463230991) to send messages and make API calls.
    
    Args:
        to_phone_number: Recipient phone number (E.164 format) or can be None if chat_id is provided
        message_text: Message text to send
        chat_id: Optional existing chat ID to send to
    
    Returns:
        Response dict if successful, None otherwise
    """
    try:
        if chat_id:
            # Send to existing chat - ALWAYS use agent number
            url = f"{SERIES_API_BASE_URL}/api/chats/{chat_id}/chat_messages"
            payload = {
                'send_from': SENDER_NUMBER,  # ALWAYS agent number (+16463230991)
                'message': {
                    'text': message_text
                }
            }
        else:
            # Create new chat and send message - ALWAYS use agent number
            if not to_phone_number:
                logger.error("Cannot send message: no phone number or chat_id provided")
                return None
            url = f"{SERIES_API_BASE_URL}/api/chats"
            payload = {
                'send_from': SENDER_NUMBER,  # ALWAYS agent number (+16463230991) - never user's number
                'chat': {
                    'phone_numbers': [to_phone_number]
                },
                'message': {
                    'text': message_text
                }
            }
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.debug(f"Message sent to {to_phone_number}")
            
            # Store last agent message per user to handle out-of-order Kafka events
            if to_phone_number:
                try:
                    from backend.db.accessors import set_last_agent_message
                    set_last_agent_message(to_phone_number, message_text)
                except Exception as e:
                    logger.error(f"Error recording last agent message for {to_phone_number}: {e}", exc_info=True)
            return result
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return None


def find_existing_chat(phone_numbers: list):
    """
    Check if a chat already exists between the given phone numbers.
    
    Args:
        phone_numbers: List of phone numbers (E.164 format) - participants to check
    
    Returns:
        Chat ID if found, None otherwise
    """
    try:
        url = f"{SERIES_API_BASE_URL}/api/chats/find"
        
        # Remove agent number from participants if present
        participants_only = [pn for pn in phone_numbers if pn != SENDER_NUMBER]
        
        if len(participants_only) < 2:
            # Need at least 2 participants to find a chat
            return None
        
        params = {
            'phone_number': participants_only[0],
            'phone_numbers[]': participants_only[1:]
        }
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            chat_id = result.get('id')
            if chat_id:
                logger.info(f"✅ Found existing chat: {chat_id} between {participants_only}")
                return chat_id
        
        return None
    except Exception as e:
        logger.debug(f"Error finding existing chat: {e}")
        return None


def create_group_chat(phone_numbers: list, display_name: str = None, initial_message: str = None):
    """
    Create a group chat using Series API via iMessage API
    ALWAYS uses agent number (+16463230991) to create the group chat and make API calls.
    The agent number is used ONLY for send_from, NOT as a participant.
    
    Args:
        phone_numbers: List of phone numbers (E.164 format) - participants to include (EXCLUDES agent number)
                      Only user phone numbers should be in this list
        display_name: Optional display name for the group
        initial_message: Optional initial message to send (defaults to empty string if not provided)
    
    Returns:
        Dict with 'chat_id' and 'is_existing' flag if successful, None otherwise
        Format: {'chat_id': int, 'is_existing': bool} or None
    """
    try:
        # API endpoint: https://series-hackathon-service-202642739529.us-east1.run.app/api/chats
        url = f"{SERIES_API_BASE_URL}/api/chats"
        
        # CRITICAL: Remove agent number from participants list if present
        # Agent number is used ONLY for send_from, not as a participant
        participants_only = [pn for pn in phone_numbers if pn != SENDER_NUMBER]
        if len(participants_only) < len(phone_numbers):
            removed_count = len(phone_numbers) - len(participants_only)
            logger.info(f"   ℹ️  Removed {removed_count} agent number(s) from participants list (agent creates chat but is not a participant)")
        
        logger.info(f"🔨 CREATING GROUP CHAT via iMessage API:")
        logger.info(f"   API Endpoint: {url}")
        logger.info(f"   🔑 CREATED BY: Agent number {SENDER_NUMBER} (agent creates chat via send_from)")
        logger.info(f"   Total participants (users only): {len(participants_only)}")
        logger.info(f"   Display name: {display_name}")
        logger.info(f"   Initial message: {initial_message[:50] if initial_message else 'None'}...")
        
        # Log each phone number individually with index
        logger.info(f"   📞 PARTICIPANTS BREAKDOWN (users only, agent excluded):")
        for idx, pn in enumerate(participants_only, 1):
            logger.info(f"      {idx}. {pn} (USER PARTICIPANT)")
        logger.info(f"   🔑 Agent {SENDER_NUMBER} will create the group chat (send_from, not a participant)")
        
        # Validate phone numbers format
        logger.info(f"   ✅ PHONE NUMBER VALIDATION:")
        invalid_numbers = []
        for pn in participants_only:
            if not pn.startswith('+'):
                logger.warning(f"      ⚠️  {pn} - Missing '+' prefix (should be E.164 format)")
                invalid_numbers.append(pn)
            elif len(pn) < 10:
                logger.warning(f"      ⚠️  {pn} - Too short (should be E.164 format)")
                invalid_numbers.append(pn)
            else:
                logger.info(f"      ✓ {pn} - Valid E.164 format")
        
        if invalid_numbers:
            logger.error(f"   ❌ INVALID PHONE NUMBERS DETECTED: {invalid_numbers}")
        
        # ALWAYS use agent number to create the group chat (send_from)
        # Agent number is NOT included in participants list
        payload = {
            'send_from': SENDER_NUMBER,  # ALWAYS agent number (+16463230991) - creates the group chat
            'chat': {
                'phone_numbers': participants_only  # Only user participants, agent excluded
            },
            'message': {
                'text': initial_message if initial_message else ''
            }
        }
        
        if display_name:
            payload['chat']['display_name'] = display_name
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"📤 API REQUEST: POST {url}")
        logger.debug(f"   Payload: {payload}")
        
        # First, check if a chat already exists between these users
        existing_chat_id = find_existing_chat(participants_only)
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            chat_id = result.get('id')
            
            # If we got a successful response (200/201), it's a success regardless of chat_id value
            # The API might return the same chat_id if chat already exists, which is fine
            # Check if this is the same as an existing chat or if we found one earlier
            is_existing = False
            if existing_chat_id and chat_id:
                if chat_id == existing_chat_id:
                    is_existing = True
                    logger.info(f"✅ GROUP CHAT ALREADY EXISTS: Chat {chat_id} already exists between these users")
                else:
                    logger.info(f"✅ GROUP CHAT CREATED: New chat {chat_id} created (different from existing {existing_chat_id})")
            elif chat_id:
                # Check response text for indicators of existing chat
                response_text = response.text.lower()
                if 'already' in response_text or 'exists' in response_text or 'duplicate' in response_text:
                    is_existing = True
                    logger.info(f"✅ GROUP CHAT ALREADY EXISTS: Chat {chat_id} (detected from response)")
                else:
                    logger.info(f"✅ GROUP CHAT CREATED: New chat {chat_id} created successfully")
            else:
                # Success response but no chat_id in response - still treat as success
                # The API might have created the chat but returned it differently
                logger.info(f"✅ GROUP CHAT SUCCESS: Received 200/201 response (chat may have been created or already exists)")
            
            logger.info(f"   Chat ID: {chat_id}")
            logger.info(f"   Created by: {SENDER_NUMBER} (agent)")
            logger.info(f"   Participants (users): {participants_only}")
            logger.info(f"   Agent number NOT in participants (correct - agent only creates chat)")
            logger.info(f"   Is existing chat: {is_existing}")
            logger.info(f"   Status: SUCCESS (200/201 response means group chat was created or already exists)")
            
            # Return chat_id and flag - 200/201 response is always success
            # Even if chat_id is None, we got a success response, so treat as success
            return {'chat_id': chat_id, 'is_existing': is_existing, 'success': True}
        elif response.status_code == 403:
            # 403 Forbidden: Phone number not allowed for this team
            error_msg = response.text
            logger.error(f"")
            logger.error(f"❌❌❌ 403 FORBIDDEN ERROR: Phone number not allowed for this team ❌❌❌")
            logger.error(f"   Status Code: {response.status_code}")
            logger.error(f"   API Response: {error_msg}")
            logger.error(f"")
            logger.error(f"   🔍 DIAGNOSIS: One or more phone numbers are NOT whitelisted in Series API")
            logger.error(f"")
            logger.error(f"   📋 PHONE NUMBERS IN GROUP CHAT:")
            logger.error(f"      Created by (send_from): {SENDER_NUMBER} (AGENT)")
            logger.error(f"      Participants (users only):")
            for idx, pn in enumerate(participants_only, 1):
                logger.error(f"         {idx}. {pn}")
            logger.error(f"")
            logger.error(f"   🔧 TROUBLESHOOTING STEPS:")
            logger.error(f"      1. Check Series API dashboard/team settings")
            logger.error(f"      2. Verify ALL participant phone numbers are whitelisted/authorized:")
            for idx, pn in enumerate(participants_only, 1):
                logger.error(f"         - {pn}")
            logger.error(f"      3. Ensure agent number ({SENDER_NUMBER}) has permission to create group chats")
            logger.error(f"      4. Check if phone numbers need to be added to team members list")
            logger.error(f"")
            logger.error(f"   💡 NOTE: Agent number is NOT in participants list (correct behavior)")
            logger.error(f"      Agent creates the chat but is not a participant")
            logger.error(f"")
            return None
        else:
            logger.error(f"❌ FAILED TO CREATE GROUP CHAT via iMessage API:")
            logger.error(f"   Status: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            logger.error(f"   Created by: {SENDER_NUMBER} (agent)")
            logger.error(f"   Participants attempted: {participants_only}")
            return None
            
    except Exception as e:
        logger.error(f"❌ ERROR CREATING GROUP CHAT: {e}", exc_info=True)
        return None


def start_typing(chat_id: int):
    """
    Start typing indicator in a chat using Series API
    ALWAYS uses agent number (+16463230991) to show typing indicator.
    
    Args:
        chat_id: Chat ID to show typing indicator in
    
    Returns:
        True if successful, False otherwise
    """
    try:
        url = f"{SERIES_API_BASE_URL}/api/chats/{chat_id}/start_typing"
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"⌨️  Starting typing indicator in chat {chat_id} (agent: {SENDER_NUMBER})")
        
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.debug(f"✅ Typing indicator started in chat {chat_id}")
            return True
        else:
            logger.warning(f"⚠️  Failed to start typing indicator: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR STARTING TYPING INDICATOR: {e}", exc_info=True)
        return False


def stop_typing(chat_id: int):
    """
    Stop typing indicator in a chat using Series API
    ALWAYS uses agent number (+16463230991) to hide typing indicator.
    
    Args:
        chat_id: Chat ID to stop typing indicator in
    
    Returns:
        True if successful, False otherwise
    """
    try:
        url = f"{SERIES_API_BASE_URL}/api/chats/{chat_id}/stop_typing"
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"⌨️  Stopping typing indicator in chat {chat_id} (agent: {SENDER_NUMBER})")
        
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            logger.debug(f"✅ Typing indicator stopped in chat {chat_id}")
            return True
        else:
            logger.warning(f"⚠️  Failed to stop typing indicator: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR STOPPING TYPING INDICATOR: {e}", exc_info=True)
        return False
