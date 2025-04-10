from typing import List, Optional
import supabase
from supabase import create_client, Client
import os
from core.models import Message
from utils.embedding import LocalEmbedder


class VectorMemory:
    def __init__(self, embedder: Optional[LocalEmbedder] = None):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)
        self.table_name = "message_embeddings"
        self.embedder = embedder or LocalEmbedder()
    
    def store_message(self, message: Message):
        # Generate embedding using local embedder
        embedding = self.embedder.generate_embedding(message.content)
        message.embedding = embedding
        
        # Store in Supabase
        data = {
            "content": message.content,
            "role": message.role.value,
            "embedding": embedding,
            "metadata": message.metadata,
            "timestamp": message.timestamp.isoformat()
        }
        self.client.table(self.table_name).insert(data).execute()
    
    def retrieve_related_messages(self, query: str, num_results: int = 5) -> List[Message]:
        # Generate embedding for the query
        query_embedding = self.embedder.generate_embedding(query)
        
        # Query Supabase using vector similarity
        result = self.client.rpc(
            "match_messages",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.78,
                "match_count": num_results
            }
        ).execute()
        
        return [Message(**msg) for msg in result.data]