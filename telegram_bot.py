import os
import logging
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import asyncio

from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize all tools
tools = []
tools.extend(get_email_tools())
tools.extend(get_transcribe_tools())
tools.extend(get_knowledge_tools())
tools.extend(get_calendar_tools())

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
      - calendar_get_today: Get today's date in YYYY-MM-DD format
      - calendar_create_event: Create event with time conflict checking. Returns either created event details or conflict information
      - calendar_update_event: Update an existing calendar event. Args: calendar_id, event_id, summary, start, end, description
      Responses:
      - Be concise but helpful
      - handle errors gracefully    
      - Only ask questions if absolutely necessary
      - output should always be organized and formatted
   """,
    tools=tools
)

logger = logging.getLogger(__name__)

# --- Restore async handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am Noori, your personal assistant. How can I help you today?",
        reply_markup=ForceReply(selective=True),
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = await personal_assistant.run(user_message)
        await update.message.reply_text(response)
    except Exception as e:
        logger.exception("Error handling message")
        await update.message.reply_text(f"I encountered an error: {str(e)}")

# --- Restore async main ---
async def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Noori Telegram Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except ImportError:
        print("nest_asyncio not installed. Installing now...")
        import subprocess
        subprocess.run(["pip", "install", "nest_asyncio"])
        print("nest_asyncio installed. Please rerun the script.")
