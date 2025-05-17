from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

async def ai_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI opponent play"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "AI is thinking..."
    )
