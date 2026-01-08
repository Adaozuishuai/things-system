import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models import AgentSearchRequest, TaskStatusResponse
from app.agent.orchestrator import orchestrator

router = APIRouter()

@router.post("/run")
async def run_agent(req: AgentSearchRequest):
    task_id = orchestrator.create_task(req)
    return {"task_id": task_id}

@router.get("/stream/global")
async def stream_global(request: Request, after_ts: float | None = None, after_id: str | None = None):
    print("Agent Router: Received global stream request")
    last_event_id = request.headers.get("last-event-id") or request.headers.get("Last-Event-ID")
    if not after_id and last_event_id:
        after_id = str(last_event_id)
    return StreamingResponse(
        orchestrator.run_global_stream(after_ts=after_ts, after_id=after_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Disable Nginx buffering if any
        }
    )

@router.get("/stream/{task_id}")
async def stream_agent(task_id: str):
    return StreamingResponse(
        orchestrator.run_stream(task_id),
        media_type="text/event-stream"
    )

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    task = orchestrator.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "result": task["result"]
    }


class DebugBroadcastRequest(BaseModel):
    event: str
    data: Dict[str, Any]


@router.post("/debug/broadcast")
async def debug_broadcast(req: DebugBroadcastRequest):
    enabled = os.getenv("ENABLE_DEBUG_ENDPOINTS", "").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        raise HTTPException(status_code=404, detail="Not found")
    await orchestrator.broadcast(req.event, req.data)
    return {"ok": True}
