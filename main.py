from dotenv import load_dotenv
load_dotenv()

from core.assistant import PersonalAssistant
from core.knowledge import KnowledgeBase
from tools.knowledge_tool import knowledge_tool
from utils.embedding import LocalEmbedder

# Initialize components
embedder = LocalEmbedder()
knowledge_base = KnowledgeBase(embedder=embedder)

# Get all knowledge tools
tools = knowledge_tool(kb=knowledge_base, max_results=5)

# Create assistant with knowledge tools
personal_assistant = PersonalAssistant(
    model='google-gla:gemini-2.0-flash',
      system_prompt="""
         You are Noori - a smart personal assistant focused on knowledge management. Key rules:

         1. Knowledge Handling:
         - Automatically save valuable information using knowledge_upsert
         - Generate complete metadata without asking user:
         * Importance: Default 3 (neutral), increase for critical info
         * Language: Auto-detect (default 'en')
         * Topics: Extract from content automatically
         * Source: 'manual' for direct user input
         - Never ask for metadata - infer everything from context

         2. Responses:
         - Be concise but helpful
         - When sharing knowledge, include key metadata
         - Only ask questions if absolutely necessary

         3. Operations:
         - Use knowledge_search before answering
         - Update existing knowledge with better info
         - Maintain clean metadata automatically
      """,
    embedder=embedder,
    tools=tools
)

# Main interaction loop
async def main():
   print("Noori Assistant initialized. Type 'exit' to quit.")
   while True:
      user_prompt = input("\nYou: ")
      if user_prompt.lower() in ['exit', 'quit']:
         break
         
      try:
         result = await personal_assistant.run(user_prompt)
         print(f"\nNoori: {result}")
      except Exception as e:
         print(f"\nError: {str(e)}")
         
if __name__ == "__main__":
   import asyncio
   asyncio.run(main())
