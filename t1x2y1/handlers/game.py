from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new game room"""
    keyboard = [
        [InlineKeyboardButton("Join Game", callback_data="join_game")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Created a new game room!\n"
        "Waiting for players to join...",
        reply_markup=reply_markup
    )

async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Join an existing game room"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"{query.from_user.first_name} has joined the game!"
    )

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the game"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Game is starting!\n"
        "Good luck!"
    )
