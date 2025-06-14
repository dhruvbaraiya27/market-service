import asyncio
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.market_data_service import MarketDataService
from app.models.market_data import PollingJob
import logging

logger = logging.getLogger(__name__)


class PollingTaskManager:
    """Manages background polling tasks for fetching prices at intervals"""
    
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.market_service = MarketDataService()
        logger.info("Polling Task Manager initialized")
    
    async def start_polling_job(self, job_id: str, symbols: List[str], 
                               interval: int, provider: str):
        """
        Start a background task that polls for prices at specified intervals
        
        Args:
            job_id: Unique identifier for this polling job
            symbols: List of stock symbols to fetch
            interval: Seconds between each poll
            provider: Market data provider to use
        """
        try:
            # Create the polling task
            task = asyncio.create_task(
                self._poll_prices(job_id, symbols, interval, provider)
            )
            
            # Store reference to the task
            self.active_tasks[job_id] = task
            
            logger.info(f"Started polling job {job_id} for symbols {symbols} "
                       f"every {interval} seconds")
            
        except Exception as e:
            logger.error(f"Failed to start polling job {job_id}: {str(e)}")
            raise
    
    async def _poll_prices(self, job_id: str, symbols: List[str], 
                          interval: int, provider: str):
        """
        The actual polling loop that runs in the background
        """
        logger.info(f"Polling task {job_id} started")
        
        while True:
            try:
                # Update job status to show it's running
                self._update_job_status(job_id, "running")
                
                # Fetch price for each symbol
                for symbol in symbols:
                    try:
                        # Create a new database session for this operation
                        db = SessionLocal()
                        
                        logger.info(f"Polling price for {symbol}")
                        
                        # Fetch the latest price
                        await self.market_service.get_latest_price(
                            symbol=symbol,
                            provider_name=provider,
                            db=db
                        )
                        
                        db.close()
                        
                        # Small delay between symbols to avoid rate limits
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error polling {symbol}: {str(e)}")
                        continue
                
                # Wait for the specified interval before next poll
                logger.info(f"Polling job {job_id} completed cycle, "
                           f"waiting {interval} seconds")
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                # Task was cancelled, clean up and exit
                logger.info(f"Polling job {job_id} cancelled")
                self._update_job_status(job_id, "cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling job {job_id}: {str(e)}")
                await asyncio.sleep(interval)  # Continue after error
    
    def stop_polling_job(self, job_id: str):
        """Stop a running polling job"""
        if job_id in self.active_tasks:
            task = self.active_tasks[job_id]
            task.cancel()
            del self.active_tasks[job_id]
            self._update_job_status(job_id, "stopped")
            logger.info(f"Stopped polling job {job_id}")
            return True
        return False
    
    def get_active_jobs(self) -> List[str]:
        """Get list of currently active job IDs"""
        return list(self.active_tasks.keys())
    
    def _update_job_status(self, job_id: str, status: str):
        """Update the status of a polling job in the database"""
        db = SessionLocal()
        try:
            job = db.query(PollingJob).filter_by(job_id=job_id).first()
            if job:
                job.status = status
                job.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
        finally:
            db.close()


# Global instance of the task manager
polling_manager = PollingTaskManager()