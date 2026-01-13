import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.global_cache: List[Dict[str, Any]] = []
        self.listeners: List[asyncio.Queue] = []
        self.lock = asyncio.Lock()

    @staticmethod
    def _strip_content_for_sse(data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "content" not in data:
            return data
        copied = dict(data)
        copied.pop("content", None)
        return copied

    async def broadcast(self, event: str, data: Any):
        out_data = data
        if event == "new_intel":
            out_data = self._strip_content_for_sse(data)
        msg = f"event: {event}\ndata: {json.dumps(out_data, ensure_ascii=False)}\n\n"
        
        if event == "new_intel":
            async with self.lock:
                self.global_cache.append(data)
                if len(self.global_cache) > 1000:
                    self.global_cache = self.global_cache[-1000:]

        to_remove = []
        for q in self.listeners:
            try:
                await q.put(msg)
            except Exception:
                to_remove.append(q)
        
        for q in to_remove:
            if q in self.listeners:
                self.listeners.remove(q)

    async def run_global_stream(self, after_ts: float = 0, after_id: Optional[str] = None):
        logger.info(f"New stream connection: after_ts={after_ts}, after_id={after_id}")
        q = asyncio.Queue()
        self.listeners.append(q)
        heartbeat_seconds = 25.0
        
        async with self.lock:
            cache = list(self.global_cache)
            logger.info(f"Stream initialized with {len(cache)} cached items")

        start_index = 0
        if after_id:
            for i, item in enumerate(cache):
                if item.get("id") == after_id:
                    start_index = i + 1
                    break

        initial_items: List[Dict[str, Any]] = []
        if after_ts and after_id:
            for item in cache[start_index:]:
                ts = item.get("timestamp") or 0
                if ts >= after_ts:
                    initial_items.append(item)
        elif after_ts:
            for item in cache:
                ts = item.get("timestamp") or 0
                if ts > after_ts:
                    initial_items.append(item)
        elif after_id:
            initial_items = cache[start_index:]
        else:
            initial_items = cache

        chunk_size = 50
        for i in range(0, len(initial_items), chunk_size):
            chunk = [self._strip_content_for_sse(x) for x in initial_items[i : i + chunk_size]]
            yield f"event: initial_batch\ndata: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=heartbeat_seconds)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in self.listeners:
                self.listeners.remove(q)

    def get_cached_intel(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.global_cache:
            if item.get("id") == item_id:
                return item
        return None

    async def analyze_data_file(self):
        logger.info("Backfilling hot intel cache from database...")
        try:
            from app.database import SessionLocal
            from app import crud
        except Exception as e:
            logger.error(f"Failed to import DB dependencies for backfill: {e}")
            return

        def _do_backfill():
            db = SessionLocal()
            try:
                items, _total = crud.get_filtered_intel(db, type_filter="hot", q=None, range_filter="all", limit=200, offset=0)
                return list(reversed(items))
            finally:
                db.close()

        try:
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(None, _do_backfill)

            async with self.lock:
                self.global_cache = [x.model_dump() for x in items]
                if len(self.global_cache) > 1000:
                    self.global_cache = self.global_cache[-1000:]

            logger.info(f"Backfilled {len(items)} hot items into SSE cache")
        except Exception as e:
            logger.error(f"Backfill failed: {e}")

orchestrator = AgentOrchestrator()
