from dotenv import load_dotenv
load_dotenv()

from core.assistant import PersonalAssistant
from core.vector_db import VectorDB
from core.knowledge import KnowledgeBase
from utils.chunking import TextChunker
from utils.embedding import LocalEmbedder

# Initialize components
chunker = TextChunker()
embedder = LocalEmbedder()
vector_db = VectorDB()
knowledge_base = KnowledgeBase(vector_db)

personal_assistant = PersonalAssistant(
    model='google-gla:gemini-2.0-flash',
    system_prompt="""
        Your name is Noori.
        You are my personal assistant with advanced capabilities including:
        - Web scraping for information
        - Document processing with chunking
        - Local text embeddings
        - Knowledge base integration
        
        Your responses should be precise, formatted, and reliable.
        Ask clarifying questions when needed.
    """,
    chunker=chunker,
    embedder=embedder,
    knowledge_base=knowledge_base
)

# Main interaction loop
print("Noori Assistant initialized. Type 'exit' to quit.")
while True:
    user_prompt = input("\nYou: ")
    if user_prompt.lower() in ['exit', 'quit']:
        break
        
    try:
        result = personal_assistant.run_sync(user_prompt)
        print(f"\nNoori: {result}")
    except Exception as e:
        print(f"\nError: {str(e)}")