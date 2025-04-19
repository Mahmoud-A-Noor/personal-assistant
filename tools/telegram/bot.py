import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

from core.assistant import PersonalAssistant
from tools.email import get_email_tools
from tools.transcribe import get_transcribe_tools
from tools.knowledge import get_knowledge_tools
from tools.calendar import get_calendar_tools
from .handlers import start, handle_message

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN):
        """Initialize the Telegram Bot with a token and set up the application."""
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
        self.app = ApplicationBuilder().token(token).build()
        self._setup_handlers()
        self._setup_assistant()
        print("Noori Telegram Bot initialized.")

    def _setup_handlers(self):
        """Set up command and message handlers for the bot."""
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    def _setup_assistant(self):
        """Initialize the PersonalAssistant with tools."""
        tools = []
        tools.extend(get_email_tools())
        tools.extend(get_transcribe_tools())
        tools.extend(get_knowledge_tools())
        tools.extend(get_calendar_tools())

        self.assistant = PersonalAssistant(
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
        self.app.bot_data["assistant"] = self.assistant

    async def run(self):
        """Run the Telegram bot."""
        print("Noori Telegram Bot is running...")
        await self.app.run_polling()
