import os
import re
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
        - TEMP: Beautiful logs show which tool is called and which agent is delegated.
        """
        prompt = user_input
        response = ""
        max_turns = 10  # Prevent infinite loops
        tool_pattern = re.compile(r"<(email_[^:>]+|transcribe_audio|knowledge_[^:>]+|calendar_[^:>]+)>", re.IGNORECASE)
        agent_pattern = re.compile(r"<delegate_to:\s*([a-zA-Z0-9_\-]+)>", re.IGNORECASE)
        done_pattern = re.compile(r"</?done\s*>", re.IGNORECASE)
        for turn in range(1, max_turns+1):
            print(f"\033[1;34m[Noori Turn {turn}]\033[0m Sending prompt to LLM:\n\033[0;36m{prompt}\033[0m\n")
            result = await self.agent.run(
                user_prompt=prompt,
                message_history=self.conversation_history
            )
            self._store_interaction(result)
            response = result.output.strip()
            # TEMP LOG: Detect and log tool calls
            for tool_match in tool_pattern.finditer(response):
                print(f"\033[1;32m[TOOL CALL]\033[0m Tool called: \033[1;33m{tool_match.group(1)}\033[0m")
            # TEMP LOG: Detect and log agent delegation
            for agent_match in agent_pattern.finditer(response):
                print(f"\033[1;35m[AGENT DELEGATION]\033[0m Delegated to agent: \033[1;33m{agent_match.group(1)}\033[0m")
            # Check for <done> tag (case-insensitive)
            if done_pattern.search(response):
                print("\033[1;34m[Noori]\033[0m Task completed. Returning final response.\n")
                return response[6:-7].strip()
            # Otherwise, feed back the last response as the new prompt
            prompt = response
        # Fallback: if <done> never found, return last response as-is
        print("\033[1;31m[Noori]\033[0m Max turns reached without <done> tag. Returning last response.\n")
        return response

    def _store_interaction(self, result):
        self.conversation_history.extend(result.new_messages())
