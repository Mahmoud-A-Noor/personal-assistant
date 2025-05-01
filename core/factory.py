from tools.email import get_email_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools
from agents.browser_agent import BrowserTaskAgent
from agents.planner_agent import PlannerAgent
from knowledge_extractors.base.extractor import BaseExtractor

def build_tools_and_agents(model="google-gla:gemini-2.0-flash"):
    tools = []
    tools.extend(get_email_tools())
    tools.extend(get_knowledge_tools())
    tools.extend(get_calendar_tools())
    tools.extend(BaseExtractor.get_extractor_tools())
    agents = {
        "browser_agent": BrowserTaskAgent(),
        "planner_agent": PlannerAgent(model=model, agents={}, tools=tools)
    }
    agents["planner_agent"].agents = {k: v for k, v in agents.items() if k != "planner_agent"}
    return tools, agents
