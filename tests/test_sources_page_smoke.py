import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agent.orchestrator import AgentOrchestrator


TWO_PART_PUBLIC_SUFFIXES = {
    "co.jp",
    "or.jp",
    "ne.jp",
    "ac.jp",
    "go.jp",
    "co.uk",
    "com.cn",
    "net.cn",
    "org.cn",
    "gov.cn",
    "com.hk",
    "com.tw",
    "com.au",
}


def get_registrable_domain(hostname: str) -> str:
    host = hostname.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return host
    last2 = ".".join(parts[-2:])
    if last2 in TWO_PART_PUBLIC_SUFFIXES and len(parts) >= 3:
        return ".".join(parts[-3:])
    return last2


def apply_sources_registry(
    registry: Dict[str, dict],
    seen_ids: set,
    incoming: List[dict],
) -> Tuple[Dict[str, dict], set]:
    next_registry = dict(registry)
    next_seen = set(seen_ids)

    for item in incoming:
        item_id = item.get("id")
        if not item_id:
            continue
        if item_id in next_seen:
            continue
        next_seen.add(item_id)

        raw_url = item.get("url")
        if not raw_url:
            continue
        try:
            parsed = urlparse(raw_url)
        except Exception:
            continue
        if not parsed.hostname:
            continue

        host = parsed.hostname.lower()
        if host.startswith("www."):
            host = host[4:]
        domain = get_registrable_domain(host)

        current = next_registry.get(domain)
        if not current:
            next_registry[domain] = {
                "domain": domain,
                "host": host,
                "origin": f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "",
                "items": [item],
            }
            continue

        if any(x.get("id") == item_id for x in current.get("items", [])):
            continue

        next_registry[domain] = {
            **current,
            "host": current.get("host") or host,
            "origin": current.get("origin") or (f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""),
            "items": [item, *current.get("items", [])],
        }

    return next_registry, next_seen


def group_sources(items: List[dict]) -> Dict[str, List[dict]]:
    by_domain: Dict[str, List[dict]] = {}
    for item in items:
        raw_url = item.get("url")
        if not raw_url:
            continue
        try:
            parsed = urlparse(raw_url)
        except Exception:
            continue
        if not parsed.hostname:
            continue
        domain = get_registrable_domain(parsed.hostname)
        by_domain.setdefault(domain, []).append(item)
    for domain, domain_items in by_domain.items():
        by_domain[domain] = sorted(domain_items, key=lambda x: float(x.get("timestamp") or 0), reverse=True)
    return by_domain


def paginate(items: List[dict], page: int, page_size: int = 10) -> List[dict]:
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    return items[start : start + page_size]


async def _read_until_event(agen, event_name: str, timeout_s: float) -> Optional[str]:
    end_at = asyncio.get_event_loop().time() + timeout_s
    while True:
        remaining = end_at - asyncio.get_event_loop().time()
        if remaining <= 0:
            return None
        try:
            msg = await asyncio.wait_for(agen.__anext__(), timeout=remaining)
        except asyncio.TimeoutError:
            return None
        if f"\nevent: {event_name}\n" in f"\n{msg}":
            return msg


def _extract_sse_data_json(msg: str):
    parts = msg.split("\n")
    data_line = next((p for p in parts if p.startswith("data: ")), None)
    if not data_line:
        raise AssertionError("missing data line in SSE message")
    return json.loads(data_line[len("data: ") :])


