from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    app_name: str = "Market Data Service"
    api_version: str = "v1"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/market_data"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 300  # 5 minutes cache
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_price_events: str = "price-events"
    
    # Market Data Providers
    alpha_vantage_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    default_provider: str = "yfinance"
    
    # Rate limiting
    rate_limit_calls: int = 5
    rate_limit_period: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Create a cached instance of settings.
    Similar to @Configuration in Spring Boot
    """
    return Settings()


# Create a global settings instance
settings = get_settings()