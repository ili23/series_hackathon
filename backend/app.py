"""
Series iMessage Service Backend
A Flask backend that consumes Kafka events from the Series iMessage Service
"""

import os
import json
import logging
from threading import Thread
from flask import Flask, jsonify, request
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce Kafka library verbosity (only show WARNING and above)
logging.getLogger('kafka').setLevel(logging.WARNING)

# Initialize Flask app
app = Flask(__name__)

# Kafka Configuration (from info.md)
KAFKA_CONFIG = {
    'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'pkc-619z3.us-east1.gcp.confluent.cloud:9092'),
    'topic_name': os.getenv('KAFKA_TOPIC', 'team.team.f6e0a95387f7417b90fe88a08a39caec'),
    'consumer_group': os.getenv('KAFKA_CONSUMER_GROUP', 'team-cg-f6e0a95387f7417b90fe88a08a39caec'),
    'api_key': os.getenv('KAFKA_API_KEY', 'b9f131d7-0172-4749-afdd-f01e753b664f'),
    'api_secret': os.getenv('KAFKA_API_SECRET', 'cfltTIivf3OHq6tr9fpASLxV4pp7vzPfvnz3cwT8+NAoOAJUCZwRuxuk1sSZTK+w'),
    'sasl_username': os.getenv('KAFKA_SASL_USERNAME', 'QRHNR6BCKVHD4M3U'),
    'security_protocol': 'SASL_SSL',
    'sasl_mechanism': 'PLAIN',
}

# Global variables for Kafka consumers/producers
kafka_consumer = None
kafka_producer = None
consumer_thread = None


def create_kafka_consumer():
    """Create and configure Kafka consumer"""
    try:
        consumer = KafkaConsumer(
            KAFKA_CONFIG['topic_name'],
            bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'].split(','),
            group_id=KAFKA_CONFIG['consumer_group'],
            security_protocol=KAFKA_CONFIG['security_protocol'],
            sasl_mechanism=KAFKA_CONFIG['sasl_mechanism'],
            sasl_plain_username=KAFKA_CONFIG['sasl_username'],
            sasl_plain_password=KAFKA_CONFIG['api_secret'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True,
        )
        logger.info("Kafka consumer created successfully")
        return consumer
    except Exception as e:
        logger.error(f"Error creating Kafka consumer: {e}")
        return None


def create_kafka_producer():
    """Create and configure Kafka producer"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_CONFIG['bootstrap_servers'].split(','),
            security_protocol=KAFKA_CONFIG['security_protocol'],
            sasl_mechanism=KAFKA_CONFIG['sasl_mechanism'],
            sasl_plain_username=KAFKA_CONFIG['sasl_username'],
            sasl_plain_password=KAFKA_CONFIG['api_secret'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
        logger.info("Kafka producer created successfully")
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None


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


def consume_kafka_messages():
    """Consume messages from Kafka in a separate thread"""
    global kafka_consumer
    
    if not kafka_consumer:
        kafka_consumer = create_kafka_consumer()
    
    if not kafka_consumer:
        logger.error("Failed to create Kafka consumer")
        return
    
    logger.info("Starting Kafka consumer...")
    
    try:
        for message in kafka_consumer:
            try:
                event = message.value
                process_kafka_event(event)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except KafkaError as e:
        logger.error(f"Kafka error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
    finally:
        if kafka_consumer:
            kafka_consumer.close()


# Flask Routes
@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Series iMessage Backend',
        'kafka_connected': kafka_consumer is not None
    })


@app.route('/api/events', methods=['GET'])
def get_recent_events():
    """Get recent events (placeholder - implement your own storage)"""
    return jsonify({
        'message': 'Event storage not implemented yet',
        'hint': 'Store events in a database or cache as they arrive'
    })


@app.route('/api/send-message', methods=['POST'])
def send_message():
    """Send a message via Kafka (if needed)"""
    # Note: This is a placeholder. Actual message sending should use the Series API
    # This endpoint is just for demonstration
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    logger.info(f"Received send message request: {data}")
    
    # TODO: Use Series API to send messages instead of Kafka
    # POST /api/chats with Authorization: Bearer <API_KEY>
    
    return jsonify({
        'message': 'Message send endpoint - use Series API directly',
        'received_data': data
    })


def initialize_kafka():
    """Initialize Kafka consumer and producer on app startup"""
    global kafka_consumer, kafka_producer, consumer_thread
    
    logger.info("Initializing Kafka connections...")
    
    # Create producer (optional, for sending messages via Kafka if needed)
    kafka_producer = create_kafka_producer()
    
    # Start consumer in background thread
    consumer_thread = Thread(target=consume_kafka_messages, daemon=True)
    consumer_thread.start()
    
    logger.info("Kafka initialization complete")


# Cleanup on shutdown
@app.teardown_appcontext
def close_kafka_connections(exception):
    """Close Kafka connections on app shutdown"""
    global kafka_consumer, kafka_producer
    
    if kafka_consumer:
        kafka_consumer.close()
        logger.info("Kafka consumer closed")
    
    if kafka_producer:
        kafka_producer.close()
        logger.info("Kafka producer closed")


# Initialize Kafka on module import
initialize_kafka()

if __name__ == '__main__':
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
