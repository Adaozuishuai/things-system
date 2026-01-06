from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import AgentSearchRequest, TaskStatusResponse
from app.agent.orchestrator import orchestrator

router = APIRouter()

@router.post("/run")
async def run_agent(req: AgentSearchRequest):
    task_id = orchestrator.create_task(req)
    return {"task_id": task_id}

@router.get("/stream/global")
async def stream_global():
    print("Agent Router: Received global stream request")
    return StreamingResponse(
        orchestrator.run_global_stream(),
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
