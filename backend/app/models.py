from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
import uuid

class Tag(BaseModel):
    label: str
    color: Literal["purple", "blue", "gray", "red"]

class KafkaPayload(BaseModel):
    id: Optional[int] = None
    no: Optional[str] = None
    title: str
    thingId: Optional[str] = None
    publishDate: str
    author: Optional[str] = None
    summary: Optional[str] = None
    original: str
    translation: Optional[str] = None
    url: Optional[str] = None
    regional_country: Optional[List[str]] = []
    domain: Optional[List[str]] = []


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
    def from_kafka_payload(cls, payload: KafkaPayload) -> "IntelItem":
        tags = cls.create_tags(payload.regional_country, payload.domain)
        
        return cls(
            id=str(uuid.uuid4()),
            title=payload.title,
            summary=payload.summary or payload.original[:200],
            source=payload.author or "API Stream",
            url=payload.url,
            time=payload.publishDate,
            timestamp=datetime.now().timestamp(),
            tags=tags,
            favorited=False,
            is_hot=False
        )

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
        
        # Time handling
        publish_date = data.get('publishDate', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            source=data.get('author', 'CMS Poller'),
            url=data.get('url'),
            time=publish_date,
            timestamp=datetime.now().timestamp(),
            tags=tags,
            favorited=False,
            is_hot=True
        )

class IntelListResponse(BaseModel):
    items: List[IntelItem]
    total: int

class FavoriteToggleRequest(BaseModel):
    favorited: bool

class ExportRequest(BaseModel):
    ids: Optional[List[str]] = None
    type: Optional[Literal["hot", "history", "all"]] = "all"
    q: Optional[str] = None
    range: Optional[Literal["all", "24h", "7d", "30d"]] = "all"

class AgentSearchRequest(BaseModel):
    query: str
    type: Optional[Literal["hot", "history"]] = "hot"
    range: Optional[Literal["all", "24h", "7d", "30d"]] = "all"
    top_k: int = 10

class AgentSearchResponse(BaseModel):
    items: List[IntelItem]
    answer: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: Literal["submitted", "running", "done", "failed"]
    result: Optional[AgentSearchResponse] = None
