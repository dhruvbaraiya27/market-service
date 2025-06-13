import httpx
from datetime import datetime
from typing import Dict, Any
from app.services.providers.base import MarketDataProvider
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage market data provider implementation"""
    
    def __init__(self):
        self.api_key = settings.alpha_vantage_api_key
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_provider_name(self) -> str:
        return "alpha_vantage"
    
    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch latest price from Alpha Vantage
        """
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not configured. Please set ALPHA_VANTAGE_API_KEY in .env")
        
        try:
            # Use GLOBAL_QUOTE function for latest price
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol.upper(),
                "apikey": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            # Check for API limit message
            if "Note" in data:
                logger.warning(f"Alpha Vantage API limit: {data['Note']}")
                raise ValueError("API call frequency limit reached. Please wait and try again.")
            
            # Check for error message
            if "Error Message" in data:
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Extract quote data
            quote = data.get("Global Quote", {})
            if not quote:
                raise ValueError(f"No data returned for symbol: {symbol}")
            
            # Extract price and other data
            price = float(quote.get("05. price", 0))
            if price == 0:
                raise ValueError(f"No valid price data for symbol: {symbol}")
            
            # Parse the timestamp
            latest_trading_day = quote.get("07. latest trading day", "")
            timestamp_str = f"{latest_trading_day} {quote.get('08. previous close', '')}"
            
            return {
                "symbol": quote.get("01. symbol", symbol.upper()),
                "price": price,
                "timestamp": datetime.utcnow(),  # Use current time since we get latest price
                "raw_data": {
                    "source": "alpha_vantage",
                    "quote": quote,
                    "open": float(quote.get("02. open", 0)),
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                    "volume": int(quote.get("06. volume", 0)),
                    "latest_trading_day": latest_trading_day,
                    "previous_close": float(quote.get("08. previous close", 0)),
                    "change": quote.get("09. change", ""),
                    "change_percent": quote.get("10. change percent", "")
                }
            }
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching price for {symbol}: {str(e)}")
            raise ValueError(f"Network error: Unable to reach Alpha Vantage API")
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            raise ValueError(f"Failed to fetch price for {symbol}: {str(e)}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate symbol format for Alpha Vantage
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Alpha Vantage accepts standard stock symbols
        import re
        return bool(re.match(r'^[A-Z]{1,5}$', symbol.upper()))