import asyncio
import json
import os
import sys
from typing import Optional


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

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
        if f"\nevent: {event_name}\n" in f"\n{msg}":
            return msg


def _extract_data_json(msg: str):
    parts = msg.split("\n")
    data_line = next((p for p in parts if p.startswith("data: ")), None)
    if not data_line:
        raise AssertionError("missing data line in SSE message")
    return json.loads(data_line[len("data: ") :])


async def test_resume_filters_by_after_id():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()

    orchestrator.global_cache.append({"id": "a", "timestamp": 1, "title": "a", "summary": "a", "tags": [], "favorited": False, "is_hot": True})
    orchestrator.global_cache.append({"id": "b", "timestamp": 2, "title": "b", "summary": "b", "tags": [], "favorited": False, "is_hot": True})
    orchestrator.global_cache.append({"id": "c", "timestamp": 3, "title": "c", "summary": "c", "tags": [], "favorited": False, "is_hot": True})

    agen = orchestrator.run_global_stream(after_id="b")
    initial = await _read_until_event(agen, "initial_batch", timeout_s=2.0)
    if not initial:
        raise AssertionError("did not receive initial_batch event")

    data = _extract_data_json(initial)
    ids = [x.get("id") for x in data]
    if ids != ["c"]:
        raise AssertionError(f"unexpected ids for after_id=b: {ids!r}")

    await agen.aclose()


async def test_resume_filters_by_after_ts_and_after_id():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()

    orchestrator.global_cache.append({"id": "a", "timestamp": 1, "title": "a", "summary": "a", "tags": [], "favorited": False, "is_hot": True})
    orchestrator.global_cache.append({"id": "b", "timestamp": 2, "title": "b", "summary": "b", "tags": [], "favorited": False, "is_hot": True})
    orchestrator.global_cache.append({"id": "c", "timestamp": 2, "title": "c", "summary": "c", "tags": [], "favorited": False, "is_hot": True})
    orchestrator.global_cache.append({"id": "d", "timestamp": 3, "title": "d", "summary": "d", "tags": [], "favorited": False, "is_hot": True})

    agen = orchestrator.run_global_stream(after_ts=2, after_id="b")
    initial = await _read_until_event(agen, "initial_batch", timeout_s=2.0)
    if not initial:
        raise AssertionError("did not receive initial_batch event")

    data = _extract_data_json(initial)
    ids = [x.get("id") for x in data]
    if ids != ["c", "d"]:
        raise AssertionError(f"unexpected ids for after_ts=2 after_id=b: {ids!r}")

    await agen.aclose()

async def test_disconnect_and_resume_does_not_repeat_messages():
    orchestrator = AgentOrchestrator()
    orchestrator.global_cache.clear()
    orchestrator.global_cache.append({"id": "seed", "timestamp": 0, "title": "seed", "summary": "seed", "tags": [], "favorited": False, "is_hot": True})

    agen1 = orchestrator.run_global_stream()
    initial1 = await _read_until_event(agen1, "initial_batch", timeout_s=2.0)
    if not initial1:
        raise AssertionError("did not receive initial_batch for first connection")

    payloads = [
        {"id": "m1", "timestamp": 1, "title": "m1", "summary": "m1", "tags": [], "favorited": False, "is_hot": True},
        {"id": "m2", "timestamp": 2, "title": "m2", "summary": "m2", "tags": [], "favorited": False, "is_hot": True},
        {"id": "m3", "timestamp": 3, "title": "m3", "summary": "m3", "tags": [], "favorited": False, "is_hot": True},
    ]

    for p in payloads:
        await orchestrator.broadcast("new_intel", p)

    msg1 = await _read_until_event(agen1, "new_intel", timeout_s=2.0)
    msg2 = await _read_until_event(agen1, "new_intel", timeout_s=2.0)
    if not msg1 or not msg2:
        raise AssertionError("did not receive expected new_intel events before disconnect")

    received1 = _extract_data_json(msg1).get("id")
    received2 = _extract_data_json(msg2).get("id")
    if [received1, received2] != ["m1", "m2"]:
        raise AssertionError(f"unexpected received order before disconnect: {[received1, received2]!r}")

    await agen1.aclose()

    agen2 = orchestrator.run_global_stream(after_id="m2")
    initial2 = await _read_until_event(agen2, "initial_batch", timeout_s=2.0)
    if not initial2:
        raise AssertionError("did not receive initial_batch for resumed connection")

    data2 = _extract_data_json(initial2)
    ids2 = [x.get("id") for x in data2]
    if ids2 != ["m3"]:
        raise AssertionError(f"unexpected resumed initial_batch ids: {ids2!r}")

    payload4 = {"id": "m4", "timestamp": 4, "title": "m4", "summary": "m4", "tags": [], "favorited": False, "is_hot": True}
    await orchestrator.broadcast("new_intel", payload4)

    msg4 = await _read_until_event(agen2, "new_intel", timeout_s=2.0)
    if not msg4:
        raise AssertionError("did not receive new_intel after resuming")
    if _extract_data_json(msg4).get("id") != "m4":
        raise AssertionError("unexpected new_intel payload after resuming")

    await agen2.aclose()


if __name__ == "__main__":
    asyncio.run(test_resume_filters_by_after_id())
    asyncio.run(test_resume_filters_by_after_ts_and_after_id())
    asyncio.run(test_disconnect_and_resume_does_not_repeat_messages())
