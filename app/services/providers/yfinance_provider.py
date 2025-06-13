import yfinance as yf
from datetime import datetime
from typing import Dict, Any
from app.services.providers.base import MarketDataProvider
import logging

logger = logging.getLogger(__name__)


class YFinanceProvider(MarketDataProvider):
    """Yahoo Finance market data provider implementation"""
    
    def get_provider_name(self) -> str:
        return "yfinance"
    
    async def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch latest price from Yahoo Finance with better error handling
        """
        try:
            # Get ticker object
            ticker = yf.Ticker(symbol.upper())
            
            # First try: Get fast_info (more reliable)
            try:
                fast_info = ticker.fast_info
                price = fast_info.get('lastPrice') or fast_info.get('regularMarketPrice')
                
                if price and price > 0:
                    return {
                        "symbol": symbol.upper(),
                        "price": float(price),
                        "timestamp": datetime.utcnow(),
                        "raw_data": {"source": "fast_info", "data": dict(fast_info)}
                    }
            except:
                logger.warning(f"fast_info failed for {symbol}, trying history")
            
            # Second try: Get recent history
            hist = ticker.history(period="1d")
            
            if hist.empty:
                # Try with a longer period
                hist = ticker.history(period="5d")
            
            if not hist.empty:
                # Get the most recent closing price
                latest_price = float(hist['Close'].iloc[-1])
                latest_time = hist.index[-1]
                
                return {
                    "symbol": symbol.upper(),
                    "price": latest_price,
                    "timestamp": datetime.utcnow(),
                    "raw_data": {
                        "source": "history",
                        "latest_day": str(latest_time),
                        "open": float(hist['Open'].iloc[-1]),
                        "high": float(hist['High'].iloc[-1]),
                        "low": float(hist['Low'].iloc[-1]),
                        "close": latest_price,
                        "volume": int(hist['Volume'].iloc[-1])
                    }
                }
            
            # If we get here, no data was found
            raise ValueError(f"No price data available for {symbol}")
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            # Try one more time with a known good symbol to check if it's a connection issue
            try:
                test_ticker = yf.Ticker("SPY")
                test_hist = test_ticker.history(period="1d")
                if test_hist.empty:
                    raise ValueError("YFinance connection issue - unable to fetch any data")
            except:
                raise ValueError("YFinance service appears to be down")
            
            raise ValueError(f"Failed to fetch price for {symbol}: {str(e)}")
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Basic validation - Yahoo Finance accepts most symbols
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation - alphanumeric with some special chars
        import re
        return bool(re.match(r'^[A-Z0-9\.\-\^=]+$', symbol.upper()))