from dotenv import load_dotenv
from pydantic_ai import Agent
from typing import Dict, Any, Optional, List
import re
import os

load_dotenv()

class PlannerAgent:
    """
    A planning agent that uses a built-in pydantic_ai Agent for plan generation and reasoning.
    This agent is aware of all other agents and tools, but does NOT directly invoke them.
    """
    def __init__(self, model: str, agents: Optional[Dict[str, Any]] = None, tools: Optional[List[Any]] = None, prompt_path: Optional[str] = None, system_prompt: Optional[str] = None):
        self.model = model
        self.agents = agents or {}
        self.tools = tools or []
        # Read system prompt from file if not provided directly
        if system_prompt is None:
            if prompt_path is None:
                prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompts", "planner_agent.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        else:
            self.system_prompt = system_prompt
        self.agent = Agent(
            self.model,
            system_prompt=system_prompt,
        )

    def _docs_dict(self, agents: Dict[str, Any], tools: List[Any]) -> (Dict[str, str], Dict[str, str]):
        agent_docs = {}
        for name, agent in agents.items():
            doc = getattr(agent.__class__, '__doc__', None) or str(agent)
            agent_docs[name] = doc.strip() if doc else "No documentation available."
        tool_docs = {}
        for tool in tools:
            tool_name = getattr(tool, 'name', repr(tool))
            tool_desc = getattr(tool, 'description', None) or str(tool)
            tool_docs[tool_name] = tool_desc.strip() if tool_desc else "No documentation available."
        return agent_docs, tool_docs

    async def plan(self, objective: str, context: Optional[dict] = None) -> List[str]:
        """
        Generate a plan for a given objective, considering available agents and tools (with their docs).
        Returns a list of steps as strings, or an empty list / indicator for impossible tasks.
        """
        agent_docs, tool_docs = self._docs_dict(self.agents, self.tools)
        prompt = (
            f"Objective: {objective}\n"
            f"Agents:\n" + "\n".join(f"- {name}: {doc}" for name, doc in agent_docs.items()) + "\n"
            f"Tools:\n" + "\n".join(f"- {name}: {doc}" for name, doc in tool_docs.items()) + "\n"
            f"Return your plan as a sequence of <step> tags, one for each step, like <step>Do something</step>. "
            f"If the task is impossible or unclear, return <step>Unable to generate a plan for this objective.</step>"
        )
        result = await self.agent.run(user_prompt=prompt)
        steps = re.findall(r'<step>(.*?)</step>', result.output, re.DOTALL)
        steps = [step.strip() for step in steps if step.strip()]
        if not steps:
            return []
        # Check for impossible indicator
        if len(steps) == 1 and 'unable' in steps[0].lower():
            return steps
        return steps
