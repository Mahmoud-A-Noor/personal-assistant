import os
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import hashlib
import uuid
from utils.embedding import LocalEmbedder
from datetime import datetime
from models.knowledge import KnowledgeItem, KnowledgeMetadata


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

    def upsert_knowledge(self, title: str, content: str, metadata: KnowledgeMetadata = KnowledgeMetadata()) -> bool:
        """Store or update a knowledge item"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Generate embedding
        embedding = self.embedder.generate_embedding(content)
        
        # Create or update point
        try:
            point = PointStruct(
                id=str(uuid.uuid4()),  # Use UUID as point ID
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
        except Exception as e:
            print(f"Error storing knowledge: {str(e)}")
            return False

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