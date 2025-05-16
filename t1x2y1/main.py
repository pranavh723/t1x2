import os
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError
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

# Register command handlers
logger.info("Registering command handlers...")

# Add essential command handlers directly
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(CommandHandler("help", start_handler)) # Replaced help_handler with start_handler

# Simplified handler for all other commands
async def not_implemented_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Temporary handler for commands not yet implemented"""
    command = update.message.text.split()[0].replace('/', '')
    await update.message.reply_text(
        f"The /{command} command is coming soon!\n\n"
        "Please use /start to see available features."
    )
    logger.info(f"User {update.effective_user.id} attempted to use /{command} command")

# Register other commands with the temporary handler
application.add_handler(CommandHandler("create_room", not_implemented_handler))
application.add_handler(CommandHandler("join", not_implemented_handler))
application.add_handler(CommandHandler("start_game", not_implemented_handler))
application.add_handler(CommandHandler("profile", not_implemented_handler))
application.add_handler(CommandHandler("stats", not_implemented_handler))
application.add_handler(CommandHandler("leaderboard", not_implemented_handler))
application.add_handler(CommandHandler("shop", not_implemented_handler))
application.add_handler(CommandHandler("ai_play", not_implemented_handler))
application.add_handler(CommandHandler("status", not_implemented_handler))

# Add admin handlers
application.add_handler(create_admin_handler())
application.add_handler(create_admin_callback_handler())

# Add a simple callback handler for all buttons
logger.info("Registering callback query handlers...")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button presses with a single handler"""
    query = update.callback_query
    await query.answer()
    
    # Log the callback data
    logger.info(f"Button pressed: {query.data} by user {query.from_user.id}")
    
    try:
        if query.data == 'play_bingo':
            await query.message.reply_text(
                "🎮 To play Bingo:\n\n"
                "1. Add this bot to a group chat\n"
                "2. Use /create_room command in the group\n"
                "3. Invite friends to join\n"
                "4. Start the game and have fun!"
            )
        elif query.data == 'profile':
            await query.message.reply_text(
                "👤 Your Profile:\n\n"
                "Username: " + (query.from_user.username or "Not set") + "\n"
                "Games played: 0\n"
                "Wins: 0\n"
                "Profile features coming soon!"
            )
        else:
            await query.message.reply_text(f"The '{query.data}' feature is coming soon!")
    except Exception as e:
        logger.error(f"Error handling button {query.data}: {str(e)}")
        await query.message.reply_text("❌ An error occurred. Please try again later.")

# Register the button handler for all callback patterns
application.add_handler(CallbackQueryHandler(button_handler))
logger.info("Button handler registered successfully")

# Add error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    try:
        # Log the error
        logger.error(f'Update {update} caused error: {context.error}')
        
        # Get user ID for logging if available
        user_id = None
        if update and hasattr(update, 'effective_user') and update.effective_user:
            user_id = update.effective_user.id
            logger.error(f'Error occurred for user {user_id}')
        
        # Handle specific errors
        error_message = "An error occurred. Please try again later."
        if isinstance(context.error, BadRequest):
            logger.error(f"Bad request error: {str(context.error)}")
            error_message = "Invalid request. Please try again."
        elif isinstance(context.error, TimedOut):
            logger.error(f"Timeout error: {str(context.error)}")
            error_message = "Request timed out. Please try again."
        elif isinstance(context.error, NetworkError):
            logger.error(f"Network error: {str(context.error)}")
            error_message = "Network error. Please check your connection."
        
        # Send error notification to user
        try:
            if update and hasattr(update, 'effective_message') and update.effective_message:
                await update.effective_message.reply_text(f"❌ {error_message}")
            elif update and hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.answer(f"❌ {error_message}", show_alert=True)
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
            
        # Send error to admin if OWNER_ID is defined
        if OWNER_ID:
            try:
                error_text = f"⚠️ Bot Error Report:\n\n"
                error_text += f"Error: {str(context.error)}\n"
                if user_id:
                    error_text += f"User: {user_id}\n"
                error_text += f"Update type: {type(update).__name__}"
                
                await context.bot.send_message(chat_id=OWNER_ID, text=error_text)
            except Exception as e:
                logger.error(f"Failed to send error to admin: {str(e)}")
    except Exception as e:
        logger.error(f"Exception in error handler: {str(e)}")

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
        
        # Define error handler function directly
        async def error_handler(update, context):
            """Handle errors in the telegram bot"""
            error = context.error
            logger.error(f"Exception while handling an update: {error}")
            
            try:
                # Send error message if we have an update object
                if update and update.effective_message:
                    await update.effective_message.reply_text(
                        f"❌ An error occurred: {str(error)}"
                    )
            except Exception as e:
                logger.error(f"Error sending error message: {str(e)}")
        
        # Add error handler to application before polling
        application.add_error_handler(error_handler)
        
        # Run the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        raise
