import aiohttp
from typing import Optional, Dict, Any
from app.services.base_poller import BasePoller
from app.models import IntelItem
from app.agent.orchestrator import orchestrator

class ArticlePoller(BasePoller):
    def __init__(self):
        super().__init__("poller")
        self.base_url: Optional[str] = None
        self.current_id: int = 6617
        
    def configure(self, base_url: str, start_id: int = 6617, interval: int = 5):
        self.base_url = base_url.rstrip('/')
        self.current_id = start_id
        self.poll_interval = interval
        self.logger.info(f"Poller configured: URL={self.base_url}, StartID={self.current_id}, Interval={self.poll_interval}s")

    def is_configured(self) -> bool:
        return bool(self.base_url)

    async def _poll_step(self):
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/articles/{self.current_id}?depth=2&draft=false&locale=undefined"
            self.logger.info(f"Polling: {url}")
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self._process_data(data)
                    self.current_id += 1
                elif response.status == 404:
                    self.logger.debug(f"ID {self.current_id} not found, waiting...")
                else:
                    self.logger.warning(f"Error fetching {url}: {response.status}")

    async def _process_data(self, data: Dict[str, Any]):
        try:
            item = IntelItem.from_cms_data(data, self.current_id)
            await orchestrator.broadcast("new_intel", item.model_dump())
            self.logger.info(f"Broadcasted article {self.current_id}")
        except Exception as e:
            self.logger.error(f"Error processing data: {e}")

article_poller = ArticlePoller()
