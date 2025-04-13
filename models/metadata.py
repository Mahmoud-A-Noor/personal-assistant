from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class KnowledgeMetadata(BaseModel):
    """Metadata associated with knowledge items"""
    
    source: Literal["conversation", "manual", "web", "file", "other"] = Field(
        default="conversation",
        description="Source of the knowledge item"
    )
    version_history: List[str] = Field(
        default_factory=list,
        description="List of previous versions of this knowledge"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="When this knowledge was last updated"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this knowledge (0-1)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with this knowledge"
    )
    importance: Optional[int] = Field(
        None,
        description="Importance level (1-10)",
        ge=1,
        le=10
    )
    related_topics: Optional[List[str]] = Field(
        None,
        description="List of related topics"
    )
    references: Optional[List[str]] = Field(
        None,
        description="List of reference URLs or citations"
    )
    language: Optional[str] = Field(
        "en",
        description="Language code (default: 'en')"
    )
