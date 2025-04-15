from dotenv import load_dotenv
import logging

from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools


# Load environment variables
load_dotenv()

# Initialize all tools
tools = []
tools.extend(get_email_tools())
tools.extend(get_transcribe_tools())
tools.extend(get_knowledge_tools())
tools.extend(get_calendar_tools())

# Initialize assistant with all tools
personal_assistant = PersonalAssistant(
    model="google-gla:gemini-2.0-flash",
    system_prompt="""
      You are Noori my super smart personal assistant.

      you have access to the following tools:
      - email_send: Send an email to the specified recipient
      - email_read: Read emails from the inbox
      - email_mark_read: Mark an email as read
      - transcribe: Transcribe audio from file path or bytes
      - knowledge_upsert: Add or update knowledge in the knowledge base even tho they are subjective opinions
      - knowledge_search: Search for similar knowledge in the knowledge base
      - knowledge_remove: Remove knowledge from the knowledge base by ID
      - calendar_get_events: Get upcoming events from the primary calendar
      - calendar_get_past_events: Get past events from the primary calendar
      - calendar_create_event_with_conflict_check: Create event with time conflict checking. Returns either created event details or conflict information

      Responses:
      - Be concise but helpful
      - handle errors gracefully    
      - Only ask questions if absolutely necessary
   """,
    tools=tools
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
            if not result:  # Handle empty responses
                print("\nNoori: Your inbox is empty")
            elif isinstance(result, dict) and 'status' in result:
                # Handle structured responses from tools
                if result['status'] == 'conflict':
                    print(f"\nNoori: {result['message']}")
                    print("Conflicting events:")
                    for event in result['conflicts']:
                        print(f"- {event['summary']} from {event['start']} to {event['end']}")
                    print(f"\nYour event: {result['proposed_event']['summary']} from {result['proposed_event']['start']} to {result['proposed_event']['end']}")
                elif result['status'] == 'error':
                    print(f"\nNoori: {result['message']}")
                    if 'suggestion' in result:
                        print(f"Suggestion: {result['suggestion']}")
                else:
                    print(f"\nNoori: {result}")
            else:
                print(f"\nNoori: {result}")
        except Exception as e:
            print(f"\nNoori: I encountered an error - {str(e)}")
            logger.exception("Error in main loop")
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
