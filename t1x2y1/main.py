import os
import logging
import random
import string
from datetime import datetime
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError
from db.models import User, Room, Game, Player
from db.database import SessionLocal
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

# Implement fully functional command handlers

# Create room command handler
async def create_room_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new bingo room"""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"Create room command from user {user_id} in chat {chat_id}")
        
        # Check if this is a private chat
        if update.effective_chat.type == 'private':
            # Send instructions for adding to group
            await update.message.reply_text(
                "🎮 To create a Bingo room:\n\n"
                "1. Add this bot to a group chat\n"
                "2. Use /create_room command in the group\n\n"
                "Use the Add to Group button to add the bot to your group!"
            )
            return
        
        # This is a group chat, create the room
        # Create a random room code
        room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Create database session
        db = SessionLocal()
        try:
            # Check if user already has an active room
            existing_room = db.query(Room).filter(
                Room.host_id == user_id,
                Room.status != 'FINISHED'
            ).first()
            
            if existing_room:
                await update.message.reply_text(
                    f"⚠️ You already have an active room: {existing_room.room_code}\n"
                    f"Please finish or cancel that game first."
                )
                return
            
            # Create new room in database
            new_room = Room(
                room_code=room_code,
                host_id=user_id,
                chat_id=chat_id,
                status='WAITING',
                created_at=datetime.now()
            )
            db.add(new_room)
            db.commit()
            
            # Send success message
            await update.message.reply_text(
                f"🎮 Room created successfully!\n\n"
                f"Room code: {room_code}\n\n"
                f"Share this code with friends to join!\n"
                f"Use /start_game to begin when everyone has joined."
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in create_room_command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

# Join room command handler
async def join_room_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Join an existing bingo room"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Join room command from user {user_id}")
        
        # Check if room code was provided
        if len(context.args) < 1:
            await update.message.reply_text(
                "🌟 Please provide a room code.\n\n"
                "Example: /join ABC123"
            )
            return
        
        # Get room code from arguments
        room_code = context.args[0].upper()
        
        # Create database session
        db = SessionLocal()
        try:
            # Find room with this code
            room = db.query(Room).filter(
                Room.room_code == room_code,
                Room.status == 'WAITING'
            ).first()
            
            if not room:
                await update.message.reply_text(
                    f"❌ Room {room_code} not found or already started.\n"
                    f"Please check the code and try again."
                )
                return
            
            # Check if user is already in this room
            existing_player = db.query(Player).filter(
                Player.user_id == user_id,
                Player.room_id == room.id
            ).first()
            
            if existing_player:
                await update.message.reply_text(
                    f"✅ You are already in room {room_code}!\n"
                    f"Waiting for the host to start the game."
                )
                return
            
            # Add user to room as player
            new_player = Player(
                user_id=user_id,
                room_id=room.id,
                joined_at=datetime.now()
            )
            db.add(new_player)
            db.commit()
            
            # Send success message
            await update.message.reply_text(
                f"✅ Successfully joined room {room_code}!\n"
                f"Waiting for the host to start the game."
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in join_room_command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

# Profile command handler
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Profile command from user {user_id}")
        
        # Create database session
        db = SessionLocal()
        try:
            # Get user from database
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if user:
                # Format user stats
                await update.message.reply_text(
                    f"👤 Your Profile:\n\n"
                    f"Username: {update.effective_user.username or 'Not set'}\n"
                    f"Games played: {user.games_played or 0}\n"
                    f"Wins: {user.wins or 0}\n"
                    f"XP: {user.xp or 0}\n"
                    f"Coins: {user.coins or 0}\n"
                    f"Streak: {user.streak or 0} days"
                )
            else:
                # User not found in database
                await update.message.reply_text(
                    "👤 Your Profile:\n\n"
                    "You don't have a profile yet. Play a game to create one!"
                )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in profile_command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

# Leaderboard command handler
async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show global leaderboard"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Leaderboard command from user {user_id}")
        
        # Create database session
        db = SessionLocal()
        try:
            # Get top 10 users by XP
            top_users = db.query(User).order_by(User.xp.desc()).limit(10).all()
            
            if top_users:
                # Format leaderboard
                leaderboard_text = "🏆 Global Leaderboard:\n\n"
                for i, user in enumerate(top_users):
                    leaderboard_text += f"{i+1}. {user.username or user.first_name}: {user.xp} XP\n"
                
                await update.message.reply_text(leaderboard_text)
            else:
                # No users found
                await update.message.reply_text("🏆 Leaderboard is empty. Be the first to play!")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in leaderboard_command: {str(e)}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

# Register command handlers
application.add_handler(CommandHandler("create_room", create_room_command))
application.add_handler(CommandHandler("join", join_room_command))
application.add_handler(CommandHandler("profile", profile_command))
application.add_handler(CommandHandler("leaderboard", leaderboard_command))

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
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        
        # Handle create room button
        if query.data == 'create_room':
            # Check if this is a private chat
            if query.message.chat.type == 'private':
                # Send instructions for adding to group
                await query.message.reply_text(
                    "🎮 To create a Bingo room:\n\n"
                    "1. Add this bot to a group chat\n"
                    "2. Use /create_room command in the group\n"
                    "3. Or use the Create Room button in the group\n\n"
                    "Click the Add to Group button to add the bot to your group!"
                )
            else:
                # This is a group chat, create the room
                try:
                    # Create a random room code
                    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    
                    # Create database session
                    db = SessionLocal()
                    try:
                        # Create new room in database
                        new_room = Room(
                            room_code=room_code,
                            host_id=user_id,
                            chat_id=chat_id,
                            status='WAITING',
                            created_at=datetime.now()
                        )
                        db.add(new_room)
                        db.commit()
                        
                        # Send success message
                        await query.message.reply_text(
                            f"🎮 Room created successfully!\n\n"
                            f"Room code: {room_code}\n\n"
                            f"Share this code with friends to join!\n"
                            f"Use /start_game to begin when everyone has joined."
                        )
                    finally:
                        db.close()
                except Exception as e:
                    logger.error(f"Error creating room: {str(e)}")
                    await query.message.reply_text("❌ Failed to create room. Please try again.")
        
        # Handle join room button
        elif query.data == 'join_room':
            # Create custom keyboard for room code entry
            await query.message.reply_text(
                "🌟 To join a room, send the room code.\n\n"
                "Example: /join ABC123"
            )
        
        # Handle profile button
        elif query.data == 'profile':
            # Create database session
            db = SessionLocal()
            try:
                # Get user from database
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    # Format user stats
                    await query.message.reply_text(
                        f"👤 Your Profile:\n\n"
                        f"Username: {query.from_user.username or 'Not set'}\n"
                        f"Games played: {user.games_played or 0}\n"
                        f"Wins: {user.wins or 0}\n"
                        f"XP: {user.xp or 0}\n"
                        f"Coins: {user.coins or 0}\n"
                        f"Streak: {user.streak or 0} days"
                    )
                else:
                    # User not found in database
                    await query.message.reply_text(
                        "👤 Your Profile:\n\n"
                        "You don't have a profile yet. Play a game to create one!"
                    )
            finally:
                db.close()
        
        # Handle leaderboard button
        elif query.data == 'leaderboard':
            # Create database session
            db = SessionLocal()
            try:
                # Get top 10 users by XP
                top_users = db.query(User).order_by(User.xp.desc()).limit(10).all()
                
                if top_users:
                    # Format leaderboard
                    leaderboard_text = "🏆 Global Leaderboard:\n\n"
                    for i, user in enumerate(top_users):
                        leaderboard_text += f"{i+1}. {user.username or user.first_name}: {user.xp} XP\n"
                    
                    await query.message.reply_text(leaderboard_text)
                else:
                    # No users found
                    await query.message.reply_text("🏆 Leaderboard is empty. Be the first to play!")
            finally:
                db.close()
        
        # Handle other buttons
        else:
            # For any other button, provide a helpful response
            await query.message.reply_text(
                f"The '{query.data}' button was pressed.\n\n"
                "Try using the Create Room or Join Room buttons to play Bingo!"
            )
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
