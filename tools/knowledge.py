import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from utils.embedding.sentence_transformers import SentenceTransformerEmbedder, EmbeddingModel
from pydantic_ai import Tool
from dotenv import load_dotenv
from uuid import uuid4

class KnowledgeTool:
    def __init__(self, collection_name="knowledge_base"):
        """
        Initialize knowledge base with Qdrant vector store
        """
        load_dotenv()
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.encoder = SentenceTransformerEmbedder(model=EmbeddingModel.MPNET)
        self.collection_name = collection_name
        
        # Create collection if it doesn't exist
        try:
            self.client.get_collection(collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.encoder.get_info()["dimension"],
                    distance=Distance.COSINE
                )
            )

    def upsert_knowledge(self, text: str, id: str = None) -> bool:
        """Upsert knowledge into vector store. Returns True if successful."""
        vector = self.encoder.embed(text)
        point = PointStruct(
            id=str(uuid4()),
            vector=vector,
            payload={"text": text}
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return True

    def search_similar(self, query: str, limit: int = 3, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar knowledge"""
        vector = self.encoder.embed(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        
        filtered_results = [
            (r.id, r.score, r.version, r.payload["text"]) 
            for r in results 
            if r.score >= score_threshold
        ]
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {"id": id, "score": score, "version": version, "text": text} 
            for id, score, version, text in filtered_results
        ] if filtered_results else "No similar results found"

    def remove_knowledge(self, id: str) -> bool:
        """Remove knowledge by ID"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[id]
        )
        return True

def get_knowledge_tools() -> List[Tool]:
    """Creates knowledge management tools"""
    knowledge_base = KnowledgeTool()
    
    return [
        Tool(
            knowledge_base.upsert_knowledge,
            name="knowledge_upsert",
            description="Add or update knowledge in the knowledge base"
        ),
        Tool(
            knowledge_base.search_similar,
            name="knowledge_search",
            description="Search for similar knowledge in the knowledge base"
        ),
        Tool(
            knowledge_base.remove_knowledge,
            name="knowledge_remove",
            description="Remove knowledge from the knowledge base by ID"
        )
    ]
