import os
import sys
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Add the project root directory to the Python path for deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Set up logger first
start_logger = logging.getLogger(__name__)

# Import with fallback paths for both local development and deployment
try:
    from t1x2y1.db.models import User
    from t1x2y1.db.database import SessionLocal
    from t1x2y1.config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
    from t1x2y1.utils.user_utils import is_user_banned
except ImportError as e:
    start_logger.error(f"Import error: {str(e)}")
    raise

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with response verification"""
    try:
        if not update.message:
            start_logger.error("No message in update object")
            return
            
        user = update.effective_user
        start_logger.info(f"Processing start from user {user.id}")
        
        # Test response capability
        try:
            await update.message.reply_text(" Bot is initializing...")
        except Exception as e:
            start_logger.error(f"Failed to send test message: {e}")
            return
            
        if update.effective_chat.type != "private":
            start_logger.info(f"Ignoring start command in non-DM chat: {update.effective_chat.id}")
            return
            
        # Create database session
        try:
            db = SessionLocal()
            db.execute("SELECT 1")  # Test connection
            start_logger.info("Database connection successful")
        except Exception as e:
            start_logger.error(f"Database connection failed: {str(e)}")
            await update.message.reply_text(" Database error. Please try again later.")
            return
            
        try:
            # Check if user exists, if not create new user
            db_user = db.query(User).filter(User.telegram_id == user.id).first()
            if not db_user:
                start_logger.info(f"Creating new user: {user.id}")
                new_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    xp=0,
                    coins=100,
                    streak=0,
                    games_played=0,
                    wins=0,
                    theme="classic"
                )
                db.add(new_user)
                db.commit()
                start_logger.info(f"Created new user: {user.id}")
        finally:
            db.close()
        
        # Check maintenance mode
        if MAINTENANCE_MODE:
            start_logger.info("Bot in maintenance mode")
            await update.message.reply_text(MAINTENANCE_MESSAGE)
            return
            
        # Check if user is banned
        if is_user_banned(user.id):
            start_logger.warning(f"Banned user attempted access: {user.id}")
            await update.message.reply_text(" You are banned from using this bot.")
            return
            
        # Create main menu keyboard based on UI/UX design plan
        keyboard = [
            [
                InlineKeyboardButton("", callback_data="start_game_menu")
            ],
            [
                InlineKeyboardButton("", callback_data="leaderboard"),
                InlineKeyboardButton("", callback_data="daily_quests")
            ],
            [
                InlineKeyboardButton("", callback_data="profile"),
                InlineKeyboardButton("", callback_data="shop")
            ],
            [
                InlineKeyboardButton("", url="https://t.me/bingobot_support"),
                InlineKeyboardButton("", url="https://t.me/Bot_SOURCEC")
            ],
            [
                InlineKeyboardButton(
                    "", 
                    url=f"https://t.me/BINGOOGAME_BOT?startgroup=true"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send welcome message with full keyboard
        await update.message.reply_text(
            " Welcome to BINGO BOT \n\n"
            "Choose a mode below to begin:",
            reply_markup=reply_markup
        )
    except Exception as e:
        start_logger.error(f"Error in start_handler: {str(e)}")
        await update.message.reply_text(" An error occurred. Please try again later.")

# Main menu keyboard layout
def create_main_menu_keyboard():
    try:
        keyboard = [
            [
                InlineKeyboardButton("", callback_data="create_room"),
                InlineKeyboardButton("", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton("quests", callback_data="quests"),
                InlineKeyboardButton("shop", callback_data="shop")
            ],
            [
                InlineKeyboardButton("", callback_data="support"),
                InlineKeyboardButton("", callback_data="updates")
            ],
            [
                InlineKeyboardButton("", url="https://t.me/BINGOOGAME_BOT?startgroup=true")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error in create_main_menu_keyboard: {str(e)}")
        return None
