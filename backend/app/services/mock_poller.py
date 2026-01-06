import asyncio
import random
import uuid
from datetime import datetime
from app.services.base_poller import BasePoller
from app.models import Tag, IntelItem
from app.agent.orchestrator import orchestrator

class MockPoller(BasePoller):
    def __init__(self):
        super().__init__("mock_poller")
        self.poll_interval = 2 # Generate every 2 seconds
        
        self.sample_titles = [
            "Regional tensions rise in Eastern Europe",
            "New trade agreement signed in Southeast Asia",
            "Cybersecurity threat detected in financial sector",
            "Tech giant announces breakthrough in AI",
            "Energy prices surge amidst global uncertainty",
            "Diplomatic talks scheduled for next week",
            "Local elections yield unexpected results"
        ]
        
        self.sample_sources = ["Reuters", "AP", "BBC", "CNN", "Al Jazeera", "TechCrunch"]
        self.sample_countries = ["US", "CN", "RU", "UK", "FR", "DE", "JP", "KR"]

    def is_configured(self) -> bool:
        return True # Always configured

    async def _poll_step(self):
        # Generate a random item
        item = self._generate_mock_item()
        
        # Log to file for debugging
        with open("mock_poller_debug.log", "a") as f:
            f.write(f"{datetime.now()}: Generated mock item {item.title}\n")
            
        # Broadcast
        await orchestrator.broadcast("new_intel", item.model_dump())
        self.logger.info(f"Broadcasted mock item: {item.title}")

    def _generate_mock_item(self) -> IntelItem:
        title = random.choice(self.sample_titles)
        source = random.choice(self.sample_sources)
        
        tags = []
        # Random country tag
        if random.random() > 0.5:
            tags.append(Tag(label=random.choice(self.sample_countries), color="red"))
        # Random topic tag
        tags.append(Tag(label="MockData", color="gray"))
        
        return IntelItem(
            id=str(uuid.uuid4()),
            title=f"[MOCK] {title}",
            summary=f"This is a simulated intelligence item generated at {datetime.now().strftime('%H:%M:%S')}. It represents real-time data flow.",
            source=source,
            url="http://localhost:5173",
            time=datetime.now().strftime("%Y/%m/%d %H:%M"),
            timestamp=datetime.now().timestamp(),
            tags=tags,
            favorited=False,
            is_hot=True
        )

# Global instance
mock_poller = MockPoller()
