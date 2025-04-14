from dotenv import load_dotenv

from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools

# Load environment variables
load_dotenv()

# Initialize all tools
tools = []
tools.extend(get_email_tools())
tools.extend(get_transcribe_tools())
tools.extend(get_knowledge_tools())

# Initialize assistant with all tools
personal_assistant = PersonalAssistant(
    model="google-gla:gemini-2.0-flash",
    system_prompt="""
      You are Noori - a smart personal assistant focused on email management.

      you have access to the following tools:
      - email_send: Send an email to the specified recipient
      - email_read: Read emails from the inbox
      - email_mark_read: Mark an email as read
      - transcribe: Transcribe audio from file path, YouTube URL, or bytes

      Responses:
      - Be concise but helpful
      - handle errors gracefully
      - Only ask questions if absolutely necessary
   """,
    tools=tools
)

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
            else:
                print(f"\nNoori: {result}")
        except Exception as e:
            print(f"\nNoori: I encountered an error - {str(e)}")
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
