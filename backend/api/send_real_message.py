"""
Script to send real iMessages using the Series API
"""
import os
import sys
import json
import logging
import requests
from backend.config import SERIES_API_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Series API Configuration
SERIES_API_BASE_URL = SERIES_API_CONFIG['base_url']
API_KEY = SERIES_API_CONFIG['api_key']
SENDER_NUMBER = SERIES_API_CONFIG['sender_number']

# Team member phone numbers (from info.md)
TEAM_PHONES = {
    'iram': '+16469324962',
    'crystal': '+19172156679',
}


def send_imessage(send_from, to_phone_numbers, message_text, display_name=None):
    """
    Send a real iMessage using the Series API
    
    Args:
        send_from: Phone number to send from (E.164 format, e.g., +16463230991)
        to_phone_numbers: List of recipient phone numbers (E.164 format)
        message_text: Message text to send
        display_name: Optional display name for group chats
    """
    url = f"{SERIES_API_BASE_URL}/api/chats"
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'send_from': send_from,
        'chat': {
            'phone_numbers': to_phone_numbers if isinstance(to_phone_numbers, list) else [to_phone_numbers]
        },
        'message': {
            'text': message_text
        }
    }
    
    # Add display name for group chats
    if display_name:
        payload['chat']['display_name'] = display_name
    
    try:
        logger.info(f"Sending iMessage from {send_from} to {', '.join(to_phone_numbers if isinstance(to_phone_numbers, list) else [to_phone_numbers])}")
        logger.debug(f"Message: {message_text}")
        logger.debug(f"API URL: {url}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code in [200, 201]:
            result = response.json()
            chat_id = result.get('id', 'N/A')
            message_id = result.get('message', {}).get('id', 'N/A') if 'message' in result else 'N/A'
            logger.info(f"✓ Message sent successfully! Chat ID: {chat_id}, Message ID: {message_id}")
            print(f"\n✓ Message sent successfully!")
            print(f"  Chat ID: {chat_id}")
            if message_id != 'N/A':
                print(f"  Message ID: {message_id}")
            return result
        else:
            error_msg = f"Error sending message - Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            print(f"\n✗ Error sending message:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Request error: {e}", exc_info=True)
        print(f"\n✗ Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        print(f"\n✗ Unexpected error: {e}")
        return None


def main():
    """Main function to send messages"""
    if len(sys.argv) < 3:
        print("Usage: python send_real_message.py <recipient_phone> <message>")
        print("\nExamples:")
        print(f"  python send_real_message.py {TEAM_PHONES['iram']} 'Hello from the backend!'")
        print(f"  python send_real_message.py {TEAM_PHONES['crystal']} 'Testing real iMessage'")
        print("\nOr use team member shortcuts:")
        print("  python send_real_message.py iram 'Hello Iram!'")
        print("  python send_real_message.py crystal 'Hello Crystal!'")
        print("\nFor group messages:")
        print(f"  python send_real_message.py '{TEAM_PHONES['iram']},{TEAM_PHONES['crystal']}' 'Group message!'")
        sys.exit(1)
    
    recipient = sys.argv[1]
    message = ' '.join(sys.argv[2:])
    
    # Check if using team member shortcut
    if recipient.lower() in TEAM_PHONES:
        recipient = TEAM_PHONES[recipient.lower()]
    
    # Handle group messages (comma-separated)
    if ',' in recipient:
        phone_numbers = [p.strip() for p in recipient.split(',')]
    else:
        phone_numbers = [recipient]
    
    # Validate phone numbers (basic E.164 format check)
    for phone in phone_numbers:
        if not phone.startswith('+') or len(phone) < 10:
            print(f"Error: Invalid phone number format: {phone}")
            print("Phone numbers must be in E.164 format (e.g., +16469324962)")
            sys.exit(1)
    
    result = send_imessage(SENDER_NUMBER, phone_numbers, message)
    
    if result:
        print("\n✓ Success! Check your phone for the message.")
        sys.exit(0)
    else:
        print("\n✗ Failed to send message.")
        sys.exit(1)


if __name__ == '__main__':
    main()

