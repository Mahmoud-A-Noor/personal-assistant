import os
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client
import hashlib
from utils.embedding import LocalEmbedder


class KnowledgeItem(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    content_hash: str  # Used for duplicate detection
    embedding: List[float]
    metadata: dict = {}


class KnowledgeBase:
    def __init__(self, embedder: Optional[LocalEmbedder] = None, similarity_threshold: float = 0.85):
        self.client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        self.table_name = "knowledge_base"
        self.similarity_threshold = similarity_threshold
        self.embedder = embedder or LocalEmbedder()

    def find_similar_knowledge(self, content: str) -> Optional[KnowledgeItem]:
        """Find semantically similar existing knowledge."""
        query_embedding = self.embedder.generate_embedding(content)
        
        result = self.client.rpc(
            "match_knowledge",
            {
                "query_embedding": query_embedding,
                "similarity_threshold": self.similarity_threshold,
                "match_count": 1
            }
        ).execute()
        
        return KnowledgeItem(**result.data[0]) if result.data else None

    def upsert_knowledge(self, title: str, content: str, metadata: dict = None) -> bool:
        """
        Smart update: 
        - If similar content exists, update it.
        - Otherwise, insert new.
        """
        # Check for similar content
        similar_item = self.find_similar_knowledge(content)
        
        # Generate content hash for duplicate detection
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Generate embedding
        embedding = self.embedder.generate_embedding(content)
        
        # Prepare data
        data = {
            "title": title,
            "content": content,
            "content_hash": content_hash,
            "embedding": embedding,
            "metadata": metadata or {}
        }
        
        if similar_item:
            # Update existing
            self.client.table(self.table_name).update(data).eq("id", similar_item.id).execute()
            return False
        else:
            # Insert new
            self.client.table(self.table_name).insert(data).execute()
            return True
    
    def search_knowledge(self, query: str, limit: int = 3) -> List[dict]:
        """Search knowledge base for relevant information."""
        query_embedding = self.embedder.generate_embedding(query)
        
        result = self.client.rpc(
            "match_knowledge",
            {
                "query_embedding": query_embedding,
                "similarity_threshold": self.similarity_threshold,
                "match_count": limit
            }
        ).execute()
        
        return [dict(item) for item in result.data]