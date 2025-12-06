"""
Series API client for sending messages and creating chats
"""
import logging
import requests
from config import SERIES_API_CONFIG

logger = logging.getLogger(__name__)

SERIES_API_BASE_URL = SERIES_API_CONFIG['base_url']
API_KEY = SERIES_API_CONFIG['api_key']
SENDER_NUMBER = SERIES_API_CONFIG['sender_number']


def send_message(to_phone_number: str, message_text: str, chat_id: int = None):
    """
    Send a message using Series API
    
    Args:
        to_phone_number: Recipient phone number (E.164 format) or can be None if chat_id is provided
        message_text: Message text to send
        chat_id: Optional existing chat ID to send to
    
    Returns:
        Response dict if successful, None otherwise
    """
    try:
        if chat_id:
            # Send to existing chat
            url = f"{SERIES_API_BASE_URL}/api/chats/{chat_id}/chat_messages"
            payload = {
                'message': {
                    'text': message_text
                }
            }
        else:
            # Create new chat and send message
            if not to_phone_number:
                logger.error("Cannot send message: no phone number or chat_id provided")
                return None
            url = f"{SERIES_API_BASE_URL}/api/chats"
            payload = {
                'send_from': SENDER_NUMBER,
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
            logger.info(f"Message sent successfully")
            return result
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return None


def create_group_chat(phone_numbers: list, display_name: str = None, initial_message: str = None):
    """
    Create a group chat using Series API
    
    Args:
        phone_numbers: List of phone numbers (E.164 format)
        display_name: Optional display name for the group
        initial_message: Optional initial message to send
    
    Returns:
        Chat ID if successful, None otherwise
    """
    try:
        url = f"{SERIES_API_BASE_URL}/api/chats"
        
        payload = {
            'send_from': SENDER_NUMBER,
            'chat': {
                'phone_numbers': phone_numbers
            }
        }
        
        if display_name:
            payload['chat']['display_name'] = display_name
        
        if initial_message:
            payload['message'] = {
                'text': initial_message
            }
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            chat_id = result.get('id')
            logger.info(f"Group chat created successfully with ID: {chat_id}")
            return chat_id
        else:
            logger.error(f"Error creating group chat: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating group chat: {e}", exc_info=True)
        return None
