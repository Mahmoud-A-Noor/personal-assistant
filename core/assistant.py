from typing import List, Optional
from models.conversation import Message, MessageRole
from core.vector_db import VectorMemory
from utils.embedding import LocalEmbedder
from pydantic_ai import Agent, Tool

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

    async def run(self, user_input: str) -> str:
        """Process user input and generate a response asynchronously using tools and context"""
        # # Retrieve context from memory
        # related_messages = self.memory.retrieve_related_messages(user_input, num_results=3)
        
        # Generate response with tools and context
        result = await self.agent.run(
            user_prompt=user_input,
            message_history=self.conversation_history
        )
        
        # Extract the response content
        response = result.data
        # Store interaction
        self._store_interaction(user_input, response, result)
        
        
        return response
    
    def _store_interaction(self, user_input: str, response: str, result):
        """Store the conversation interaction in memory"""
        # user_msg = Message(content=user_input, role=MessageRole.USER)
        # assistant_msg = Message(content=response, role=MessageRole.ASSISTANT)
        # self.memory.store_message(user_msg)
        # self.memory.store_message(assistant_msg)
        self.conversation_history.extend(result.all_messages())
        
        
