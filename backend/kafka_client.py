"""
Kafka client management for consumer and producer
"""
import json
import logging
from threading import Thread
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from config import KAFKA_CONFIG

logger = logging.getLogger(__name__)

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


def consume_kafka_messages(event_processor):
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
                event_processor(event)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except KafkaError as e:
        logger.error(f"Kafka error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
    finally:
        if kafka_consumer:
            kafka_consumer.close()


def initialize_kafka(event_processor):
    """Initialize Kafka consumer and producer on app startup"""
    global kafka_consumer, kafka_producer, consumer_thread
    
    logger.info("Initializing Kafka connections...")
    
    # Create producer (optional, for sending messages via Kafka if needed)
    kafka_producer = create_kafka_producer()
    
    # Start consumer in background thread
    consumer_thread = Thread(target=consume_kafka_messages, args=(event_processor,), daemon=True)
    consumer_thread.start()
    
    logger.info("Kafka initialization complete")


def close_kafka_connections():
    """Close Kafka connections on app shutdown"""
    global kafka_consumer, kafka_producer
    
    if kafka_consumer:
        kafka_consumer.close()
        logger.info("Kafka consumer closed")
    
    if kafka_producer:
        kafka_producer.close()
        logger.info("Kafka producer closed")


def get_kafka_consumer():
    """Get the current Kafka consumer instance"""
    return kafka_consumer


def get_kafka_producer():
    """Get the current Kafka producer instance"""
    return kafka_producer

