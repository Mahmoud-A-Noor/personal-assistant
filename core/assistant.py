from typing import List, Optional, Dict
from pydantic_ai import Agent, Tool

class PersonalAssistant:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        tools: Optional[List[Tool]] = None,
        agents: Optional[Dict[str, Agent]] = None
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.agents = agents or {}
        
        self.conversation_history = []
        
        # Initialize agent with tools
        self.agent = Agent(
            self.model,
            system_prompt=self.system_prompt,
            tools=self.tools
        )

    async def run(self, user_input: str) -> str:
        """Process user input and generate a response asynchronously using tools, agents, and context"""
        # Always let the LLM decide if this should be delegated to an agent
        result = await self.agent.run(
            user_prompt=user_input,
            message_history=self.conversation_history
        )
        response = result.output
        self._store_interaction(result)

        # Check for agent delegation instruction in the LLM output
        if response.strip().lower().startswith("delegate_to:"):
            lines = response.strip().splitlines()
            agent_line = lines[0]
            task_line = lines[1] if len(lines) > 1 else user_input
            agent_name = agent_line.split(":", 1)[1].strip()
            task = task_line.replace("task:", "").strip() if task_line.lower().startswith("task:") else user_input
            if hasattr(self, 'agents') and agent_name in self.agents:
                agent = self.agents[agent_name]
                agent_result = await agent.run_task(task)
                # Ask LLM to synthesize final answer
                followup_result = await self.agent.run(
                    user_prompt=agent_result,
                    message_history=self.conversation_history
                )
                self._store_interaction(followup_result)
                return followup_result.output
        return response

    def _store_interaction(self, result):
        self.conversation_history.extend(result.new_messages())
