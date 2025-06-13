from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.providers.base import MarketDataProvider
from app.services.providers.yfinance_provider import YFinanceProvider
from app.services.providers.alpha_vantage_provider import AlphaVantageProvider
from app.models.market_data import RawMarketData, PricePoint
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Service layer for market data operations.
    Similar to @Service in Spring Boot.
    """
    
    def __init__(self):
        # Initialize providers
        self.providers: Dict[str, MarketDataProvider] = {
            "yfinance": YFinanceProvider(),
            "alpha_vantage": AlphaVantageProvider(),
            # Add more providers here as needed
        }
        self.default_provider = settings.default_provider
    
    def get_provider(self, provider_name: Optional[str] = None) -> MarketDataProvider:
        """Get a specific provider or the default one"""
        provider_name = provider_name or self.default_provider
        
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        return self.providers[provider_name]
    
    async def get_latest_price(
        self, 
        symbol: str, 
        provider_name: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, any]:
        """
        Get latest price for a symbol from specified provider
        """
        provider = self.get_provider(provider_name)
        
        # Validate symbol
        if not provider.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        # Fetch price data
        price_data = await provider.get_latest_price(symbol)
        
        # Store in database if session provided
        if db:
            # Store raw response
            raw_data = RawMarketData(
                symbol=price_data["symbol"],
                provider=provider.get_provider_name(),
                raw_response=price_data["raw_data"]
            )
            db.add(raw_data)
            db.flush()  # Get the ID
            
            # Store processed price point
            price_point = PricePoint(
                symbol=price_data["symbol"],
                price=price_data["price"],
                timestamp=price_data["timestamp"],
                provider=provider.get_provider_name(),
                raw_data_id=raw_data.id
            )
            db.add(price_point)
            db.commit()
            
            logger.info(f"Stored price data for {symbol}: ${price_data['price']}")
        
        # Return formatted response
        return {
            "symbol": price_data["symbol"],
            "price": price_data["price"],
            "timestamp": price_data["timestamp"],
            "provider": provider.get_provider_name()
        }