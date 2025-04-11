from typing import List, Optional
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from core.models import Message
from utils.embedding import LocalEmbedder


class VectorMemory:
    def __init__(self, embedder: Optional[LocalEmbedder] = None):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = "message_embeddings"
        self.embedder = embedder or LocalEmbedder()
        
        # Create collection if not exists
        try:
            self.client.get_collection(self.collection_name)
        except Exception as e:
            print(f"Creating new collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.dimension,
                    distance=Distance.COSINE
                )
            )
    
    def store_message(self, message: Message):
        embedding = self.embedder.generate_embedding(message.content)
        message.embedding = embedding
        
        # Use abs() to ensure positive ID and modulo to limit size
        point_id = abs(hash(message.content)) % (2**63 - 1)
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "content": message.content,
                "role": message.role.value,
                "metadata": message.metadata,
                "timestamp": message.timestamp.isoformat()
            }
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    def retrieve_related_messages(self, query: str, num_results: int = 5) -> List[Message]:
        query_embedding = self.embedder.generate_embedding(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=num_results
        )
        
        return [Message(**result.payload) for result in results]