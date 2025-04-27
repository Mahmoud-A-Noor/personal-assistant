from dotenv import load_dotenv
import logging
import os
from agents.browser_agent import BrowserTaskAgent
from agents.planner_agent import PlannerAgent

from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools

##########################################################################################

# TODO: make the agent able to run multiple tools or agents as required per request
# Noori: You have 9 unread emails.
# You: give me summary of them and mark them as read  
# Noori: I have marked all the emails as read.

##########################################################################################


# Load environment variables
load_dotenv()

# Initialize all tools
tools = []
tools.extend(get_email_tools())
tools.extend(get_transcribe_tools())
tools.extend(get_knowledge_tools())
tools.extend(get_calendar_tools())

# Initialize all agents
agents = {
    "browser_agent": BrowserTaskAgent(),
    "planner_agent": PlannerAgent(model="google-gla:gemini-2.0-flash", agents={}, tools=tools)
}
agents["planner_agent"].agents = {k: v for k, v in agents.items() if k != "planner_agent"}

# Initialize assistant with all tools and agents
personal_assistant = PersonalAssistant(
    model="google-gla:gemini-2.0-flash",
    tools=tools,
    agents=agents
)

logger = logging.getLogger(__name__)

# Main interaction loop
async def main():
    print("Noori Email Assistant initialized. Type 'exit' to quit.")
    while True:
        user_prompt = input("\nYou: ")
        if user_prompt.lower() in ['exit', 'quit']:
            break
            
        try:
            result = await personal_assistant.run(user_prompt)
            print(f"\nNoori: {result}")
        except Exception as e:
            print(f"\nNoori: I encountered an error - {str(e)}")
            logger.exception("Error in main loop")
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
