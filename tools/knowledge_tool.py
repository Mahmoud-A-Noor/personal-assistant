from typing import List, Optional, Dict, Union
from pydantic import BaseModel, field_validator
from pydantic_ai import Tool
from core.knowledge import KnowledgeBase, KnowledgeMetadata
from typing_extensions import Literal

class KnowledgeToolInput(BaseModel):
    query: str
    limit: int = 3

class KnowledgeUpdateInput(BaseModel):
    title: str
    content: str
    source: Optional[Literal["conversation", "manual", "web", "other"]] = None
    importance: Optional[int] = None
    related_topics: Optional[List[str]] = None
    references: Optional[List[str]] = None
    language: Optional[str] = None
    
    def to_metadata(self) -> KnowledgeMetadata:
        """Convert input to KnowledgeMetadata"""
        return KnowledgeMetadata(
            source=self.source,
            importance=self.importance,
            related_topics=self.related_topics or [],
            references=self.references or [],
            language=self.language or "en"
        )

class MetadataQueryInput(BaseModel):
    field: Literal["importance", "related_topics", "references", "language", "tags", "source"]
    value: Union[int, List[str], str]
    limit: int = 10

class MetadataUpdateInput(BaseModel):
    id: Optional[str] = None
    query: Optional[str] = None
    field: Literal["importance", "related_topics", "references", "language", "tags"]
    value: Union[int, List[str], str]
    
    @field_validator('id', 'query')
    def validate_id_or_query(cls, v, values):
        if not v and not values.get('query'):
            raise ValueError('Either id or query must be provided')
        return v

class BatchMetadataUpdateInput(BaseModel):
    updates: List[MetadataUpdateInput]
    
    @field_validator('updates')
    def validate_unique_ids(cls, v):
        ids = [update.id for update in v if update.id]
        if len(ids) != len(set(ids)):
            raise ValueError('Batch updates must have unique IDs')
        return v

class BatchKnowledgeUpdateInput(BaseModel):
    items: List[KnowledgeUpdateInput]
    
    @field_validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Batch must contain at least one item')
        return v


class KnowledgeTool(Tool):
    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None, max_retries: int = 3):
        self.kb = knowledge_base or KnowledgeBase()
        self.max_retries = 3
        self.name = "Knowledge-Tool-Kit"
        self.description = "A tool kit for managing and searching knowledge base"
        
        
    def search(self, input: KnowledgeToolInput) -> List[dict]:
        """Search knowledge base for relevant information"""
        return self.kb.search_knowledge(input.query, input.limit)
    
    def upsert(self, input: KnowledgeUpdateInput) -> bool:
        """Add or update knowledge in the knowledge base"""
        return self.kb.upsert_knowledge(
            title=input.title,
            content=input.content,
            metadata=input.to_metadata()
        )
    
    def batch_upsert(self, input: BatchKnowledgeUpdateInput) -> List[bool]:
        """Batch upsert multiple knowledge items"""
        results = []
        for item in input.items:
            try:
                success = self.upsert(item)
                results.append(success)
            except Exception as e:
                print(f"Error upserting item: {e}")
                results.append(False)
        return results
    
    def update_metadata(self, input: MetadataUpdateInput) -> bool:
        """Update a specific metadata field for a knowledge item"""
        if input.id:
            item = self.kb.find_similar_knowledge(input.id)
            if not item:
                return False
        else:
            items = self.kb.search_knowledge(input.query, 1)
            if not items:
                return False
            item = items[0]
        
        # Update the specific field
        if input.field == "importance":
            item.metadata.importance = input.value
        elif input.field == "related_topics":
            item.metadata.related_topics = input.value
        elif input.field == "references":
            item.metadata.references = input.value
        elif input.field == "language":
            item.metadata.language = input.value
        elif input.field == "tags":
            item.metadata.tags = input.value
            
        return self.kb.upsert_knowledge(
            title=item.title,
            content=item.content,
            metadata=item.metadata
        )
    
    def batch_update_metadata(self, input: BatchMetadataUpdateInput) -> List[bool]:
        """Batch update metadata for multiple knowledge items"""
        results = []
        for update in input.updates:
            results.append(self.update_metadata(update))
        return results
    
    def query_by_metadata(self, input: MetadataQueryInput) -> List[dict]:
        """Search knowledge base by metadata field"""
        # Get all items
        items = self.kb.search_knowledge("", input.limit)
        
        # Filter by metadata
        filtered = []
        for item in items:
            metadata = item["metadata"]
            if input.field == "importance" and metadata["importance"] == input.value:
                filtered.append(item)
            elif input.field == "related_topics" and any(topic in metadata["related_topics"] for topic in input.value):
                filtered.append(item)
            elif input.field == "references" and any(ref in metadata["references"] for ref in input.value):
                filtered.append(item)
            elif input.field == "language" and metadata["language"] == input.value:
                filtered.append(item)
            elif input.field == "tags" and any(tag in metadata["tags"] for tag in input.value):
                filtered.append(item)
            elif input.field == "source" and metadata["source"] == input.value:
                filtered.append(item)
        
        return filtered
    
    def get_metadata(self, id: str) -> Optional[dict]:
        """Get all metadata for a specific knowledge item"""
        item = self.kb.find_similar_knowledge(id)
        if item:
            return item.metadata.dict()
        return None
    
    def add_reference(self, id: str, reference: str) -> bool:
        """Add a reference to a knowledge item"""
        item = self.kb.find_similar_knowledge(id)
        if not item:
            return False
            
        if reference not in item.metadata.references:
            item.metadata.references.append(reference)
            return self.kb.upsert_knowledge(
                title=item.title,
                content=item.content,
                metadata=item.metadata
            )
        return True
    
    def add_topic(self, id: str, topic: str) -> bool:
        """Add a related topic to a knowledge item"""
        item = self.kb.find_similar_knowledge(id)
        if not item:
            return False
            
        if topic not in item.metadata.related_topics:
            item.metadata.related_topics.append(topic)
            return self.kb.upsert_knowledge(
                title=item.title,
                content=item.content,
                metadata=item.metadata
            )
        return True
