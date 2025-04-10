from typing import List, Optional
from core.models import Message, MessageRole
from core.vector_db import VectorMemory
from core.knowledge import KnowledgeBase
from utils.chunking import TextChunker
from utils.embedding import LocalEmbedder
from pydantic_ai import Agent


class PersonalAssistant:
    def __init__(
        self, 
        model: str,
        system_prompt: str,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[LocalEmbedder] = None,
        knowledge_base: Optional[KnowledgeBase] = None
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or LocalEmbedder()
        self.memory = VectorMemory(embedder=self.embedder)
        self.knowledge = knowledge_base or KnowledgeBase(embedder=self.embedder)
        self.conversation_history = []
    
    def run_sync(self, user_input: str) -> str:
        # Process input with chunking if needed
        if len(user_input) > 1000:  # Example threshold for chunking
            chunks = self.chunker.chunk_text(user_input)
            processed_input = " ".join([chunk['content'] for chunk in chunks])
        else:
            processed_input = user_input
            
        # Retrieve relevant context
        related_messages = self.memory.retrieve_related_messages(processed_input)
        knowledge_results = self.knowledge.search_knowledge(processed_input)
        
        # Generate response
        response = self._generate_response(
            user_input=processed_input,
            context_messages=related_messages,
            knowledge_results=knowledge_results
        )
        
        # Store interaction
        self._store_interaction(processed_input, response)
        
        return response
    
    def _generate_response(
        self, 
        user_input: str, 
        context_messages: List[Message], 
        knowledge_results: List[dict]
    ) -> str:
        # Format context
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in context_messages])
        knowledge = "\n".join([f"Knowledge: {item['content']}" for item in knowledge_results])
        
        assistant = Agent(
            self.model,
            system_prompt=self.system_prompt + f"\n\nContext:\n{context}\n{knowledge}",
        )
        return assistant.run_sync(user_input).data
    
    def _store_interaction(self, user_input: str, response: str):
        user_msg = Message(content=user_input, role=MessageRole.USER)
        assistant_msg = Message(content=response, role=MessageRole.ASSISTANT)
        
        self.memory.store_message(user_msg)
        self.memory.store_message(assistant_msg)
        self.conversation_history.extend([user_msg, assistant_msg])