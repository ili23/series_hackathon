"""
Kafka producer for sending messages
"""
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from config import KAFKA_CONFIG

logger = logging.getLogger(__name__)


class KafkaProducerManager:
    """Manages Kafka producer instance and lifecycle"""
    
    def __init__(self):
        self.producer = None
    
    def create_producer(self):
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
    
    def get_producer(self):
        """Get the producer instance (creates one if it doesn't exist)"""
        if not self.producer:
            self.producer = self.create_producer()
        return self.producer
    
    def initialize(self):
        """Initialize Kafka producer on startup"""
        logger.info("Initializing Kafka producer...")
        self.producer = self.create_producer()
        
        if self.producer:
            logger.info("Kafka producer initialization complete")
        else:
            logger.error("Kafka producer initialization failed")
        
        return self.producer
    
    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            try:
                self.producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self.producer = None
    
    def send_message(self, topic, value, key=None):
        """
        Send a message to Kafka topic
        
        Args:
            topic: Kafka topic name
            value: Message value (will be JSON serialized)
            key: Optional message key
        
        Returns:
            Future object or None if producer is not available
        """
        producer = self.get_producer()
        
        if not producer:
            logger.error("Cannot send message: Kafka producer not available")
            return None
        
        try:
            future = producer.send(topic, value=value, key=key)
            logger.debug(f"Message sent to topic {topic}")
            return future
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
            return None


# Create a singleton instance
_producer_manager = KafkaProducerManager()


# Convenience functions that use the singleton (for backward compatibility)
def create_kafka_producer():
    """Create and configure Kafka producer"""
    return _producer_manager.create_producer()


def get_kafka_producer():
    """Get the current Kafka producer instance (creates one if it doesn't exist)"""
    return _producer_manager.get_producer()


def initialize_kafka_producer():
    """Initialize Kafka producer on startup"""
    return _producer_manager.initialize()


def close_kafka_producer():
    """Close Kafka producer connection"""
    _producer_manager.close()


def send_kafka_message(topic, value, key=None):
    """
    Send a message to Kafka topic
    
    Args:
        topic: Kafka topic name
        value: Message value (will be JSON serialized)
        key: Optional message key
    
    Returns:
        Future object or None if producer is not available
    """
    return _producer_manager.send_message(topic, value, key)
