from sqlalchemy.orm import Session
from . import db_models
from .models import IntelItem, Tag
import json
from datetime import datetime
from sqlalchemy import or_
from typing import List, Optional

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
    # 转换 Pydantic 模型到数据库模型
    tags_list = [t.label for t in item.tags]
    
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
        favorited=item.favorited
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

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
    # History 默认为所有记录 (History is implied as all)

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
    
    # 排序：按时间戳倒序 (Sort by timestamp desc)
    query = query.order_by(db_models.IntelItemDB.timestamp.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    # 将数据库模型转换为 Pydantic 模型以供响应
    pydantic_items = []
    for item in items:
        tags = [Tag(label=t, color="blue") for t in item.tags] if item.tags else []
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
        tags = [Tag(label=t, color="blue") for t in item.tags] if item.tags else []
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
        tags = [Tag(label=t, color="blue") for t in item.tags] if item.tags else []
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
    return pydantic_items

def clear_intel_items(db: Session):
    """
    清空所有情报数据 (慎用)。
    """
    db.query(db_models.IntelItemDB).delete()
    db.commit()
