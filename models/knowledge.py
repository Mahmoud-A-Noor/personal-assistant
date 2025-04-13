from typing import List, Optional, Union
from pydantic import BaseModel, field_validator, Field
from typing_extensions import Literal
from models.metadata import KnowledgeMetadata
from datetime import datetime
import uuid


class KnowledgeItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    content_hash: str  # Used for duplicate detection
    embedding: List[float]
    metadata: KnowledgeMetadata = Field(
        default_factory=KnowledgeMetadata,
        description="Structured metadata about this knowledge item"
    )


class KnowledgeToolInput(BaseModel):
    """Input model for knowledge search operations"""
    query: str = Field(..., description="Search query string")
    limit: int = Field(3, description="Maximum number of results to return")


class KnowledgeUpdateInput(BaseModel):
    """Input model for adding/updating knowledge items"""
    title: str = Field(..., description="Title of the knowledge item")
    content: str = Field(..., description="Detailed content of the knowledge item")
    source: Optional[Literal["conversation", "manual", "web", "other"]] = Field(
        None, description="Source of the knowledge")
    importance: Optional[int] = Field(
        None, description="Importance level (1-10)", ge=1, le=10)
    related_topics: Optional[List[str]] = Field(
        None, description="List of related topics")
    references: Optional[List[str]] = Field(
        None, description="List of reference URLs or citations")
    language: Optional[str] = Field(
        "en", description="Language code (default: 'en')")

    def to_metadata(self) -> KnowledgeMetadata:
        """Convert input to KnowledgeMetadata"""
        return KnowledgeMetadata(
            source=self.source,
            importance=self.importance,
            related_topics=self.related_topics or [],
            references=self.references or [],
            language=self.language,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


class MetadataQueryInput(BaseModel):
    """Input model for querying by metadata fields"""
    field: Literal["importance", "related_topics", "references", "language", "tags", "source"] = Field(
        ..., description="Metadata field to query")
    value: Union[int, List[str], str] = Field(
        ..., description="Value to match against the field")
    limit: int = Field(10, description="Maximum number of results to return")


class MetadataUpdateInput(BaseModel):
    """Input model for updating metadata fields"""
    id: Optional[str] = Field(
        None, description="ID of the knowledge item to update")
    query: Optional[str] = Field(
        None, description="Search query to find item to update")
    field: Literal["importance", "related_topics", "references", "language", "tags"] = Field(
        ..., description="Metadata field to update")
    value: Union[int, List[str], str] = Field(
        ..., description="New value for the field")

    @field_validator('id', 'query')
    def validate_id_or_query(cls, v, values):
        """Ensure either ID or query is provided"""
        if not v and not values.get('query'):
            raise ValueError('Either id or query must be provided')
        return v


class BatchMetadataUpdateInput(BaseModel):
    """Input model for batch metadata updates"""
    updates: List[MetadataUpdateInput] = Field(
        ..., description="List of metadata updates to apply")

    @field_validator('updates')
    def validate_unique_ids(cls, v):
        """Ensure batch updates have unique IDs"""
        ids = [update.id for update in v if update.id]
        if len(ids) != len(set(ids)):
            raise ValueError('Batch updates must have unique IDs')
        return v


class BatchKnowledgeUpdateInput(BaseModel):
    """Input model for batch knowledge updates"""
    items: List[KnowledgeUpdateInput] = Field(
        ..., description="List of knowledge items to update")

    @field_validator('items')
    def validate_items(cls, v):
        """Ensure at least one item is provided"""
        if not v:
            raise ValueError('Batch must contain at least one item')
        return v
