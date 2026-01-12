import asyncio
import aiohttp
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from app.services.base_poller import BasePoller
from app.models import Tag, IntelItem
from app.agent.orchestrator import orchestrator

from app.database import SessionLocal
from app import crud

class PayloadPoller(BasePoller):
    def __init__(self):
        super().__init__("payload_poller")
        self.cms_url: Optional[str] = None
        self.user_collection: str = "users"
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.collection_slug: Optional[str] = None
        
        self.poll_interval: int = 10  # seconds
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None
        self.last_fetched_ids: set = set()
        self.last_cleanup_time: float = 0 # Timestamp of last DB cleanup

    def configure(self, cms_url: str, collection_slug: str, email: str, password: str, user_collection: str = "users", interval: int = 10):
        self.cms_url = cms_url.rstrip('/')
        self.collection_slug = collection_slug
        self.email = email
        self.password = password
        self.user_collection = user_collection
        self.poll_interval = max(2, interval)
        self.logger.info(f"PayloadPoller configured: URL={self.cms_url}, Collection={self.collection_slug}, User={self.email}")

    def is_configured(self) -> bool:
        return all([self.cms_url, self.collection_slug, self.email, self.password])

    async def stop(self):
        await super().stop()
        if self.session:
            await self.session.close()
            self.session = None

    async def _login(self) -> bool:
        if not self.session:
            self.session = aiohttp.ClientSession()

        login_url = f"{self.cms_url}/api/{self.user_collection}/login"
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        try:
            async with self.session.post(login_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token")
                    self.logger.info(f"Payload CMS login successful. Token acquired: {bool(self.token)}")
                    return True
                else:
                    self.logger.error(f"Payload CMS login failed: {response.status}")
                    text = await response.text()
                    self.logger.error(f"Response: {text}")
                    return False
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    async def _poll_step(self):
        # 0. Daily DB Cleanup
        now = datetime.now().timestamp()
        if now - self.last_cleanup_time > 86400: # 24 hours
            retention_days_raw = (os.getenv("INTEL_RETENTION_DAYS") or "").strip()
            if retention_days_raw:
                try:
                    retention_days = int(retention_days_raw)
                except Exception:
                    retention_days = 0
                if retention_days > 0:
                    self.logger.info(f"Running daily DB cleanup (retention_days={retention_days})...")
                    db = SessionLocal()
                    try:
                        deleted = crud.delete_old_intel_items(db, days=retention_days)
                        if deleted > 0:
                            self.logger.info(f"Cleaned up {deleted} old items.")
                        self.last_cleanup_time = now
                    except Exception as e:
                        self.logger.error(f"Cleanup failed: {e}")
                    finally:
                        db.close()
                else:
                    self.last_cleanup_time = now
            else:
                self.last_cleanup_time = now

        # Initial login if needed
        if not self.token:
            if not await self._login():
                self.logger.error("Login failed. Retrying next cycle.")
                return

        if not self.session:
            self.session = aiohttp.ClientSession()

        fetch_url = f"{self.cms_url}/api/{self.collection_slug}"
        # Add query params if needed, e.g., sort by date
        # fetch_url += "?sort=-createdAt&limit=10"
        
        self.logger.info(f"Polling Payload CMS: {fetch_url}")
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"JWT {self.token}"

        async with self.session.get(fetch_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                await self._process_data(data)
            elif response.status == 401 or response.status == 403:
                self.logger.warning("Unauthorized, attempting to re-login...")
                self.token = None # Clear token to force re-login
                if await self._login():
                    # Retry once immediately
                    headers["Authorization"] = f"JWT {self.token}"
                    async with self.session.get(fetch_url, headers=headers) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            await self._process_data(data)
            else:
                self.logger.warning(f"Error fetching data: {response.status}")

    async def _process_data(self, data: Dict[str, Any]):
        """
        Process the fetched collection data.
        Payload CMS returns { "docs": [...] }
        """
        docs = data.get("docs", [])
        if not docs:
            self.logger.info("No docs found in response")
            return

        # 1. Filter new items
        new_docs = []
        for doc in docs:
            doc_id = doc.get("id")
            if doc_id in self.last_fetched_ids:
                continue
            self.last_fetched_ids.add(doc_id)
            new_docs.append(doc)

        # Limit tracked IDs
        if len(self.last_fetched_ids) > 1000:
            self.last_fetched_ids = set(list(self.last_fetched_ids)[-500:])

        if not new_docs:
            return

        self.logger.info(f"Processing {len(new_docs)} new items...")

        # 2. Refine items using LLM (Concurrent with limit)
        # SKIP LLM Refinement - Direct Pass Through
        refined_item_dicts = []
        
        for doc in new_docs:
            # DEBUG: Log keys to check availability of thingId and url
            if len(refined_item_dicts) == 0:
                self.logger.debug(f"Doc keys: {list(doc.keys())}")
                self.logger.debug(f"Doc thingId: {doc.get('thingId')}")
                self.logger.debug(f"Doc url: {doc.get('url')}")

            # Pre-map to dict structure expected by Orchestrator
            # We keep 'original' for context if available
            raw_item_dict = {
                "id": str(doc.get("id", uuid.uuid4())),
                "title": doc.get("title") or "Untitled",
                "summary": doc.get("summary") or doc.get("description") or "",
                "original": doc.get("original") or doc.get("content") or "",
                "content": doc.get("original") or doc.get("content") or "", # Map original content to content field
                "tags": [], # Will be filled by Refiner
                "thingId": doc.get("thingId"),
                # Pass through other fields needed for mapping later
                "publishDate": doc.get("publishDate") or doc.get("createdAt"),
                "source": doc.get("author") or "PayloadCMS",
                "url": doc.get("url") or f"{self.cms_url}/admin/collections/{self.collection_slug}/{doc.get('id')}",
                # Pass through custom CMS fields so they are available in _dict_to_intel_item
                "regional_country": doc.get("regional_country"),
                "domain": doc.get("domain"),
                "topicType": doc.get("topicType")
            }
            # Directly use raw item without LLM refinement
            refined_item_dicts.append(raw_item_dict)
        
        # Execute refinement concurrently with limit
        # refined_item_dicts = await asyncio.gather(*tasks)

        items: List[IntelItem] = []
        for item_dict in refined_item_dicts:
            self.logger.debug(f"Preparing to broadcast item: {item_dict.get('id')}")
            item = self._dict_to_intel_item(item_dict)
            if not item:
                self.logger.error(f"Failed to map item {item_dict.get('id')} to IntelItem model")
                continue
            items.append(item)

        if not items:
            return

        def _persist_batch(batch: List[IntelItem]) -> int:
            db = SessionLocal()
            try:
                return crud.upsert_intel_items(db, batch)
            finally:
                db.close()

        try:
            await asyncio.to_thread(_persist_batch, items)
        except Exception as e:
            self.logger.error(f"DB upsert batch failed: {e}")
            return

        broadcast_count = 0
        for item in items:
            await orchestrator.broadcast("new_intel", item.model_dump())
            broadcast_count += 1

        if broadcast_count > 0:
            self.logger.info(f"Broadcasted {broadcast_count} new items")

    async def _refine_with_semaphore(self, raw_item_dict: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        async with semaphore:
            return await orchestrator.refine_intel_item(raw_item_dict)

    def _dict_to_intel_item(self, data: Dict[str, Any]) -> Optional[IntelItem]:
        try:
            # Handle Date
            date_str = data.get("publishDate") or datetime.now().isoformat()
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                dt = datetime.now()
            
            display_time = dt.strftime("%Y/%m/%d %H:%M")
            timestamp = dt.timestamp()

            # Handle Tags (Refiner returns list of dicts, we need list of Tag objects)
            tags = []
            
            # 1. AI Refined Tags
            raw_tags = data.get("tags", [])
            for t in raw_tags:
                if isinstance(t, dict):
                     tags.append(Tag(label=t.get("label"), color=t.get("color", "gray")))
                elif isinstance(t, str):
                     tags.append(Tag(label=t, color="gray"))

            # 2. CMS Original Fields (regional_country, domain)
            # regional_country -> Red Tags
            if "regional_country" in data:
                rc = data["regional_country"]
                if isinstance(rc, list):
                    for c in rc:
                        tags.append(Tag(label=str(c), color="red"))
                elif isinstance(rc, str):
                    tags.append(Tag(label=rc, color="red"))
            
            # domain -> Blue Tags
            if "domain" in data:
                dm = data["domain"]
                if isinstance(dm, list):
                    for d in dm:
                        tags.append(Tag(label=str(d), color="blue"))
                elif isinstance(dm, str):
                    tags.append(Tag(label=dm, color="blue"))

            # topicType -> Gray Tags (Optional)
            if "topicType" in data:
                 tt = data["topicType"]
                 if isinstance(tt, str):
                     # Split by comma if needed, e.g. "Military,Test"
                     for t_part in tt.split(','):
                         if t_part.strip():
                             tags.append(Tag(label=t_part.strip(), color="gray"))

            thing_id = str(data.get("thingId") or data.get("thing_id")) if (data.get("thingId") or data.get("thing_id")) else None
            if thing_id:
                item_id = thing_id
            else:
                url = data.get("url")
                if url:
                    item_id = IntelItem._stable_id_from_value(url)
                else:
                    item_id = str(data.get("id"))

            return IntelItem(
                id=str(item_id),
                title=str(data.get("title")),
                summary=str(data.get("summary")),
                source=str(data.get("source")),
                url=str(data.get("url")),
                time=display_time,
                timestamp=timestamp,
                tags=tags,
                favorited=False,
                is_hot=True,
                content=str(data.get("content")) if data.get("content") else None,
                thing_id=thing_id
            )
        except Exception as e:
            self.logger.error(f"Error mapping dict to IntelItem: {e}")
            return None


# Global instance
payload_poller = PayloadPoller()
