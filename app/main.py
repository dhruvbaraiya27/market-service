from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import prices
from app.core.database import Base, engine
from app.core.logging import setup_logging

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI instance
app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Market Data Service - Fetches and processes market data",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": settings.app_name,
        "version": settings.api_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name
    }


# Include routers
app.include_router(prices.router, prefix="/api/v1")


# This will be imported by uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )