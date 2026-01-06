import asyncio
import aiohttp
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
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

    def configure(self, cms_url: str, collection_slug: str, email: str, password: str, user_collection: str = "users", interval: int = 10):
        self.cms_url = cms_url.rstrip('/')
        self.collection_slug = collection_slug
        self.email = email
        self.password = password
        self.user_collection = user_collection
        self.poll_interval = interval
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

        # 2. Refine items using LLM (Concurrent)
        tasks = []
        for doc in new_docs:
            # Pre-map to dict structure expected by Orchestrator
            # We keep 'original' for context if available
            raw_item_dict = {
                "id": str(doc.get("id", uuid.uuid4())),
                "title": doc.get("title") or "Untitled",
                "summary": doc.get("summary") or doc.get("description") or "",
                "original": doc.get("original") or doc.get("content") or "",
                "tags": [], # Will be filled by Refiner
                # Pass through other fields needed for mapping later
                "publishDate": doc.get("publishDate") or doc.get("createdAt"),
                "source": doc.get("author") or "PayloadCMS",
                "url": f"{self.cms_url}/admin/collections/{self.collection_slug}/{doc.get('id')}",
                # Pass through custom CMS fields so they are available in _dict_to_intel_item
                "regional_country": doc.get("regional_country"),
                "domain": doc.get("domain"),
                "topicType": doc.get("topicType")
            }
            tasks.append(orchestrator.refine_intel_item(raw_item_dict))
        
        # Execute refinement concurrently
        refined_item_dicts = await asyncio.gather(*tasks)

        # 3. Save and Broadcast
        new_items_count = 0
        db = SessionLocal()
        try:
            for item_dict in refined_item_dicts:
                # Convert dict back to IntelItem model
                item = self._dict_to_intel_item(item_dict)
                if not item:
                    continue

                # Save to Database
                try:
                    existing = crud.get_intel_by_id(db, item.id)
                    if not existing:
                        crud.create_intel_item(db, item)
                        new_items_count += 1
                        # Broadcast
                        await orchestrator.broadcast("new_intel", item.model_dump())
                except Exception as e:
                    self.logger.error(f"Error saving item {item.id} to DB: {e}")
        finally:
            db.close()
        
        if new_items_count > 0:
            self.logger.info(f"Refined and broadcasted {new_items_count} new items")

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

            return IntelItem(
                id=str(data.get("id")),
                title=str(data.get("title")),
                summary=str(data.get("summary")),
                source=str(data.get("source")),
                url=str(data.get("url")),
                time=display_time,
                timestamp=timestamp,
                tags=tags,
                favorited=False,
                is_hot=True
            )
        except Exception as e:
            self.logger.error(f"Error mapping dict to IntelItem: {e}")
            return None
        try:
            # Flexible mapping based on common fields
            title = doc.get("title") or doc.get("name") or "Untitled"
            summary = doc.get("summary") or doc.get("description") or doc.get("content") or ""
            if isinstance(summary, dict): # Handle rich text or JSON content
                summary = json.dumps(summary)
            
            # Truncate summary
            summary = str(summary)[:200]
            
            # Date handling
            date_str = doc.get("createdAt") or doc.get("updatedAt") or datetime.now().isoformat()
            try:
                # Handle ISO format
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                display_time = dt.strftime("%Y/%m/%d %H:%M")
                timestamp = dt.timestamp()
            except:
                dt = datetime.now()
                display_time = dt.strftime("%Y/%m/%d %H:%M")
                timestamp = dt.timestamp()

            # Tags handling
            tags = []
            # Check for explicit tags field
            doc_tags = doc.get("tags", [])
            if isinstance(doc_tags, list):
                for t in doc_tags:
                    if isinstance(t, str):
                        tags.append(Tag(label=t, color="blue"))
                    elif isinstance(t, dict) and "name" in t:
                        tags.append(Tag(label=t["name"], color="blue"))

            # Check for regional/domain fields (from user's previous request context)
            if "regional_country" in doc:
                rc = doc["regional_country"]
                if isinstance(rc, list):
                    for c in rc:
                        tags.append(Tag(label=str(c), color="red"))
                elif isinstance(rc, str):
                    tags.append(Tag(label=rc, color="red"))
            
            if "domain" in doc:
                dm = doc["domain"]
                if isinstance(dm, list):
                    for d in dm:
                        tags.append(Tag(label=str(d), color="blue"))
                elif isinstance(dm, str):
                    tags.append(Tag(label=dm, color="blue"))

            return IntelItem(
                id=str(doc.get("id", uuid.uuid4())),
                title=str(title),
                summary=str(summary),
                source="PayloadCMS",
                url=f"{self.cms_url}/admin/collections/{self.collection_slug}/{doc.get('id')}",
                time=display_time,
                timestamp=timestamp,
                tags=tags,
                favorited=False,
                is_hot=True # Mark as hot for the "Today's Hotspot" tab
            )
        except Exception as e:
            self.logger.error(f"Error mapping doc to item: {e}")
            return None

# Global instance
payload_poller = PayloadPoller()
