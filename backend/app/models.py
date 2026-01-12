from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
import uuid
import hashlib

class Tag(BaseModel):
    label: str
    color: Literal["purple", "blue", "gray", "red"]


class IntelItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    url: Optional[str] = None
    time: str  # Display string like "2025/8/30 12:30"
    timestamp: float # For sorting
    tags: List[Tag]
    favorited: bool = False
    is_hot: bool = False # Internal flag for mock data separation
    content: Optional[str] = None # Full translated content
    thing_id: Optional[str] = None # CMS thingId

    @staticmethod
    def _stable_id_from_value(value: Optional[Any], fallback: Optional[str] = None) -> str:
        if value is None or value == "":
            if fallback:
                return fallback
            return str(uuid.uuid4())
        if isinstance(value, (int, float)):
            return str(int(value))
        s = str(value)
        if s.isdigit():
            return s
        digest = hashlib.sha1(s.encode("utf-8")).hexdigest()
        return digest

    @staticmethod
    def _parse_publish_datetime(value: Optional[Any]) -> datetime:
        if not value:
            return datetime.now()
        if isinstance(value, datetime):
            return value
        s = str(value).strip()
        if not s:
            return datetime.now()
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return datetime.now()

    @staticmethod
    def create_tags(regional_country: Optional[List[str]] = None, domain: Optional[List[str]] = None) -> List[Tag]:
        tags = []
        regional_country = regional_country or []
        domain = domain or []
        if regional_country:
            for country in regional_country:
                tags.append(Tag(label=country, color="red"))
        
        if domain:
            for d in domain:
                tags.append(Tag(label=d, color="blue"))
        return tags

    @classmethod
    def from_cms_data(cls, data: Dict[str, Any], current_id: int = 0) -> "IntelItem":
        # Basic Mapping
        title = data.get('title', f"Article {current_id}")
        
        # Summary extraction
        summary = ""
        if 'summary' in data:
            summary = data['summary']
        elif 'original' in data:
            summary = data['original'][:200]
        elif 'content' in data:
            summary = str(data['content'])[:200]
        else:
            summary = "No summary available"
            
        # Extract tags
        regional_country = []
        domain = []
        
        if 'regional_country' in data:
            rc_data = data['regional_country']
            if isinstance(rc_data, list):
                for item in rc_data:
                    if isinstance(item, str):
                        regional_country.append(item)
                    elif isinstance(item, dict) and 'name' in item:
                        regional_country.append(item['name'])
                        
        if 'domain' in data:
            d_data = data['domain']
            if isinstance(d_data, list):
                for item in d_data:
                    if isinstance(item, str):
                        domain.append(item)
                    elif isinstance(item, dict) and 'name' in item:
                        domain.append(item['name'])
                        
        tags = cls.create_tags(regional_country, domain)

        dt = cls._parse_publish_datetime(data.get("publishDate") or data.get("createdAt"))
        thing_id = data.get("thingId") or data.get("thing_id")
        if thing_id:
            stable_id = str(thing_id)
        else:
            url = data.get("url")
            item_id = url or data.get("id") or current_id
            stable_id = cls._stable_id_from_value(item_id)
        
        return cls(
            id=stable_id,
            title=title,
            summary=summary,
            source=data.get('author', 'CMS'),
            url=data.get('url'),
            time=dt.strftime("%Y/%m/%d %H:%M"),
            timestamp=dt.timestamp(),
            tags=tags,
            favorited=False,
            is_hot=True,
            thing_id=str(thing_id) if thing_id else None
        )

class IntelListResponse(BaseModel):
    items: List[IntelItem]
    total: int

class FavoriteToggleRequest(BaseModel):
    intel_id: Optional[str] = None
    favorited: bool

class ExportRequest(BaseModel):
    format: Literal["csv", "json", "docx"] = "docx"
    ids: Optional[List[str]] = None
    type: Optional[Literal["hot", "history", "all"]] = "all"
    q: Optional[str] = None
    range: Optional[Literal["all", "3h", "6h", "12h"]] = "all"

class AgentSearchRequest(BaseModel):
    query: str
    type: Optional[Literal["hot", "history"]] = "hot"
    range: Optional[Literal["all", "3h", "6h", "12h"]] = "all"
    top_k: int = 10

class AgentSearchResponse(BaseModel):
    answer: str
    sources: List[IntelItem] = []

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = {}

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: Literal["submitted", "running", "done", "failed"]
    result: Optional[AgentSearchResponse] = None