async def test_sources_page_like_grouping_and_realtime_stream():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()
    orchestrator.global_cache.append(
        {
            "id": "seed-1",
            "title": "seed",
            "summary": "seed",
            "timestamp": 1,
            "tags": [],
            "favorited": False,
            "is_hot": True,
            "url": "https://www.bbc.co.uk/news/world-00000000",
        }
    )

    agen = orchestrator.run_global_stream()

    initial_msg = await _read_until_event(agen, "initial_batch", timeout_s=2.0)
    if not initial_msg:
        raise AssertionError("did not receive initial_batch event")
    initial_items = _extract_sse_data_json(initial_msg)
    if not isinstance(initial_items, list) or not initial_items:
        raise AssertionError("initial_batch payload is empty or not a list")

    registry: Dict[str, dict] = {}
    seen_ids: set = set()
    registry, seen_ids = apply_sources_registry(registry, seen_ids, initial_items)
    if "bbc.co.uk" not in registry:
        raise AssertionError("expected bbc.co.uk to be created from initial_batch")
    if len(registry["bbc.co.uk"]["items"]) != 1:
        raise AssertionError("expected bbc.co.uk to have 1 item from initial_batch")

    await orchestrator.broadcast(
        "new_intel",
        {
            "id": "rt-1",
            "title": "realtime",
            "summary": "realtime",
            "timestamp": 2,
            "tags": [],
            "favorited": False,
            "is_hot": True,
            "url": "https://www.reuters.com/world/test",
        },
    )

    new_msg = await _read_until_event(agen, "new_intel", timeout_s=2.0)
    if not new_msg:
        raise AssertionError("did not receive new_intel event")
    new_item = _extract_sse_data_json(new_msg)
    if new_item.get("id") != "rt-1":
        raise AssertionError(f"unexpected new_intel payload id: {new_item.get('id')!r}")

    registry, seen_ids = apply_sources_registry(registry, seen_ids, [new_item])
    if "reuters.com" not in registry:
        raise AssertionError("expected reuters.com to be created from realtime push")
    if len(registry["reuters.com"]["items"]) != 1:
        raise AssertionError("expected reuters.com to have 1 item after first push")

    grouped = group_sources(initial_items + [new_item])
    if "bbc.co.uk" not in grouped:
        raise AssertionError("expected bbc.co.uk group missing")
    if "reuters.com" not in grouped:
        raise AssertionError("expected reuters.com group missing")
    if len(grouped["bbc.co.uk"]) != 1 or len(grouped["reuters.com"]) != 1:
        raise AssertionError("unexpected group counts after new_intel")

    await orchestrator.broadcast(
        "new_intel",
        {
            "id": "rt-2",
            "title": "realtime2",
            "summary": "realtime2",
            "timestamp": 3,
            "tags": [],
            "favorited": False,
            "is_hot": True,
            "url": "https://www.reuters.com/world/test2",
        },
    )
    new2_msg = await _read_until_event(agen, "new_intel", timeout_s=2.0)
    if not new2_msg:
        raise AssertionError("did not receive second new_intel event")
    new_item2 = _extract_sse_data_json(new2_msg)

    registry, seen_ids = apply_sources_registry(registry, seen_ids, [new_item2])
    if len(registry["reuters.com"]["items"]) != 2:
        raise AssertionError("expected reuters.com to accumulate 2 items after second push")

    registry_before = dict(registry)
    seen_before = set(seen_ids)
    registry, seen_ids = apply_sources_registry(
        registry,
        seen_ids,
        [
            {
                "id": "rt-2",
                "title": "dup",
                "timestamp": 3,
                "url": "https://www.reuters.com/world/test2",
            }
        ],
    )
    if registry != registry_before or seen_ids != seen_before:
        raise AssertionError("duplicate id should not change registry")

    registry_before = dict(registry)
    seen_before = set(seen_ids)
    registry, seen_ids = apply_sources_registry(registry, seen_ids, [{"id": "no-url-1", "timestamp": 4, "url": None}])
    if registry != registry_before or seen_ids == seen_before:
        raise AssertionError("no-url item should be seen but not added to any source")

    grouped2 = group_sources(initial_items + [new_item, new_item2])
    if len(grouped2.get("reuters.com", [])) != 2:
        raise AssertionError("expected reuters.com group to have 2 items")

    await agen.aclose()


def test_sources_page_like_pagination():
    items = []
    for i in range(11):
        items.append(
            {
                "id": f"p-{i+1}",
                "timestamp": i + 1,
                "url": "https://example.com/a",
            }
        )

    grouped = group_sources(items)
    domain_items = grouped.get("example.com")
    if not domain_items:
        raise AssertionError("expected example.com group missing")
    p1 = paginate(domain_items, page=1, page_size=10)
    p2 = paginate(domain_items, page=2, page_size=10)
    if len(p1) != 10:
        raise AssertionError(f"unexpected page1 size: {len(p1)}")
    if len(p2) != 1:
        raise AssertionError(f"unexpected page2 size: {len(p2)}")


if __name__ == "__main__":
    asyncio.run(test_sources_page_like_grouping_and_realtime_stream())
    test_sources_page_like_pagination()
