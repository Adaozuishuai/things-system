from sqlalchemy.orm import Session
from . import db_models
from .models import IntelItem, Tag
import json
from datetime import datetime
from sqlalchemy import or_
from typing import List, Optional

def _deserialize_tags(raw_tags) -> List[Tag]:
    if not raw_tags:
        return []
    tags: List[Tag] = []
    for t in raw_tags:
        if isinstance(t, dict):
            tags.append(Tag(label=str(t.get("label", "")), color=str(t.get("color", "blue"))))
        else:
            tags.append(Tag(label=str(t), color="blue"))
    return tags

def _serialize_tags(tags: List[Tag]):
    return [{"label": t.label, "color": t.color} for t in (tags or [])]

# ===========================
# 原始数据操作 (Raw Data Operations)
# ===========================

def create_raw_data(db: Session, content: str, url: str = None, source: str = "manual"):
    """
    创建一条新的原始数据记录。
    
    参数:
        db: 数据库会话
        content: 原始数据内容
        url: 数据来源 URL (可选)
        source: 数据来源标识 (默认为 "manual")
    """
    db_item = db_models.RawData(content=content, url=url, source=source)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_unprocessed_raw_data(db: Session, limit: int = 1):
    """
    获取未处理的原始数据列表。
    
    参数:
        db: 数据库会话
        limit: 限制返回的条数
    """
    return db.query(db_models.RawData).filter(db_models.RawData.processed == False).limit(limit).all()

def mark_raw_data_processed(db: Session, raw_id: str):
    """
    标记指定的原始数据为已处理状态。
    
    参数:
        db: 数据库会话
        raw_id: 原始数据 ID
    """
    db_item = db.query(db_models.RawData).filter(db_models.RawData.id == raw_id).first()
    if db_item:
        db_item.processed = True
        db.commit()

# ===========================
# 情报数据操作 (Intel Item Operations)
# ===========================

def create_intel_item(db: Session, item: IntelItem):
    """
    创建一条新的情报条目。
    注意：数据库中的 tags 是 JSON 字符串列表，而 IntelItem 中是 Tag 对象列表，需要转换。
    
    参数:
        db: 数据库会话
        item: Pydantic 模型对象 (IntelItem)
    """
    tags_list = _serialize_tags(item.tags)
    db_item = db_models.IntelItemDB(
        id=item.id,
        title=item.title,
        summary=item.summary,
        source=item.source,
        url=item.url,
        publish_time_str=item.time,
        timestamp=item.timestamp,
        tags=tags_list,
        is_hot=item.is_hot,
        favorited=item.favorited,
        content=item.content,
        thing_id=item.thing_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_intel_item(db: Session, item: IntelItem):
    """
    更新现有的情报条目。
    """
    db_item = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == item.id).first()
    if db_item:
        db_item.title = item.title
        db_item.summary = item.summary
        db_item.content = item.content
        db_item.thing_id = item.thing_id
        db_item.tags = _serialize_tags(item.tags)
        # Don't update favorited status to preserve user choice
        # db_item.favorited = item.favorited 
        db.commit()
        db.refresh(db_item)
        return db_item
    return None

def get_intel_by_id(db: Session, item_id: str):
    """
    根据 ID 获取情报详情。
    """
    return db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == item_id).first()

