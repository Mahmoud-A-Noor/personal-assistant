import logging
from telegram import Update, ForceReply
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! I am Noori, your personal assistant. How can I help you today?",
        reply_markup=ForceReply(selective=True),
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    user_message = update.message.text
    try:
        assistant = context.application.bot_data["assistant"]
        response = await assistant.run(user_message)
        await update.message.reply_text(response)
    except Exception as e:
        logger.exception("Error handling message")
        await update.message.reply_text(f"I encountered an error: {str(e)}")
