from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.market_data import (
    PriceResponse, 
    PollingJobRequest, 
    PollingJobResponse,
    ErrorResponse
)
from app.services.market_data_service import MarketDataService
from app.services.background_tasks import polling_manager
from app.models.market_data import PollingJob
import logging
import asyncio

logger = logging.getLogger(__name__)

# Create router (similar to @RestController in Spring Boot)
router = APIRouter(
    prefix="/prices",
    tags=["prices"],
    responses={404: {"model": ErrorResponse}}
)

# Create service instance
market_service = MarketDataService()


@router.get("/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL)"),
    provider: Optional[str] = Query(None, description="Market data provider"),
    db: Session = Depends(get_db)
):
    """
    Get the latest price for a given symbol.
    
    - **symbol**: Stock symbol (e.g., AAPL, MSFT)
    - **provider**: Optional provider name (defaults to yfinance)
    """
    try:
        price_data = await market_service.get_latest_price(
            symbol=symbol,
            provider_name=provider,
            db=db
        )
        return PriceResponse(**price_data)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching price: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data")


@router.post("/poll", response_model=PollingJobResponse, status_code=202)
async def create_polling_job(
    request: PollingJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a polling job to fetch prices at regular intervals.
    
    This endpoint accepts the job and returns immediately with 202 Accepted.
    The actual polling happens in the background.
    """
    try:
        # Create polling job record
        job = PollingJob(
            symbols=request.symbols,
            interval=request.interval,
            provider=request.provider.value,
            status="accepted"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Start the background polling task
        asyncio.create_task(
            polling_manager.start_polling_job(
                job_id=job.job_id,
                symbols=job.symbols,
                interval=job.interval,
                provider=job.provider
            )
        )
        
        logger.info(f"Created polling job {job.job_id} for symbols {job.symbols}")
        
        return PollingJobResponse(
            job_id=job.job_id,
            status=job.status,
            config={
                "symbols": job.symbols,
                "interval": job.interval,
                "provider": job.provider
            }
        )
    
    except Exception as e:
        logger.error(f"Error creating polling job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create polling job")


@router.get("/poll/{job_id}", response_model=PollingJobResponse)
async def get_polling_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of a polling job"""
    job = db.query(PollingJob).filter_by(job_id=job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Polling job not found")
    
    # Check if job is in active tasks
    is_active = job_id in polling_manager.get_active_jobs()
    
    return PollingJobResponse(
        job_id=job.job_id,
        status=job.status if not is_active else "running",
        config={
            "symbols": job.symbols,
            "interval": job.interval,
            "provider": job.provider
        }
    )


@router.delete("/poll/{job_id}")
async def stop_polling_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Stop a running polling job"""
    job = db.query(PollingJob).filter_by(job_id=job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Polling job not found")
    
    # Stop the background task
    stopped = polling_manager.stop_polling_job(job_id)
    
    if stopped:
        job.status = "stopped"
        db.commit()
        return {"message": f"Polling job {job_id} stopped successfully"}
    else:
        return {"message": f"Polling job {job_id} was not running"}