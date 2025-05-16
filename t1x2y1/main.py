import os
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from config import OWNER_ID, ENV, MAINTENANCE_MODE, MAINTENANCE_MESSAGE, TELEGRAM_BOT_TOKEN, DATABASE_URL
from utils.rate_limit import rate_limited
from ratelimit import sleep_and_retry, limits
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Table
from db.db import init_db
from db.models import Maintenance
from utils.user_utils import is_user_banned
from utils.maintenance_utils import maintenance_check
from utils.error_handler import error_handler

# Load environment variables
load_dotenv()

# Bot token and owner ID are imported from config.py

# Import handlers
from handlers.start import start_handler
from handlers.game import create_room, join_room, start_game, ai_play
from handlers.shop import show_shop
from handlers.admin import create_admin_handler, create_admin_callback_handler
from handlers.leaderboard import show_leaderboard
from handlers.status import status_handler

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Initialize database and session
try:
    # Use SQLite database that will be created automatically
    engine = create_engine(DATABASE_URL)
    init_db()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database and session initialized successfully")
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")
    if ENV == 'production':
        raise

# Import models
from db.models import User, Room, Game, Card, Maintenance


# Create application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Add command handlers with rate limiting and validation
command_handlers = {
    'start': start_handler,
    'leaderboard': show_leaderboard,
    'shop': show_shop,
    'create_room': create_room,
    'join_room': join_room,
    'start_game': start_game,
    'ai_play': ai_play,
    'status': status_handler
}

async def validate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Validate command parameters and permissions"""
    try:
        if not update.effective_user:
            logger.warning("Command from user not found")
            await update.message.reply_text("❌ User not found.")
            return False
            
        if maintenance_check(update, context):
            logger.info("Command blocked due to maintenance mode")
            return False
            
        if is_user_banned(update.effective_user.id):
            logger.warning(f"Banned user {update.effective_user.id} attempted command")
            await update.message.reply_text("❌ You are banned from using this bot.")
            return False
            
        logger.info(f"Validated command from user {update.effective_user.id}")
        return True
    except Exception as e:
        logger.error(f"Error in validate_command: {str(e)}", exc_info=True)
        await update.message.reply_text("❌ An error occurred. Please try again later.")
        return False

# Define rate limits
RATE_LIMITS = {
    'default': (5, 60),  # 5 requests per 60 seconds
    'create_room': (2, 30),  # 2 requests per 30 seconds
    'join_room': (3, 30),  # 3 requests per 30 seconds
    'start_game': (2, 30),  # 2 requests per 30 seconds
    'ai_play': (10, 60),  # 10 requests per 60 seconds
}

# Define custom exceptions
class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded"""
    pass

# Add command handlers with rate limiting and validation
for cmd, handler in command_handlers.items():
    limit = RATE_LIMITS.get(cmd, RATE_LIMITS['default'])
    
    async def create_wrapper(cmd=cmd, handler=handler):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                if await validate_command(update, context):
                    return await handler(update, context)
            except RateLimitExceeded:
                logger.warning(f"Rate limit exceeded for command {cmd} from user {update.effective_user.id}")
                await update.message.reply_text("⏳ Please wait a moment before trying again.")
            except Exception as e:
                logger.error(f"Error handling command {cmd}: {str(e)}", exc_info=True)
                await update.message.reply_text("❌ An error occurred. Please try again later.")
        return wrapper
    
    application.add_handler(CommandHandler(cmd, rate_limited(*limit)(create_wrapper())))

# Add admin handlers
application.add_handler(create_admin_handler())
application.add_handler(create_admin_callback_handler())

# Add callback query handlers with validation
callback_handlers = {
    'create_room': create_room,
    'join_room': join_room,
    'start_game': start_game,
    'ai_play': ai_play
}

async def validate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Validate callback query permissions"""
    try:
        if not update.callback_query:
            return False
            
        if maintenance_check(update, context):
            return False
            
        if is_user_banned(update.callback_query.from_user.id):
            await update.callback_query.answer("❌ You are banned from using this bot.", show_alert=True)
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error in validate_callback: {str(e)}")
        await update.callback_query.answer("❌ An error occurred. Please try again later.", show_alert=True)
        return False

# Add callback query handlers with validation
for action, handler in callback_handlers.items():
    async def create_callback_wrapper(action=action, handler=handler):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if await validate_callback(update, context):
                return await handler(update, context)
        return wrapper
    
    application.add_handler(CallbackQueryHandler(create_callback_wrapper(), pattern=f"^{action}_"))

# Add error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    try:
        logger.error(f'Update {update} caused error {context.error}')
        
        # Handle specific errors
        if isinstance(context.error, telegram.error.BadRequest):
            logger.error("Bad request error: %s", str(context.error))
        elif isinstance(context.error, telegram.error.TimedOut):
            logger.error("Timeout error: %s", str(context.error))
        elif isinstance(context.error, telegram.error.NetworkError):
            logger.error("Network error: %s", str(context.error))
            
        # Send error message to admin
        if OWNER_ID:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"⚠️ Error in bot:\n\n"
                     f"Error: {str(context.error)}\n"
                     f"Update: {str(update)}\n"
                     f"Traceback: {str(context.error.__traceback__)}"
            )
    except Exception as e:
        logger.error(f"Failed to send error notification: {str(e)}")

application.add_error_handler(error_handler)

# Helper functions
async def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if bot is in maintenance mode"""
    if MAINTENANCE_MODE:
        await update.message.reply_text(MAINTENANCE_MESSAGE)
        return True
    return False

def is_user_banned(user_id: int) -> bool:
    """Check if user is banned"""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        return user and user.banned



# Start the bot
if __name__ == '__main__':
    try:
        logger.info("Starting Bingo Bot...")
        logger.info(f"Using database: {DATABASE_URL}")
        
        # Initialize maintenance mode
        with SessionLocal() as db:
            maintenance = db.query(Maintenance).first()
            if maintenance:
                MAINTENANCE_MODE = maintenance.enabled
                MAINTENANCE_MESSAGE = maintenance.message or MAINTENANCE_MESSAGE
        
        # Add error handler to application before polling
        application.add_error_handler(error_handler.handle_error)
        
        # Run the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        raise
