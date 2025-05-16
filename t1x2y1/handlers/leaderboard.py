from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from db.models import User
from db.db import SessionLocal
from utils.ui import create_leaderboard_keyboard

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the leaderboard interface"""
    user_id = update.effective_user.id
    
    # Create leaderboard keyboard
    keyboard = create_leaderboard_keyboard()
    
    await update.message.reply_text(
        "Choose a leaderboard type:",
        reply_markup=keyboard
    )

async def handle_leaderboard_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle leaderboard type selection"""
    query = update.callback_query
    leaderboard_type = query.data.split('_')[1]
    
    # Get leaderboard data
    if leaderboard_type == 'global':
        title = "Global Leaderboard 🌍"
        data = leaderboard.get_global_leaderboard()
    elif leaderboard_type == 'daily':
        title = "Daily Leaderboard 📅"
        data = leaderboard.get_daily_leaderboard()
    elif leaderboard_type == 'weekly':
        title = "Weekly Leaderboard 📅"
        data = leaderboard.get_weekly_leaderboard()
    else:  # friends
        title = "Friends Leaderboard 👥"
        data = leaderboard.get_friends_leaderboard(user_id)
    
    # Format leaderboard message
    message = f"{title}\n\n"
    for entry in data:
        message += f"{entry['rank']}. {entry['username']}\n"
        message += f"  XP: {entry['xp']}\n"
        message += f"  Coins: {entry['coins']} 🪙\n"
        message += f"  Streak: {entry['streak']} days\n\n"
    
    await query.edit_message_text(
        text=message,
        reply_markup=create_leaderboard_keyboard(back=True)
    )

# Leaderboard keyboard layout
def create_leaderboard_keyboard(back: bool = False) -> InlineKeyboardMarkup:
    """Create leaderboard selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🌍 Global", callback_data="leaderboard_global"),
            InlineKeyboardButton("📅 Daily", callback_data="leaderboard_daily")
        ],
        [
            InlineKeyboardButton("📅 Weekly", callback_data="leaderboard_weekly"),
            InlineKeyboardButton("👥 Friends", callback_data="leaderboard_friends")
        ]
    ]
    
    if back:
        keyboard.append([
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ])
    
    return InlineKeyboardMarkup(keyboard)
