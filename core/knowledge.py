import os
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import hashlib
from utils.embedding import LocalEmbedder
from datetime import datetime


class KnowledgeMetadata(BaseModel):
    source: Literal["conversation", "manual", "web", "other"] = Field(
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
    
    importance: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Importance level of this knowledge (1-5)"
    )
    
    related_topics: List[str] = Field(
        default_factory=list,
        description="Topics related to this knowledge"
    )
    
    references: List[str] = Field(
        default_factory=list,
        description="List of references or sources for this knowledge"
    )
    
    language: str = Field(
        default="en",
        description="Language of the knowledge content"
    )


class KnowledgeItem(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    content_hash: str  # Used for duplicate detection
    embedding: List[float]
    metadata: KnowledgeMetadata = Field(
        default_factory=KnowledgeMetadata,
        description="Structured metadata about this knowledge item"
    )


class KnowledgeBase:
    def __init__(self, embedder: Optional[LocalEmbedder] = None, similarity_threshold: float = 0.85):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "knowledge_base"
        self.similarity_threshold = similarity_threshold
        self.embedder = embedder or LocalEmbedder()
        
        # Create collection if not exists
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.dimension,
                    distance=Distance.COSINE
                )
            )

    def find_similar_knowledge(self, content: str) -> Optional[KnowledgeItem]:
        """Find semantically similar existing knowledge."""
        query_embedding = self.embedder.generate_embedding(content)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            score_threshold=self.similarity_threshold,
            limit=1
        )
        
        if results:
            payload = results[0].payload
            return KnowledgeItem(
                id=str(results[0].id),
                title=payload["title"],
                content=payload["content"],
                content_hash=payload["content_hash"],
                embedding=results[0].vector,
                metadata=KnowledgeMetadata(**payload["metadata"])
            )
        return None

    def _update_knowledge(self, id: str, title: str, content: str, metadata: KnowledgeMetadata) -> bool:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        embedding = self.embedder.generate_embedding(content)
        
        # Use positive hash from the id string
        point_id = abs(hash(id)) % (2**63 - 1)
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "title": title,
                "content": content,
                "content_hash": content_hash,
                "metadata": metadata.dict()
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return False

    def _insert_knowledge(self, title: str, content: str, metadata: KnowledgeMetadata) -> bool:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        embedding = self.embedder.generate_embedding(content)
        
        point = PointStruct(
            id=int(hash(content_hash)),
            vector=embedding,
            payload={
                "title": title,
                "content": content,
                "content_hash": content_hash,
                "metadata": metadata.dict()
            }
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return True

    def upsert_knowledge(self, title: str, content: str, metadata: KnowledgeMetadata = KnowledgeMetadata()) -> bool:
        """
        Smart update with merging capabilities:
        - Combines content when similar knowledge exists
        - Preserves important metadata
        - Maintains version history
        """
        similar_item = self.find_similar_knowledge(content)
        
        if similar_item:
            new_title = f"{similar_item.title} + {title}"
            new_content = f"{similar_item.content}\n\n---\n\n{content}"
            
            merged_metadata = similar_item.metadata.copy()
            merged_metadata.version_history.append({
                'timestamp': datetime.now().isoformat(),
                'previous_content': similar_item.content[:200] + '...'
            })
            merged_metadata.update(metadata.dict(exclude_unset=True))
            
            return self._update_knowledge(similar_item.id, new_title, new_content, merged_metadata)
        else:
            return self._insert_knowledge(title, content, metadata)

    def search_knowledge(self, query: str, limit: int = 3) -> List[dict]:
        """Search knowledge base for relevant information."""
        query_embedding = self.embedder.generate_embedding(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            score_threshold=self.similarity_threshold,
            limit=limit
        )
        
        return [{
            "id": str(result.id),
            "title": result.payload["title"],
            "content": result.payload["content"],
            "score": result.score,
            "metadata": KnowledgeMetadata(**result.payload["metadata"]).dict()
        } for result in results]

    def find_knowledge_by_id(self, id: str) -> Optional[KnowledgeItem]:
        """Find knowledge item by its ID or hash."""
        try:
            # Try to find by exact ID
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[int(id)]
            )
            
            if result:
                payload = result[0].payload
                return KnowledgeItem(
                    id=str(result[0].id),
                    title=payload["title"],
                    content=payload["content"],
                    content_hash=payload["content_hash"],
                    embedding=result[0].vector,
                    metadata=KnowledgeMetadata(**payload["metadata"])
                )
            
            # If not found, try to find by content hash
            results = self.client.search(
                collection_name=self.collection_name,
                query_filter={"must": [{"key": "content_hash", "match": {"value": id}}]},
                limit=1
            )
            
            if results:
                payload = results[0].payload
                return KnowledgeItem(
                    id=str(results[0].id),
                    title=payload["title"],
                    content=payload["content"],
                    content_hash=payload["content_hash"],
                    embedding=results[0].vector,
                    metadata=KnowledgeMetadata(**payload["metadata"])
                )
            
            return None
            
        except Exception as e:
            print(f"Error finding knowledge by ID: {e}")
            return None