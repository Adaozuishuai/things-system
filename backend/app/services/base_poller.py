import asyncio
import logging
from typing import Optional, Any
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)

class BasePoller(ABC):
    def __init__(self, name: str = "BasePoller"):
        self.logger = logging.getLogger(name)
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.poll_interval: int = 5  # seconds
        
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if poller is properly configured to start"""
        pass

    @abstractmethod
    async def _poll_step(self):
        """Execute a single polling step"""
        pass

    async def start(self):
        if self.is_running:
            self.logger.warning("Poller is already running")
            return
            
        if not self.is_configured():
            self.logger.error("Poller not configured properly")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._poll_loop())
        self.logger.info("Poller started")

    async def stop(self):
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.logger.info("Poller stopped")

    async def _poll_loop(self):
        while self.is_running:
            try:
                await self._poll_step()
            except Exception as e:
                self.logger.error(f"Poller loop error: {e}")
            
            await asyncio.sleep(self.poll_interval)
