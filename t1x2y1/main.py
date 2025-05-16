import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from config import OWNER_ID, TELEGRAM_BOT_TOKEN, DATABASE_URL, ENV, MAINTENANCE_MODE, MAINTENANCE_MESSAGE, RATE_LIMITS

from handlers.start import start_handler
from handlers.game import create_room, join_room, start_game
from handlers.social import show_social
from handlers.achievements import show_achievements
from handlers.events import show_events
from handlers.analytics import show_analytics
from handlers.admin import create_admin_handler, create_admin_callback_handler
from db.db import init_db
)
logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Rate limiting constants
ONE_MINUTE = 60
FIVE_MINUTES = 300
TEN_MINUTES = 600

# Command rate limits (calls per period)
RATE_LIMITS = {
    'start': (10, ONE_MINUTE),  # 10 calls per minute
    'game': (5, FIVE_MINUTES),  # 5 calls per 5 minutes
    'shop': (20, TEN_MINUTES),  # 20 calls per 10 minutes
    'default': (30, ONE_MINUTE)  # Default rate limit
}

# Owner ID
OWNER_ID = int(os.getenv('ADMIN_ID', '6985505204'))

# Global maintenance mode flag
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "The bot is currently in maintenance mode. Please try again later."

# Load environment variables


# Get environment
ENV = os.getenv('ENV', 'development').lower()

# Initialize bot
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Set database URL based on environment
if ENV == 'production':
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        logger.warning("No DATABASE_URL found. Using SQLite for development.")
        DATABASE_URL = 'sqlite:///bingo_bot.db'
else:
    DATABASE_URL = 'sqlite:///bingo_bot.db'

# Log environment and database settings
logger.info(f"Starting in {ENV} environment")
logger.info(f"Using database: {DATABASE_URL}")

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")
    if ENV == 'production':
        raise  # In production, we need database
    else:
        logger.warning("Continuing in development mode without database")

# Create application
application = Application.builder().token(TOKEN).build()

# Initialize database
init_db()

# Add handlers with rate limiting
application.add_handler(CommandHandler("start", rate_limited(*RATE_LIMITS['start'])(start_handler)))
application.add_handler(CommandHandler("leaderboard", rate_limited(*RATE_LIMITS['default'])(show_leaderboard)))
application.add_handler(CommandHandler("shop", rate_limited(*RATE_LIMITS['shop'])(show_shop)))
application.add_handler(CommandHandler("quests", rate_limited(*RATE_LIMITS['default'])(show_quests)))
application.add_handler(CommandHandler("cards", rate_limited(*RATE_LIMITS['default'])(show_card_builder)))
application.add_handler(CommandHandler("events", rate_limited(*RATE_LIMITS['default'])(show_events)))
application.add_handler(CommandHandler("achievements", rate_limited(*RATE_LIMITS['default'])(show_achievements)))
application.add_handler(CommandHandler("social", rate_limited(*RATE_LIMITS['default'])(show_social)))
application.add_handler(CommandHandler("analytics", rate_limited(*RATE_LIMITS['default'])(show_analytics)))
application.add_handler(create_admin_handler())
application.add_handler(create_admin_callback_handler())

# Callback query handlers
application.add_handler(CallbackQueryHandler(create_room, pattern="^create_room$"))
application.add_handler(CallbackQueryHandler(join_room, pattern="^join_room$"))
application.add_handler(CallbackQueryHandler(start_game, pattern="^start_game$"))
application.add_handler(CallbackQueryHandler(ai_play, pattern="^ai_play$"))

# Add error handler
def rate_limited(max_calls: int, period: int):
    """Decorator for rate limiting commands"""
    def decorator(func):
        @wraps(func)
        @sleep_and_retry
        @limits(calls=max_calls, period=period)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                # Check maintenance mode
                if await maintenance_check(update, context):
                    return
                
                # Check if user is banned
                if await is_user_banned(update.effective_user.id):
                    await update.message.reply_text("You are banned from using this bot.")
                    return
                
                # Validate command
                if not await validate_command(update, context):
                    return
                
                return await func(update, context)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                await error_handler(update, context)
        return wrapper
    return decorator

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    try:
        # Log to telegram
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"An error occurred:\n{str(context.error)}\n\n"
            f"Update: {update}\n"
            f"Error: {str(context.error)}\n"
            f"Traceback: {str(context.error.__traceback__)}"
        )
    except Exception as e:
        logger.error(f"Failed to send error notification to admin: {str(e)}")

async def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if bot is in maintenance mode"""
    if MAINTENANCE_MODE:
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text(MAINTENANCE_MESSAGE)
            return True
    return False

async def is_user_banned(user_id: int) -> bool:
    """Check if user is banned"""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        return user.banned if user else False

async def validate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Validate command parameters and permissions"""
    command = context.args[0] if context.args else None
    
    # Check if command exists
    if not command:
        await update.message.reply_text("Please provide a valid command.")
        return False
        
    # Add specific command validations here
    return True

async def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if bot is in maintenance mode"""
    if MAINTENANCE_MODE:
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text(MAINTENANCE_MESSAGE)
            return True
    return False

application.add_error_handler(error_handler)

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
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            error_callback=error_handler
        )
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        raise
