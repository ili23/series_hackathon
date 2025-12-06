"""
Kafka consumer for receiving messages
"""
import json
import logging
from threading import Thread
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from config import KAFKA_CONFIG

logger = logging.getLogger(__name__)


class KafkaConsumerManager:
    """Manages Kafka consumer instance and lifecycle"""
    
    def __init__(self):
        self.consumer = None
        self.consumer_thread = None
    
    def create_consumer(self):
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
                auto_offset_reset='earliest',  # Start from earliest messages
                enable_auto_commit=True,
            )
            logger.info("Kafka consumer created successfully")
            return consumer
        except Exception as e:
            logger.error(f"Error creating Kafka consumer: {e}")
            return None
    
    def _consume_messages(self, event_processor):
        """Consume messages from Kafka (internal method)"""
        if not self.consumer:
            self.consumer = self.create_consumer()
        
        if not self.consumer:
            logger.error("Failed to create Kafka consumer")
            return
        
        logger.info("Starting Kafka consumer...")
        logger.info(f"Subscribed to topic: {KAFKA_CONFIG['topic_name']}")
        
        try:
            # Trigger connection by polling (non-blocking with timeout)
            # This will cause the consumer to connect and get partition assignments
            logger.info("Connecting to Kafka and waiting for partition assignment...")
            self.consumer.poll(timeout_ms=5000)
            
            # Check if consumer has been assigned partitions (indicates it's connected)
            assigned_partitions = self.consumer.assignment()
            if assigned_partitions:
                logger.info(f"✓ Kafka consumer ready! Assigned to {len(assigned_partitions)} partition(s): {assigned_partitions}")
            else:
                logger.warning("Kafka consumer connected but no partitions assigned yet (topic may be empty or doesn't exist)")
            
            # Now start consuming messages
            for message in self.consumer:
                try:
                    event = message.value
                    logger.info(f"Received Kafka message: offset={message.offset}, partition={message.partition}, key={message.key}")
                    event_processor(event)
                    logger.info(f"Successfully processed message: offset={message.offset}")
                except Exception as e:
                    logger.error(f"Error processing message (offset={message.offset}, partition={message.partition}): {e}", exc_info=True)
                    # Continue processing other messages even if one fails
                    # Note: With auto_commit=True, the offset will be committed even if processing fails
                    # Consider switching to manual commit for better reliability
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
        finally:
            if self.consumer:
                self.consumer.close()
    
    def start(self, event_processor):
        """Start consuming messages in a background thread"""
        logger.info("Initializing Kafka consumer...")
        
        # Start consumer in background thread
        self.consumer_thread = Thread(target=self._consume_messages, args=(event_processor,), daemon=True)
        self.consumer_thread.start()
        
        logger.info("Kafka consumer initialization complete")
    
    def stop(self):
        """Stop and close the consumer"""
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka consumer: {e}")
            finally:
                self.consumer = None
    
    def get_consumer(self):
        """Get the current Kafka consumer instance"""
        return self.consumer
    
    def is_ready(self):
        """Check if Kafka consumer is ready to receive messages"""
        if not self.consumer:
            return False
        
        try:
            # Check if consumer has been assigned partitions (indicates it's connected and subscribed)
            assigned_partitions = self.consumer.assignment()
            return len(assigned_partitions) > 0
        except Exception:
            return False


# Create a singleton instance
_consumer_manager = KafkaConsumerManager()


# Convenience functions that use the singleton (for backward compatibility)
def initialize_kafka_consumer(event_processor):
    """Initialize Kafka consumer on app startup"""
    _consumer_manager.start(event_processor)


def close_kafka_consumer():
    """Close Kafka consumer connection"""
    _consumer_manager.stop()


def get_kafka_consumer():
    """Get the current Kafka consumer instance"""
    return _consumer_manager.get_consumer()


def is_kafka_consumer_ready():
    """Check if Kafka consumer is ready to receive messages"""
    return _consumer_manager.is_ready()
