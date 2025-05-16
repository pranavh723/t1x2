from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.models import User
from db.db import SessionLocal
from config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
from utils.user_utils import is_user_banned
import logging

# Set up logger
start_logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    try:
        start_logger.info(f"Start command received from user {update.effective_user.id}")
        user = update.effective_user
        
        # Check maintenance mode
        if MAINTENANCE_MODE:
            await update.message.reply_text(MAINTENANCE_MESSAGE)
            return
            
        # Check if user is banned
        if is_user_banned(user.id):
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
            
        # Simple keyboard with only essential buttons
        keyboard = [
            [
                InlineKeyboardButton("🎮 Play Bingo", callback_data="play_bingo"),
                InlineKeyboardButton("👤 My Profile", callback_data="profile")
            ],
            [
                InlineKeyboardButton(
                    "➕ Add to Group", 
                    url=f"https://t.me/BINGOOGAME_BOT?startgroup=true"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message with simplified keyboard
        await update.message.reply_text(
            f"Welcome to Bingo Bot, {user.first_name}!\n\n"
            "This bot lets you play Bingo with friends in group chats.\n\n"
            "To start playing:\n"
            "1. Add the bot to a group\n"
            "2. Use /create_room command in the group\n"
            "3. Invite friends to join\n"
            "4. Start the game and have fun!\n\n"
            "Use the buttons below to navigate:",
            reply_markup=reply_markup
        )
    except Exception as e:
        start_logger.error(f"Error in start_handler: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

# Main menu keyboard layout
def create_main_menu_keyboard():
    try:
        keyboard = [
            [
                InlineKeyboardButton("🎮 Start Game", callback_data="create_room"),
                InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("quests", callback_data="quests"),
                InlineKeyboardButton("shop", callback_data="shop")
            ],
            [
                InlineKeyboardButton("ℹ️ Support", callback_data="support"),
                InlineKeyboardButton("🔔 Updates", callback_data="updates")
            ],
            [
                InlineKeyboardButton("➕ Add to Group", url="https://t.me/BINGOOGAME_BOT?startgroup=true")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error in create_main_menu_keyboard: {str(e)}")
        return None
