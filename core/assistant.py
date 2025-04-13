from typing import List, Optional
from pydantic_ai import Agent, Tool

class PersonalAssistant:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        tools: Optional[List[Tool]] = None
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        
        self.conversation_history = []
        
        # Initialize agent with tools
        self.agent = Agent(
            self.model,
            system_prompt=self.system_prompt,
            tools=self.tools
        )

    async def run(self, user_input: str) -> str:
        """Process user input and generate a response asynchronously using tools and context"""
        
        # Generate response with tools and context
        result = await self.agent.run(
            user_prompt=user_input,
            message_history=self.conversation_history
        )
        
        # Extract the response content
        response = result.data
        # Store interaction
        self._store_interaction(result)
        
        
        return response
    
    def _store_interaction(self, result):
        self.conversation_history.extend(result.new_messages())
        
        
