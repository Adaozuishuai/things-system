from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Literal
from starlette.responses import StreamingResponse
from app.agent.orchestrator import orchestrator
import asyncio
import uuid
import json

router = APIRouter()

class AgentRunRequest(BaseModel):
    query: str
    type: Literal["hot", "history", "all"] = "hot"
    range: Literal["all", "3h", "6h", "12h"] = "all"

@router.post("/run")
async def run_agent(req: AgentRunRequest):
    task_id = str(uuid.uuid4())
    return {"task_id": task_id}

@router.get("/stream/global")
async def stream_global(request: Request, after_ts: float = 0, after_id: Optional[str] = None):
    async def gen():
        async for chunk in orchestrator.run_global_stream(after_ts=after_ts, after_id=after_id):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/stream/{task_id}")
async def stream_task(task_id: str, request: Request):
    async def gen():
        yield f"event: progress\ndata: {json.dumps({'step': 'init', 'message': 'Initializing...'})}\n\n"
        await asyncio.sleep(0.5)
        if await request.is_disconnected():
            return
        yield f"event: progress\ndata: {json.dumps({'step': 'search', 'message': 'Searching...'})}\n\n"
        await asyncio.sleep(0.5)
        if await request.is_disconnected():
            return
        yield f"event: done\ndata: {json.dumps({'answer': 'Dummy answer'})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
