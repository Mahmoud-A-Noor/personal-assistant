from dotenv import load_dotenv
import logging
from core.factory import build_tools_and_agents
from core.assistant import PersonalAssistant


# Load environment variables
load_dotenv()

# Initialize all tools and agents
tools, agents = build_tools_and_agents()

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