def get_filtered_intel(
    db: Session,
    type_filter: str = "all",
    q: Optional[str] = None,
    range_filter: str = "all",
    limit: int = 20,
    offset: int = 0
):
    """
    获取过滤后的情报列表，支持多种筛选条件。
    
    参数:
        db: 数据库会话
        type_filter: 类型筛选 ("hot", "history", "all")
        q: 搜索关键词 (匹配标题或摘要)
        range_filter: 时间范围筛选 ("all", "24h", "7d", "30d")
        limit: 每页条数
        offset: 分页偏移量
    
    返回:
        (pydantic_items, total): 元组，包含 Pydantic 对象列表和总记录数
    """
    query = db.query(db_models.IntelItemDB)

    # 1. 类型筛选 (Type Filter)
    if type_filter == "hot":
        query = query.filter(db_models.IntelItemDB.is_hot == True)
    elif type_filter == "history":
        query = query.filter(db_models.IntelItemDB.is_hot == False)

    # 2. 关键词搜索 (Search)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                db_models.IntelItemDB.title.ilike(search),
                db_models.IntelItemDB.summary.ilike(search)
            )
        )

    # 3. 时间范围筛选 (Time Range)
    if range_filter != "all":
        now_ts = datetime.now().timestamp()
        if range_filter == "24h":
            cutoff = now_ts - 86400
            query = query.filter(db_models.IntelItemDB.timestamp >= cutoff)
        elif range_filter == "7d":
            cutoff = now_ts - 7 * 86400
            query = query.filter(db_models.IntelItemDB.timestamp >= cutoff)
        elif range_filter == "30d":
            cutoff = now_ts - 30 * 86400
            query = query.filter(db_models.IntelItemDB.timestamp >= cutoff)
    
    if type_filter == "history":
        query = query.order_by(db_models.IntelItemDB.created_at.desc(), db_models.IntelItemDB.timestamp.desc())
    else:
        query = query.order_by(db_models.IntelItemDB.timestamp.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    # 将数据库模型转换为 Pydantic 模型以供响应
    pydantic_items = []
    for item in items:
        tags = _deserialize_tags(item.tags)
        pydantic_items.append(
            IntelItem(
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
        )

    return pydantic_items, total

def get_favorites(db: Session, q: Optional[str] = None, limit: int = 20, offset: int = 0):
    """
    获取收藏的情报列表。
    
    参数:
        db: 数据库会话
        q: 搜索关键词 (可选)
        limit: 每页条数
        offset: 分页偏移量
    """
    query = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.favorited == True)
    
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                db_models.IntelItemDB.title.ilike(search),
                db_models.IntelItemDB.summary.ilike(search)
            )
        )
        
    query = query.order_by(db_models.IntelItemDB.timestamp.desc())
    
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    pydantic_items = []
    for item in items:
        tags = _deserialize_tags(item.tags)
        pydantic_items.append(
            IntelItem(
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
        )
        
    return pydantic_items, total


def toggle_favorite(db: Session, item_id: str, favorited: bool):
    """
    切换或设置情报条目的收藏状态。
    
    参数:
        db: 数据库会话
        item_id: 情报 ID
        favorited: 目标状态 (True/False)
        
    返回:
        更新后的 IntelItem 对象，若未找到则返回 None
    """
    item = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id == item_id).first()
    if item:
        item.favorited = favorited
        db.commit()
        # 返回转换后的 Pydantic 对象
        tags = _deserialize_tags(item.tags)
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
    return None

def get_by_ids(db: Session, ids: List[str]):
    """
    根据 ID 列表批量获取情报条目 (常用于导出功能)。
    
    参数:
        db: 数据库会话
        ids: ID 字符串列表
    """
    items = db.query(db_models.IntelItemDB).filter(db_models.IntelItemDB.id.in_(ids)).all()
    pydantic_items = []
    for item in items:
        tags = _deserialize_tags(item.tags)
        pydantic_items.append(
            IntelItem(
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
        )
    return pydantic_items

def clear_intel_items(db: Session):
    """
    清空所有情报数据 (慎用)。
    """
    db.query(db_models.IntelItemDB).delete()
    db.commit()

def delete_old_intel_items(db: Session, days: int = 30) -> int:
    """
    Delete intel items older than 'days'.
    Returns number of deleted items.
    """
    cutoff_ts = datetime.now().timestamp() - (days * 86400)
    # Don't delete favorites!
    deleted_count = db.query(db_models.IntelItemDB).filter(
        db_models.IntelItemDB.timestamp < cutoff_ts,
        db_models.IntelItemDB.favorited == False
    ).delete()
    db.commit()
    return deleted_count
