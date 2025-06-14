from confluent_kafka import Consumer, KafkaError
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.kafka_config import KafkaConfig
from app.models.market_data import PricePoint, MovingAverage
from datetime import datetime
import json
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovingAverageConsumer:
    """
    Kafka consumer that calculates moving averages for stock prices
    """
    
    def __init__(self):
        # Create database connection
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create Kafka consumer
        self.consumer = Consumer(KafkaConfig.get_consumer_config())
        self.consumer.subscribe([settings.kafka_topic_price_events])
        
        # Flag for graceful shutdown
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Moving Average Consumer initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received, stopping consumer...")
        self.running = False
    
    def calculate_moving_average(self, symbol: str, period: int = 5) -> float:
        """
        Calculate moving average for a symbol
        
        Args:
            symbol: Stock symbol
            period: Number of periods for moving average (default: 5)
        
        Returns:
            Moving average value
        """
        db = self.SessionLocal()
        try:
            # Get last N price points
            price_points = db.query(PricePoint).filter(
                PricePoint.symbol == symbol
            ).order_by(
                desc(PricePoint.timestamp)
            ).limit(period).all()
            
            if len(price_points) < period:
                logger.warning(f"Not enough data points for {symbol}. "
                             f"Have {len(price_points)}, need {period}")
                return None
            
            # Calculate average
            prices = [p.price for p in price_points]
            moving_avg = sum(prices) / len(prices)
            
            logger.info(f"Calculated {period}-point MA for {symbol}: "
                       f"{moving_avg:.2f} (prices: {prices})")
            
            return moving_avg
            
        finally:
            db.close()
    
    def store_moving_average(self, symbol: str, average: float, period: int = 5):
        """Store calculated moving average in database"""
        db = self.SessionLocal()
        try:
            ma_record = MovingAverage(
                symbol=symbol,
                average_price=average,
                period=period,
                calculated_at=datetime.utcnow()
            )
            db.add(ma_record)
            db.commit()
            
            logger.info(f"Stored MA for {symbol}: {average:.2f}")
            
        except Exception as e:
            logger.error(f"Error storing moving average: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def process_message(self, message: dict):
        """Process a single price event message"""
        try:
            symbol = message.get('symbol')
            price = message.get('price')
            
            logger.info(f"Processing price event: {symbol} @ ${price}")
            
            # Calculate moving average
            moving_avg = self.calculate_moving_average(symbol)
            
            if moving_avg is not None:
                # Store the moving average
                self.store_moving_average(symbol, moving_avg)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def run(self):
        """Main consumer loop"""
        logger.info("Starting Moving Average Consumer...")
        
        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                # Parse message
                try:
                    message_value = msg.value().decode('utf-8')
                    message_data = json.loads(message_value)
                    
                    # Process the message
                    self.process_message(message_data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        finally:
            # Clean up
            logger.info("Closing consumer...")
            self.consumer.close()
            logger.info("Consumer closed successfully")


def main():
    """Entry point for the consumer"""
    consumer = MovingAverageConsumer()
    consumer.run()


if __name__ == "__main__":
    main()