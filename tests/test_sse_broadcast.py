import asyncio
import json
import os
import sys
from typing import Optional


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agent.orchestrator import AgentOrchestrator


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
        if msg.startswith(f"event: {event_name}\n"):
            return msg


async def test_broadcast_new_intel():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()
    orchestrator.global_cache.append(
        {
            "id": "seed-1",
            "title": "seed",
            "summary": "seed",
            "timestamp": 0,
            "tags": [],
            "favorited": False,
            "is_hot": True,
        }
    )

    agen = orchestrator.run_global_stream()

    initial = await asyncio.wait_for(agen.__anext__(), timeout=2.0)
    if not initial.startswith("event: initial_batch"):
        raise AssertionError(f"unexpected first message: {initial[:80]!r}")

    payload = {
        "id": "test-1",
        "title": "t",
        "summary": "s",
        "timestamp": 0,
        "tags": [],
        "favorited": False,
        "is_hot": True,
    }

    await orchestrator.broadcast("new_intel", payload)

    msg = await _read_until_event(agen, "new_intel", timeout_s=2.0)
    if not msg:
        raise AssertionError("did not receive new_intel event")

    parts = msg.split("\n")
    data_line = next((p for p in parts if p.startswith("data: ")), None)
    if not data_line:
        raise AssertionError("missing data line in SSE message")

    data = json.loads(data_line[len("data: ") :])
    if data.get("id") != "test-1":
        raise AssertionError(f"unexpected payload id: {data.get('id')!r}")

    await agen.aclose()


async def test_broadcast_five_messages():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()
    orchestrator.global_cache.append(
        {
            "id": "seed-1",
            "title": "seed",
            "summary": "seed",
            "timestamp": 0,
            "tags": [],
            "favorited": False,
            "is_hot": True,
        }
    )

    agen = orchestrator.run_global_stream()

    initial = await asyncio.wait_for(agen.__anext__(), timeout=2.0)
    if not initial.startswith("event: initial_batch"):
        raise AssertionError(f"unexpected first message: {initial[:80]!r}")

    payloads = []
    for i in range(5):
        payload = {
            "id": f"multi-{i+1}",
            "title": f"t-{i+1}",
            "summary": f"s-{i+1}",
            "timestamp": i + 1,
            "tags": [],
            "favorited": False,
            "is_hot": True,
        }
        payloads.append(payload)
        await orchestrator.broadcast("new_intel", payload)

    received_ids = []
    for _ in range(5):
        msg = await _read_until_event(agen, "new_intel", timeout_s=2.0)
        if not msg:
            raise AssertionError("did not receive expected new_intel event")

        parts = msg.split("\n")
        data_line = next((p for p in parts if p.startswith("data: ")), None)
        if not data_line:
            raise AssertionError("missing data line in SSE message")

        data = json.loads(data_line[len("data: ") :])
        received_ids.append(data.get("id"))

    expected_ids = [p["id"] for p in payloads]
    if received_ids != expected_ids:
        raise AssertionError(f"unexpected payload order: {received_ids!r}, expected {expected_ids!r}")

    await agen.aclose()


if __name__ == "__main__":
    asyncio.run(test_broadcast_new_intel())
    asyncio.run(test_broadcast_five_messages())
