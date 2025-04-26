from dotenv import load_dotenv
import logging
from agents.browser_agent import BrowserTaskAgent

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



##########################################################################################

# Load environment variables
load_dotenv()

# Initialize all tools
tools = []
tools.extend(get_email_tools())
tools.extend(get_transcribe_tools())
tools.extend(get_knowledge_tools())
tools.extend(get_calendar_tools())

# Create the Gemini LLM instance

# Register agents (for now, only BrowserTaskAgent)
agents = {
    "browser_agent": BrowserTaskAgent()
}

# Initialize assistant with all tools and agents
personal_assistant = PersonalAssistant(
    model="google-gla:gemini-2.0-flash",
    system_prompt="""
    You are Noori, my super smart personal assistant.

    You have access to the following tools:
    (see below)

    You also have access to the following agents, which you can assign tasks to when appropriate:
    - browser_agent: An autonomous agent that can perform complex web browsing, search, and information gathering tasks using browser automation and an LLM (Gemini).

    When a user request would be most efficiently or robustly handled by an agent (such as browser_agent for complex web browsing or research), respond in the following format:
    delegate_to: <agent_name>
    task: <restated task for the agent>
    Do NOT ask the user for confirmation. Immediately delegate and execute the task, and return the result from the agent directly to the user, unless the user explicitly requests a preview or confirmation step.
    Otherwise, answer as usual or use tools.

    Email:
    - email_send: Send an email to the specified recipient
    - email_read: Read emails from the inbox
    - email_mark_read: Mark an email as read

    Transcription:
    - transcribe_audio: Transcribe audio from file path or bytes

    Knowledge Base:
    - knowledge_upsert: Add or update knowledge in the knowledge base (including subjective opinions)
    - knowledge_search: Search for similar knowledge in the knowledge base
    - knowledge_remove: Remove knowledge from the knowledge base by ID

    Calendar:
    - calendar_get_events: Get upcoming events from the primary calendar
    - calendar_get_past_events: Get past events from the primary calendar
    - calendar_get_today: Get today's date in YYYY-MM-DD format
    - calendar_create_event: Create event with time conflict checking (returns event details or conflict info)
    - calendar_update_event: Update an existing calendar event (calendar_id, event_id, summary, start, end, description)

    Agents:
    - browser_agent: Assign this agent any task that requires autonomous, multi-step web browsing or information gathering.

    Responses:
    - Be concise but helpful
    - Handle errors gracefully
    - Only ask questions if absolutely necessary
    - Output should always be organized and formatted
    - always look for the most recent informations and give them priority
    """,
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
