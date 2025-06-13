from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class MarketDataProvider(str, Enum):
    """Supported market data providers"""
    ALPHA_VANTAGE = "alpha_vantage"
    YFINANCE = "yfinance"
    FINNHUB = "finnhub"


class PriceResponse(BaseModel):
    """Response model for price endpoints"""
    symbol: str
    price: float
    timestamp: datetime
    provider: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PollingJobRequest(BaseModel):
    """Request model for creating polling jobs"""
    symbols: List[str] = Field(..., min_items=1, max_items=10)
    interval: int = Field(..., ge=10, le=3600)  # 10 seconds to 1 hour
    provider: MarketDataProvider = MarketDataProvider.YFINANCE
    
    @validator('symbols')
    def validate_symbols(cls, v):
        # Convert to uppercase and remove duplicates
        return list(set([s.upper() for s in v]))


class PollingJobResponse(BaseModel):
    """Response model for polling job creation"""
    job_id: str
    status: str
    config: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)