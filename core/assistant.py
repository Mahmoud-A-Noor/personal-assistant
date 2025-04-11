from typing import List, Optional
from core.models import Message, MessageRole
from core.vector_db import VectorMemory
from utils.embedding import LocalEmbedder
from pydantic_ai import Agent, Tool
from datetime import datetime

class PersonalAssistant:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        embedder: Optional[LocalEmbedder] = None,
        tools: Optional[List[Tool]] = None
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.embedder = embedder or LocalEmbedder()
        self.tools = tools or []
        
        self.memory = VectorMemory(embedder=self.embedder)
        self.conversation_history = []
        
        # Initialize agent with tools
        self.agent = Agent(
            self.model,
            system_prompt=self.system_prompt,
            tools=self.tools
        )
    
    def run_sync(self, user_input: str) -> str:
        """Process user input and generate a response using tools and context"""
        # Retrieve context from memory
        related_messages = self.memory.retrieve_related_messages(user_input, num_results=5)
        
        # Generate response with tools and context
        response = self.agent.run_sync(
            user_prompt=user_input,
            message_history=related_messages
        ).data
        
        # Store interaction
        self._store_interaction(user_input, response)
        return response
    
    def _store_interaction(self, user_input: str, response: str):
        """Store the conversation interaction in memory"""
        user_msg = Message(content=user_input, role=MessageRole.USER)
        assistant_msg = Message(content=response, role=MessageRole.ASSISTANT)
        
        self.memory.store_message(user_msg)
        self.memory.store_message(assistant_msg)
        self.conversation_history.extend([user_msg, assistant_msg])