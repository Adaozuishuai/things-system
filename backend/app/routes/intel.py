import io
from datetime import datetime
from urllib.parse import quote
from docx import Document
from fastapi import APIRouter, HTTPException, Response, Depends
from typing import Optional, Literal
from sqlalchemy.orm import Session
from app.models import IntelListResponse, FavoriteToggleRequest, ExportRequest, IntelItem, Tag
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
        cached = orchestrator.get_cached_intel(id)
        if not cached:
            raise HTTPException(status_code=404, detail="Intel item not found")

        tags = []
        for t in cached.get("tags") or []:
            if isinstance(t, dict):
                tags.append(Tag(label=t.get("label", ""), color=t.get("color", "blue")))
            else:
                tags.append(Tag(label=str(t), color="blue"))

        intel_item = IntelItem(
            id=str(cached.get("id", id)),
            title=cached.get("title") or "",
            summary=cached.get("summary") or "",
            source=cached.get("source") or "Hot Stream",
            url=cached.get("url"),
            time=cached.get("time") or "",
            timestamp=float(cached.get("timestamp") or datetime.now().timestamp()),
            tags=tags,
            favorited=bool(cached.get("favorited") or False),
            is_hot=False,
            content=cached.get("content"),
            thing_id=cached.get("thing_id") or cached.get("thingId")
        )

        if not crud.get_intel_by_id(db, intel_item.id):
            crud.create_intel_item(db, intel_item)

        return intel_item
    
    tags = []
    for t in item.tags or []:
        if isinstance(t, dict):
            tags.append(Tag(label=str(t.get("label", "")), color=str(t.get("color", "blue"))))
        else:
            tags.append(Tag(label=str(t), color="blue"))
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
        is_hot=item.is_hot,
        content=item.content,
        thing_id=item.thing_id
    )

@router.post("/{id}/favorite")
async def toggle_favorite(id: str, req: FavoriteToggleRequest, db: Session = Depends(get_db)):
    # Pass req.favorited to crud
    item = crud.toggle_favorite(db, id, req.favorited)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
