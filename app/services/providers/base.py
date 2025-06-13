from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class MarketDataProvider(ABC):
    """
    Abstract base class for market data providers.
    Similar to interface in Java/Spring Boot.
    """
    
    @abstractmethod
    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the latest price for a given symbol.
        
        Returns:
            Dict containing at least:
            - symbol: str
            - price: float
            - timestamp: datetime
            - raw_data: Any (original response)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name"""
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is supported by this provider"""
        pass