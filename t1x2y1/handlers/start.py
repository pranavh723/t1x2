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
            
        # Create database session
        db = SessionLocal()
        try:
            # Check if user exists, if not create new user
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            if not db_user:
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    xp=0,
                    coins=100,  # Initial coins
                    streak=0
                )
                db.add(new_user)
                db.commit()
        finally:
            db.close()

        # Create main menu keyboard
        keyboard = create_main_menu_keyboard()
        
        # Add support, source links, and add to group button
        support_keyboard = [
            [
                InlineKeyboardButton("Support", url="https://t.me/bingobot_support"),
                InlineKeyboardButton("Source", url="https://t.me/Bot_SOURCEC")
            ],
            [
                InlineKeyboardButton(
                    "➕ Add to Group", 
                    url=f"https://t.me/BINGOOGAME_BOT?startgroup=true"
                )
            ]
        ]
        support_markup = InlineKeyboardMarkup(support_keyboard)
        
        # Send welcome message
        await update.message.reply_text(
            f"Welcome to Bingo Bot, {user.first_name}!\n"
            "Play Bingo with friends or against AI!\n\n"
            "Use the buttons below to get started.",
            reply_markup=keyboard
        )
        
        # Send support and source links
        await update.message.reply_text(
            "Need help or want to see the source code?",
            reply_markup=support_markup
        )
    except Exception as e:
        logger.error(f"Error in start_handler: {str(e)}")
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
