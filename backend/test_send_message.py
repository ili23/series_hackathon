"""
Test script to send test messages to Kafka
"""
import json
import sys
from kafka_producer import create_kafka_producer, get_kafka_producer
from config import KAFKA_CONFIG


def send_test_message(event_type='message.received', data=None):
    """Send a test message to Kafka"""
    
    # Use existing producer if available, otherwise create a new one
    producer = get_kafka_producer() or create_kafka_producer()
    
    if not producer:
        print("Error: Failed to create Kafka producer")
        return False
    
    # Default test data based on event type
    if data is None:
        if event_type == 'message.received':
            data = {
                'id': 'test-msg-123',
                'chat_id': 'test-chat-456',
                'from_phone': '+1234567890',
                'text': 'Hello, this is a test message!',
                'is_read': False
            }
        elif event_type == 'typing_indicator.received':
            data = {
                'chat_id': 'test-chat-456',
                'display': 'Test User'
            }
        elif event_type == 'typing_indicator.removed':
            data = {
                'chat_id': 'test-chat-456'
            }
        else:
            data = {'test': 'data'}
    
    # Create event in the expected format
    event = {
        'event_type': event_type,
        'data': data
    }
    
    try:
        print(f"Sending test event: {event_type}")
        print(f"Event data: {json.dumps(event, indent=2)}")
        
        future = producer.send(KAFKA_CONFIG['topic_name'], value=event)
        record_metadata = future.get(timeout=10)
        
        print(f"\n✓ Message sent successfully!")
        print(f"  Topic: {record_metadata.topic}")
        print(f"  Partition: {record_metadata.partition}")
        print(f"  Offset: {record_metadata.offset}")
        return True
        
    except Exception as e:
        print(f"✗ Error sending message: {e}")
        return False


if __name__ == '__main__':
    # Default: send a message.received event
    event_type = sys.argv[1] if len(sys.argv) > 1 else 'message.received'
    
    # Supported event types
    valid_types = ['message.received', 'typing_indicator.received', 'typing_indicator.removed']
    
    if event_type not in valid_types:
        print(f"Invalid event type: {event_type}")
        print(f"Valid types: {', '.join(valid_types)}")
        sys.exit(1)
    
    success = send_test_message(event_type)
    sys.exit(0 if success else 1)

