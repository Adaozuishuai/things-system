import io
import uuid
from datetime import datetime
from urllib.parse import quote
from docx import Document
from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from sqlalchemy.orm import Session
from app.models import IntelListResponse, FavoriteToggleRequest, ExportRequest, IntelItem, Tag, KafkaPayload
from app.database import get_db
from app import crud
from app.agent.orchestrator import orchestrator

router = APIRouter()

@router.get("/", response_model=IntelListResponse)
async def get_intel(
    type: Literal["hot", "history", "all"] = "all",
    q: Optional[str] = None,
    range: Literal["all", "24h", "7d", "30d"] = "all",
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    items, total = crud.get_filtered_intel(db, type_filter=type, q=q, range_filter=range, limit=limit, offset=offset)
    return {"items": items, "total": total}

@router.get("/favorites", response_model=IntelListResponse)
async def get_favorites(
    q: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    items, total = crud.get_favorites(db, q=q, limit=limit, offset=offset)
    return {"items": items, "total": total}

@router.post("/export")
async def export_intel(req: ExportRequest, db: Session = Depends(get_db)):
    # Determine items to export
    items = []
    
    if req.ids and len(req.ids) > 0:
        items = crud.get_by_ids(db, req.ids)
    else:
        items, _ = crud.get_filtered_intel(
            db,
            type_filter=req.type or "all",
            q=req.q,
            range_filter=req.range or "all",
            limit=1000
        )
    
    # Generate DOCX
    doc = Document()
    doc.add_heading('Intelligence Export', 0)
    
    for item in items:
        doc.add_heading(item.title, level=1)
        
        # Meta info
        p = doc.add_paragraph()
        p.add_run('ID: ').bold = True
        p.add_run(f"{item.id}\n")
        p.add_run('Time: ').bold = True
        p.add_run(f"{item.time}\n")
        p.add_run('Source: ').bold = True
        p.add_run(f"{item.source}\n")
        p.add_run('Tags: ').bold = True
        tags_str = ", ".join([t.label for t in item.tags])
        p.add_run(f"{tags_str}\n")
        p.add_run('Favorited: ').bold = True
        p.add_run(f"{item.favorited}")
        
        # Summary
        doc.add_heading('Summary', level=2)
        doc.add_paragraph(item.summary)
        
        doc.add_paragraph('_' * 50)
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    
    # Determine filename
    filename = "情报批量导出.docx"
    if len(items) == 1:
        # Remove invalid chars for filename
        safe_title = "".join([c for c in items[0].title if c not in r'\/:*?"<>|'])
        filename = f"{safe_title}.docx"
    
    # Encode filename for header
    encoded_filename = quote(filename)
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )

@router.get("/{id}", response_model=IntelItem)
async def get_intel_detail(id: str, db: Session = Depends(get_db)):
    item = crud.get_intel_by_id(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Intel item not found")
    
    # Convert DB model to Pydantic model, handling tags conversion
    tags = [Tag(label=t, color="blue") for t in item.tags] if item.tags else []
    return IntelItem(
        id=item.id,
        title=item.title,
        summary=item.summary,
        source=item.source,
        url=item.url,
        time=item.publish_time_str,
        timestamp=item.timestamp,
        tags=tags,
        favorited=item.favorited,
        is_hot=item.is_hot
    )

@router.post("/ingest")
async def ingest_kafka_payload(payload: KafkaPayload):
    """
    Ingest data from Kafka payload directly without DB storage.
    Broadcasts to connected clients via SSE.
    """
    # Adapt Payload to IntelItem
    tags = []
    
    # 1. Regional Country -> Red Tag
    if payload.regional_country:
        for country in payload.regional_country:
            tags.append(Tag(label=country, color="red"))
            
    # 2. Domain -> Blue Tag
    if payload.domain:
        for domain in payload.domain:
            tags.append(Tag(label=domain, color="blue"))
            
    # Create IntelItem
    # Use current time if publishDate is not parsable or just use it as string
    # Assuming publishDate is a string we can just display
    
    item = IntelItem(
        id=str(uuid.uuid4()),
        title=payload.title,
        summary=payload.summary or payload.original[:200], # Use original as fallback summary
        source=payload.author or "API Stream",
        url=payload.url,
        time=payload.publishDate,
        timestamp=datetime.now().timestamp(),
        tags=tags,
        favorited=False,
        is_hot=False
    )
    
    # Broadcast to global stream
    await orchestrator.broadcast("new_intel", item.model_dump())
    
    return {"status": "broadcasted", "item_id": item.id}

@router.post("/{id}/favorite")
async def toggle_favorite(id: str, req: FavoriteToggleRequest, db: Session = Depends(get_db)):
    # Pass req.favorited to crud
    item = crud.toggle_favorite(db, id, req.favorited)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

class PollerConfig(BaseModel):
    base_url: str
    start_id: int = 6617
    interval: int = 5

@router.post("/poller/start")
async def start_poller(config: PollerConfig):
    from app.services.poller import article_poller
    article_poller.configure(config.base_url, config.start_id, config.interval)
    await article_poller.start()
    return {"status": "started", "config": config}

@router.post("/poller/stop")
async def stop_poller():
    from app.services.poller import article_poller
    await article_poller.stop()
    return {"status": "stopped"}

@router.get("/poller/status")
async def get_poller_status():
    from app.services.poller import article_poller
    return {
        "running": article_poller.is_running,
        "current_id": article_poller.current_id,
        "base_url": article_poller.base_url
    }

class PayloadPollerConfig(BaseModel):
    cms_url: str
    collection_slug: str
    email: str
    password: str
    user_collection: str = "users"
    interval: int = 10

@router.post("/payload/start")
async def start_payload_poller(config: PayloadPollerConfig):
    from app.services.payload_poller import payload_poller
    payload_poller.configure(
        cms_url=config.cms_url,
        collection_slug=config.collection_slug,
        email=config.email,
        password=config.password,
        user_collection=config.user_collection,
        interval=config.interval
    )
    await payload_poller.start()
    return {"status": "started", "config": config.model_dump(exclude={'password'})}

@router.post("/payload/stop")
async def stop_payload_poller():
    from app.services.payload_poller import payload_poller
    await payload_poller.stop()
    return {"status": "stopped"}

@router.get("/payload/status")
async def get_payload_poller_status():
    from app.services.payload_poller import payload_poller
    return {
        "running": payload_poller.is_running,
        "cms_url": payload_poller.cms_url,
        "collection": payload_poller.collection_slug
    }
