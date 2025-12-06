"""
Event handlers for processing Kafka events
"""
import json
import logging

logger = logging.getLogger(__name__)


def handle_message_received(event_data):
    """Handle message.received events"""
    logger.info(f"Message received event: {json.dumps(event_data, indent=2)}")
    
    # Extract relevant information
    message_id = event_data.get('id')
    chat_id = event_data.get('chat_id')
    from_phone = event_data.get('from_phone')
    text = event_data.get('text')
    is_read = event_data.get('is_read')
    
    logger.info(f"New message from {from_phone} in chat {chat_id}: {text}")
    
    # TODO: Add your business logic here
    # - Store message in database
    # - Trigger notifications
    # - Process message content
    # - etc.


def handle_typing_indicator_received(event_data):
    """Handle typing_indicator.received events"""
    logger.info(f"Typing indicator received: {json.dumps(event_data, indent=2)}")
    
    chat_id = event_data.get('chat_id')
    display = event_data.get('display')
    
    logger.info(f"User started typing in chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Update UI with typing indicator
    # - Store typing state
    # etc.


def handle_typing_indicator_removed(event_data):
    """Handle typing_indicator.removed events"""
    logger.info(f"Typing indicator removed: {json.dumps(event_data, indent=2)}")
    
    chat_id = event_data.get('chat_id')
    
    logger.info(f"User stopped typing in chat {chat_id}")
    
    # TODO: Add your business logic here
    # - Remove typing indicator from UI
    # - Update typing state
    # etc.


def process_kafka_event(event):
    """Process incoming Kafka events"""
    try:
        event_type = event.get('event_type')
        data = event.get('data', {})
        
        logger.info(f"Processing event: {event_type}")
        
        if event_type == 'message.received':
            handle_message_received(data)
        elif event_type == 'typing_indicator.received':
            handle_typing_indicator_received(data)
        elif event_type == 'typing_indicator.removed':
            handle_typing_indicator_removed(data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            
    except Exception as e:
        logger.error(f"Error processing event: {e}", exc_info=True)

