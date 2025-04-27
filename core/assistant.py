import os
from typing import List, Optional, Dict
from pydantic_ai import Agent, Tool

class PersonalAssistant:
    def __init__(
        self,
        model: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        agents: Optional[Dict[str, Agent]] = None,
        prompt_path: Optional[str] = None
    ):
        self.model = model
        self.tools = tools or []
        self.agents = agents or {}
        self.conversation_history = []

        # Read system prompt from file if not provided directly
        if system_prompt is not None:
            self.system_prompt = system_prompt
        else:
            if prompt_path is None:
                prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompts", "assistant.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()

        # Initialize agent with tools
        self.agent = Agent(
            self.model,
            system_prompt=self.system_prompt,
            tools=self.tools
        )

    async def run(self, user_input: str) -> str:
        """
        Implements system prompt logic:
        - The LLM will decide if the task is simple or complex based on the system prompt.
        - The LLM will delegate to planner_agent or handle directly as needed.
        - The LLM will wrap the final response in <done> tags (success or failure).
        - This method loops, feeding back intermediate results, until a <done> tag is found.
        - The <done> tag is removed before returning the response to the user.
        """
        prompt = user_input
        response = ""
        max_turns = 10  # Prevent infinite loops
        for _ in range(max_turns):
            result = await self.agent.run(
                user_prompt=prompt,
                message_history=self.conversation_history
            )
            self._store_interaction(result)
            response = result.output.strip()
            # Check for <done> tag (case-insensitive)
            if response.lower().startswith("<done>") and response.lower().endswith("</done>"):
                # Remove <done> tags and return clean response
                return response[6:-7].strip()
            # Otherwise, feed back the last response as the new prompt
            prompt = response
        # Fallback: if <done> never found, return last response as-is
        return response

    def _store_interaction(self, result):
        self.conversation_history.extend(result.new_messages())
