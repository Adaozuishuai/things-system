from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
import uuid

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
    def create_tags(regional_country: List[str] = [], domain: List[str] = []) -> List[Tag]:
        tags = []
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
        
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            source=data.get('author', 'CMS'),
            url=data.get('url'),
            time=data.get('publishDate', datetime.now().strftime("%Y/%m/%d %H:%M")),
            timestamp=datetime.now().timestamp(),
            tags=tags,
            favorited=False,
            is_hot=True
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
