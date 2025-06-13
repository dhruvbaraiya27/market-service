from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class RawMarketData(Base):
    """Stores raw responses from market data providers"""
    __tablename__ = "raw_market_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    raw_response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Create indexes for faster queries
    __table_args__ = (
        Index('idx_raw_market_symbol_provider', 'symbol', 'provider'),
        Index('idx_raw_market_created', 'created_at'),
    )


class PricePoint(Base):
    """Stores processed price points"""
    __tablename__ = "price_points"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    provider = Column(String, nullable=False)
    raw_data_id = Column(String, nullable=True)  # Reference to raw_market_data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_price_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_price_provider', 'provider'),
    )


class MovingAverage(Base):
    """Stores calculated moving averages"""
    __tablename__ = "moving_averages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    average_price = Column(Float, nullable=False)
    period = Column(Integer, default=5)  # 5-point MA
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_ma_symbol_calculated', 'symbol', 'calculated_at'),
    )


class PollingJob(Base):
    """Stores polling job configurations"""
    __tablename__ = "polling_jobs"
    
    job_id = Column(String, primary_key=True, default=lambda: f"poll_{uuid.uuid4().hex[:8]}")
    symbols = Column(JSON, nullable=False)  # List of symbols
    interval = Column(Integer, nullable=False)  # Polling interval in seconds
    provider = Column(String, nullable=False)
    status = Column(String, default="active")  # active, paused, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())