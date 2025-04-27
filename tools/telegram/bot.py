import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from tools.telegram.handlers import start, handle_message
from core.factory import build_tools_and_agents
from core.assistant import PersonalAssistant

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
        """Initialize the PersonalAssistant with tools and agents, just like main.py."""
        tools, agents = build_tools_and_agents()
        self.assistant = PersonalAssistant(
            model="google-gla:gemini-2.0-flash",
            tools=tools,
            agents=agents
        )
        self.app.bot_data["assistant"] = self.assistant

    async def run(self):
        print("Noori Telegram Bot is running...")
        await self.app.run_polling()
