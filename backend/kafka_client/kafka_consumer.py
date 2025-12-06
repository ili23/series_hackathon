"""
Kafka consumer for receiving messages
"""
import json
import logging
import time
from threading import Thread
from kafka import KafkaConsumer
from kafka.errors import KafkaError, KafkaTimeoutError
from config import KAFKA_CONFIG

logger = logging.getLogger(__name__)


class KafkaConsumerManager:
    """Manages Kafka consumer instance and lifecycle"""
    # Defaults in case __init__ is bypassed in a long-lived process
    consumer = None
    consumer_thread = None
    running = False
    restart_count = 0
    max_restarts = 10
    
    def __init__(self):
        self.consumer = None
        self.consumer_thread = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 10
    
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
            logger.debug("Kafka consumer created")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return None
    
    def _consume_messages(self, event_processor):
        """Consume messages from Kafka with automatic restart on heartbeat failures"""
        while self.running and self.restart_count < self.max_restarts:
            try:
                # Create or recreate consumer
                if not self.consumer:
                    self.consumer = self.create_consumer()
                
                if not self.consumer:
                    logger.error("Failed to create Kafka consumer")
                    break
                
                logger.info(f"Starting Kafka consumer (topic: {KAFKA_CONFIG['topic_name']})")
                
                # Wait for partition assignment - this is required for Kafka to work
                # Partition assignment happens asynchronously during consumer group join
                max_wait_time = 30  # Maximum seconds to wait for partition assignment
                wait_interval = 1  # Check every second
                waited_time = 0
                assigned_partitions = set()
                
                while self.running and waited_time < max_wait_time:
                    # Poll to trigger consumer group join and partition assignment
                    self.consumer.poll(timeout_ms=1000)
                    
                    # Check if partitions have been assigned
                    assigned_partitions = self.consumer.assignment()
                    if assigned_partitions:
                        logger.info(f"Kafka consumer ready ({len(assigned_partitions)} partition(s))")
                        self.restart_count = 0  # Reset on successful connection
                        break
                    
                    waited_time += wait_interval
                    if waited_time % 5 == 0:  # Log every 5 seconds
                        logger.info(f"Waiting for partition assignment... ({waited_time}s)")
                
                # If no partitions assigned after waiting, this is a critical error
                if not assigned_partitions:
                    logger.error(f"Failed to get partition assignment after {max_wait_time}s. "
                               "Kafka consumer cannot receive messages without partitions. "
                               "Check topic exists and consumer group permissions.")
                    # Close consumer and retry
                    if self.consumer:
                        try:
                            self.consumer.close()
                        except:
                            pass
                        self.consumer = None
                    
                    # Wait before retrying
                    if self.restart_count < self.max_restarts:
                        wait_time = min(2 ** self.restart_count, 30)
                        logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max restart attempts reached, stopping")
                        break
                
                # Consume messages with timeout to allow heartbeat checks
                # Using poll() instead of iterator to have better control
                last_status_log = time.time()
                status_log_interval = 10  # Log status every 10 seconds
                
                while self.running:
                    try:
                        # Poll for messages with timeout - this allows heartbeats to be sent
                        message_batch = self.consumer.poll(timeout_ms=1000, max_records=1)
                        
                        # Periodic status logging to confirm consumer is active
                        current_time = time.time()
                        if current_time - last_status_log >= status_log_interval:
                            assigned_partitions = self.consumer.assignment()
                            logger.info(f"Kafka consumer active - polling for messages (partitions: {len(assigned_partitions)})")
                            last_status_log = current_time
                        
                        if not message_batch:
                            continue  # No messages, continue polling (heartbeats still sent)
                        
                        # Process each message
                        for topic_partition, messages in message_batch.items():
                            for message in messages:
                                try:
                                    event = message.value
                                    logger.debug(f"Processing message offset={message.offset}")
                                    
                                    # Process event (this may take a while for voice transcription)
                                    event_processor(event)
                                    
                                except Exception as e:
                                    logger.error(f"Error processing message offset={message.offset}: {e}", exc_info=True)
                                    # Continue processing other messages
                                    
                    except (KafkaError, KafkaTimeoutError) as e:
                        error_msg = str(e).lower()
                        if 'heartbeat' in error_msg or 'timeout' in error_msg or 'session' in error_msg:
                            logger.warning(f"Heartbeat timeout (processing took too long), restarting...")
                            raise  # Break out to restart
                        else:
                            raise  # Re-raise other Kafka errors
                            
            except (KafkaError, KafkaTimeoutError) as e:
                error_msg = str(e).lower()
                if 'heartbeat' in error_msg or 'timeout' in error_msg or 'session' in error_msg:
                    self.restart_count += 1
                    logger.warning(f"Heartbeat failure (attempt {self.restart_count}/{self.max_restarts})")
                    
                    # Close current consumer
                    if self.consumer:
                        try:
                            self.consumer.close()
                        except:
                            pass
                        self.consumer = None
                    
                    if self.restart_count < self.max_restarts:
                        wait_time = min(2 ** self.restart_count, 30)
                        logger.info(f"Restarting in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max restart attempts reached, stopping")
                        break
                else:
                    logger.error(f"Kafka error: {e}")
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error in consumer: {e}", exc_info=True)
                break
            finally:
                if self.consumer:
                    try:
                        self.consumer.close()
                    except:
                        pass
                    self.consumer = None
        
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
        self.running = True
        self.restart_count = 0
        
        # Start consumer in background thread
        self.consumer_thread = Thread(target=self._consume_messages, args=(event_processor,), daemon=True)
        self.consumer_thread.start()
        
        logger.info("Kafka consumer initialized")
    
    def stop(self):
        """Stop and close the consumer"""
        if self.consumer:
            try:
                self.consumer.close()
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
