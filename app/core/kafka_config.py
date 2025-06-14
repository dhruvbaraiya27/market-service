from confluent_kafka import Producer, Consumer
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class KafkaConfig:
    """Kafka configuration and helper methods"""
    
    @staticmethod
    def get_producer_config():
        """Get Kafka producer configuration"""
        return {
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'client.id': 'market-data-producer',
            'acks': 'all',  # Wait for all replicas to acknowledge
            'compression.type': 'gzip',
            'queue.buffering.max.messages': 100000,
            'queue.buffering.max.ms': 100,
            'batch.num.messages': 500
        }
    
    @staticmethod
    def get_consumer_config(group_id: str = "moving-average-consumer"):
        """Get Kafka consumer configuration"""
        return {
            'bootstrap.servers': settings.kafka_bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',  # Start from beginning if no offset
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 1000,
            'session.timeout.ms': 30000,
            'max.poll.interval.ms': 300000,
        }


class KafkaProducerWrapper:
    """Wrapper for Kafka Producer with error handling"""
    
    def __init__(self):
        self.producer = Producer(KafkaConfig.get_producer_config())
        
    def send_price_event(self, symbol: str, price: float, timestamp: str, 
                        provider: str, raw_response_id: str = None):
        """Send price event to Kafka"""
        try:
            message = {
                "symbol": symbol,
                "price": price,
                "timestamp": timestamp,
                "source": provider,
                "raw_response_id": raw_response_id
            }
            
            # Serialize message
            message_json = json.dumps(message)
            
            # Send to Kafka
            self.producer.produce(
                topic=settings.kafka_topic_price_events,
                value=message_json.encode('utf-8'),
                key=symbol.encode('utf-8'),  # Use symbol as key for partitioning
                callback=self._delivery_callback
            )
            
            # Trigger any queued messages
            self.producer.poll(0)
            
            logger.info(f"Sent price event for {symbol}: ${price}")
            
        except Exception as e:
            logger.error(f"Error sending price event: {str(e)}")
            raise
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')
    
    def flush(self):
        """Flush any pending messages"""
        self.producer.flush()
    
    def __del__(self):
        """Clean up producer on deletion"""
        if hasattr(self, 'producer'):
            self.producer.flush()