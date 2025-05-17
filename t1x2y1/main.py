#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    MessageHandler
)
from telegram.error import BadRequest, TimedOut, NetworkError
from dotenv import load_dotenv

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Local imports
from t1x2y1.config import TELEGRAM_BOT_TOKEN, DATABASE_URL
from t1x2y1.db.database import init_db, get_db

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Now import from the project modules
from config import OWNER_ID, ENV, TELEGRAM_BOT_TOKEN, DATABASE_URL
from t1x2y1.utils.rate_limit import rate_limited
from t1x2y1.db.database import engine, SessionLocal, Base
from t1x2y1.db.models import User, Room, Game, Card, Maintenance, Player
from t1x2y1.utils.constants import RoomStatus, GameStatus
from t1x2y1.utils.game_utils import generate_bingo_card, format_bingo_card, create_card_keyboard, check_bingo_pattern, generate_random_number
from ratelimit import sleep_and_retry, limits
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect
from t1x2y1.utils.user_utils import is_user_banned
from t1x2y1.utils.maintenance_utils import maintenance_check

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

# Initialize database - create all tables first
try:
    # Import all models to ensure they're registered with Base
    from t1x2y1.db.models import User, Room, Game, Card, Maintenance, Player
    
    # Explicitly create all tables before attempting any queries
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    
    # Verify tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")
    
    if 'maintenance' not in tables or 'users' not in tables:
        logger.error(f"Critical tables missing after creation: {tables}")
        # Force create specific tables
        if 'maintenance' not in tables:
            Maintenance.__table__.create(bind=engine)
        if 'users' not in tables:
            User.__table__.create(bind=engine)
        if 'rooms' not in tables:
            Room.__table__.create(bind=engine)
        if 'players' not in tables:
            Player.__table__.create(bind=engine)
        logger.info("Forced creation of critical tables")
except Exception as e:
    logger.error(f"Error creating database tables: {str(e)}")
    raise

# Now that tables exist, initialize required data
try:
    # Create database session
    db = SessionLocal()
    
    # Check if maintenance record exists, create if not
    try:
        maintenance = db.query(Maintenance).first()
        if not maintenance:
            maintenance = Maintenance(enabled=False, message="Bot is currently under maintenance.")
            db.add(maintenance)
            db.commit()
            logger.info("Created initial maintenance record")
    except Exception as e:
        logger.error(f"Error checking maintenance record: {str(e)}")
        # Continue even if this fails
        
    # Check if admin user exists
    if OWNER_ID:
        try:
            admin = db.query(User).filter(User.telegram_id == OWNER_ID).first()
            if not admin:
                admin = User(
                    telegram_id=OWNER_ID,
                    username="admin",
                    first_name="Admin",
                    xp=1000,
                    coins=9999,
                    theme="admin"
                )
                db.add(admin)
                db.commit()
                logger.info(f"Created admin user with ID {OWNER_ID}")
        except Exception as e:
            logger.error(f"Error checking admin user: {str(e)}")
            # Continue even if this fails
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    # Continue even if initialization fails
finally:
    if 'db' in locals():
        db.close()

# All models and utilities have been imported above


# Create the Application
application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .read_timeout(30)
    .write_timeout(30)
    .connect_timeout(30)
    .pool_timeout(30)
    .get_updates_connection_pool_size(10)
    .build()
)

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
application.add_handler(CommandHandler("start", start_handler, filters=filters.ChatType.PRIVATE))
logger.info(f"Start handler registered: {application.handlers}")

# Verify all handlers
for handler in application.handlers[0]:
    logger.info(f"Registered handler: {handler.callback.__name__} for commands: {getattr(handler, 'commands', [])}")

# Add essential command handlers directly
application.add_handler(CommandHandler("help", start_handler, filters=filters.ChatType.PRIVATE)) # Replaced help_handler with start_handler

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
                status=RoomStatus.ACTIVE,
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
                Room.status == RoomStatus.ACTIVE
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
        
        # Handle start game menu button
        if query.data == 'start_game_menu':
            # Create game mode selection keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎲 Solo vs AI", callback_data="solo_game"),
                    InlineKeyboardButton("👥 Multiplayer", callback_data="multiplayer_game")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send game mode selection message
            await query.message.edit_text(
                "Choose how you want to play Bingo:",
                reply_markup=reply_markup
            )
            
        # Handle solo game button
        elif query.data == 'solo_game':
            # Create AI difficulty selection keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🟢 Easy", callback_data="ai_easy"),
                    InlineKeyboardButton("🟡 Medium", callback_data="ai_medium"),
                    InlineKeyboardButton("🔴 Hard", callback_data="ai_hard")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="start_game_menu")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send AI difficulty selection message
            await query.message.edit_text(
                "🤖 Choose AI difficulty:",
                reply_markup=reply_markup
            )
            
        # Handle multiplayer game button
        elif query.data == 'multiplayer_game':
            # Create room setup keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎮 Create Room", callback_data="create_room"),
                    InlineKeyboardButton("🌟 Join Room", callback_data="join_room")
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data="start_game_menu")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send room options message
            await query.message.edit_text(
                "👥 Multiplayer Mode:\n\n"
                "Create a new room or join an existing one:",
                reply_markup=reply_markup
            )
            
        # Handle create room button
        elif query.data == 'create_room':
            # Check if this is a private chat
            if query.message.chat.type == 'private':
                # Create room setup keyboard for private chat
                keyboard = [
                    [
                        InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/BINGOOGAME_BOT?startgroup=true")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send instructions for adding to group
                await query.message.edit_text(
                    "🎮 To create a Bingo room:\n\n"
                    "1. Add this bot to a group chat\n"
                    "2. Use /create_room command in the group\n"
                    "3. Or use the Create Room button in the group\n\n"
                    "Click the Add to Group button to add the bot to your group!",
                    reply_markup=reply_markup
                )
            else:
                # This is a group chat, ask for room setup
                keyboard = [
                    [
                        InlineKeyboardButton("Public Room", callback_data="create_public_room"),
                        InlineKeyboardButton("Private Room", callback_data="create_private_room")
                    ],
                    [
                        InlineKeyboardButton("2 Players", callback_data="players_2"),
                        InlineKeyboardButton("3 Players", callback_data="players_3"),
                        InlineKeyboardButton("5 Players", callback_data="players_5")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Store temporary room settings in user_data
                context.user_data['room_setup'] = {
                    'type': 'public',
                    'max_players': 5,
                    'auto_call': True
                }
                
                # Send room setup message
                await query.message.edit_text(
                    "🎮 Room Setup:\n\n"
                    "Select room type and max players:",
                    reply_markup=reply_markup
                )
                
        # Handle room type and player count selection
        elif query.data.startswith('create_') or query.data.startswith('players_'):
            # Create database session
            db = SessionLocal()
            try:
                # Update room settings based on selection
                if query.data == 'create_public_room':
                    context.user_data['room_setup']['type'] = 'public'
                elif query.data == 'create_private_room':
                    context.user_data['room_setup']['type'] = 'private'
                elif query.data.startswith('players_'):
                    player_count = int(query.data.split('_')[1])
                    context.user_data['room_setup']['max_players'] = player_count
                
                # Create a random room code
                room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Check if user already has an active room
                existing_room = db.query(Room).filter(
                    Room.host_id == user_id,
                    Room.status != 'FINISHED'
                ).first()
                
                if existing_room:
                    # Show error and options
                    keyboard = [
                        [
                            InlineKeyboardButton("Continue Setup", callback_data="force_create_room"),
                            InlineKeyboardButton("Cancel", callback_data="multiplayer_game")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.message.edit_text(
                        f"⚠️ You already have an active room: {existing_room.room_code}\n"
                        f"Do you want to create a new room anyway?",
                        reply_markup=reply_markup
                    )
                    return
                
                # Create new room in database
                new_room = Room(
                    room_code=room_code,
                    host_id=user_id,
                    chat_id=chat_id,
                    status='WAITING',
                    created_at=datetime.now(),
                    room_type=context.user_data['room_setup']['type'],
                    max_players=context.user_data['room_setup']['max_players'],
                    auto_call=context.user_data['room_setup']['auto_call']
                )
                db.add(new_room)
                db.commit()
                
                # Create room management keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("🔗 Invite Friends", callback_data=f"invite_{room_code}"),
                        InlineKeyboardButton("🎮 Start Game", callback_data=f"start_game_{room_code}")
                    ],
                    [
                        InlineKeyboardButton("❌ Leave Room", callback_data="leave_room")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send success message
                await query.message.edit_text(
                    f"🎯 Room Created: #{room_code}\n"
                    f"Players Joined: 1/{context.user_data['room_setup']['max_players']}\n\n"
                    f"Room Type: {context.user_data['room_setup']['type'].capitalize()}\n"
                    f"Auto-Call: {'Yes' if context.user_data['room_setup']['auto_call'] else 'No'}",
                    reply_markup=reply_markup
                )
                
                # Add host as first player
                new_player = Player(
                    user_id=user_id,
                    room_id=new_room.id,
                    joined_at=datetime.now()
                )
                db.add(new_player)
                db.commit()
            except Exception as e:
                logger.error(f"Error creating room: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to create room. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                    ]])
                )
            finally:
                db.close()
        
        # Handle join room button
        elif query.data == 'join_room':
            # Create custom keyboard for room code entry
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send room code entry message
            await query.message.edit_text(
                "🌟 To join a room, send the room code.\n\n"
                "Example: /join ABC123",
                reply_markup=reply_markup
            )
            
        # Handle invite link generation
        elif query.data.startswith('invite_'):
            # Extract room code from callback data
            room_code = query.data.split('_')[1]
            
            # Create invite link
            invite_link = f"https://t.me/BINGOOGAME_BOT?start=join_{room_code}"
            
            # Create keyboard with invite link
            keyboard = [
                [
                    InlineKeyboardButton("🔗 Copy Invite Link", url=invite_link)
                ],
                [
                    InlineKeyboardButton("🔙 Back to Room", callback_data=f"room_info_{room_code}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send invite message
            await query.message.edit_text(
                f"🔗 Invite Friends to Room #{room_code}\n\n"
                f"Share this link with friends to join your game:\n"
                f"{invite_link}\n\n"
                f"Or they can use command: /join {room_code}",
                reply_markup=reply_markup
            )
            
        # Handle room info display
        elif query.data.startswith('room_info_'):
            # Extract room code from callback data
            room_code = query.data.split('_')[2]
            
            # Create database session
            db = SessionLocal()
            try:
                # Get room info
                room = db.query(Room).filter(Room.room_code == room_code).first()
                
                if not room:
                    await query.message.edit_text(
                        "❌ Room not found. It may have been deleted.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                        ]])
                    )
                    return
                
                # Get player count
                player_count = db.query(Player).filter(Player.room_id == room.id).count()
                
                # Create room management keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("🔗 Invite Friends", callback_data=f"invite_{room_code}"),
                        InlineKeyboardButton("🎮 Start Game", callback_data=f"start_game_{room_code}")
                    ],
                    [
                        InlineKeyboardButton("❌ Leave Room", callback_data="leave_room")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send room info message
                await query.message.edit_text(
                    f"🎯 Room: #{room_code}\n"
                    f"Players Joined: {player_count}/{room.max_players}\n\n"
                    f"Room Type: {room.room_type.capitalize()}\n"
                    f"Auto-Call: {'Yes' if room.auto_call else 'No'}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error getting room info: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to get room info. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="multiplayer_game")
                    ]])
                )
            finally:
                db.close()
        
        # Handle profile button
        elif query.data == 'profile':
            # Create database session
            db = SessionLocal()
            try:
                # Get user from database
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    # Create profile keyboard
                    keyboard = [
                        [
                            InlineKeyboardButton("🎨 Change Theme", callback_data="change_theme"),
                            InlineKeyboardButton("📜 My Stats", callback_data="my_stats")
                        ],
                        [
                            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    # Format user stats
                    await query.message.edit_text(
                        f"👤 Profile: @{query.from_user.username or query.from_user.first_name}\n\n"
                        f"XP: {user.xp or 0}\n"
                        f"Coins: {user.coins or 0}\n"
                        f"Theme: {user.theme.capitalize()}\n"
                        f"Streak: 🔥 {user.streak or 0} Days",
                        reply_markup=reply_markup
                    )
                else:
                    # User not found in database
                    keyboard = [
                        [
                            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.message.edit_text(
                        "👤 Your Profile:\n\n"
                        "You don't have a profile yet. Play a game to create one!",
                        reply_markup=reply_markup
                    )
            finally:
                db.close()
        
        # Handle leaderboard button
        elif query.data == 'leaderboard':
            # Create database session
            db = SessionLocal()
            try:
                # Create leaderboard view selection keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("📅 Daily", callback_data="leaderboard_daily"),
                        InlineKeyboardButton("🌍 Global", callback_data="leaderboard_global"),
                        InlineKeyboardButton("👤 Friends", callback_data="leaderboard_friends")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Get top 10 users by XP
                top_users = db.query(User).order_by(User.xp.desc()).limit(10).all()
                
                if top_users:
                    # Format leaderboard
                    leaderboard_text = "🏆 Leaderboard - Global\n\n"
                    for i, user in enumerate(top_users):
                        leaderboard_text += f"{i+1}. @{user.username or user.first_name} - {user.xp} XP\n"
                    
                    await query.message.edit_text(
                        leaderboard_text,
                        reply_markup=reply_markup
                    )
                else:
                    # No users found
                    await query.message.edit_text(
                        "🏆 Leaderboard is empty. Be the first to play!",
                        reply_markup=reply_markup
                    )
            finally:
                db.close()
                
        # Handle shop button
        elif query.data == 'shop':
            # Create shop keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🎨 Theme Pack - 50", callback_data="buy_theme"),
                    InlineKeyboardButton("💥 Power Cut - 30", callback_data="buy_power")
                ],
                [
                    InlineKeyboardButton("🔁 Rematch+ - 20", callback_data="buy_rematch"),
                    InlineKeyboardButton("💎 Premium Card - 100", callback_data="buy_premium")
                ],
                [
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create database session to get user coins
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                coins = user.coins if user else 0
                
                # Send shop message
                await query.message.edit_text(
                    f"🛒 BINGO SHOP\n\n"
                    f"Your Coins: {coins}\n\n"
                    f"Spend your coins on power-ups, themes, and upgrades!",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error showing shop: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to load shop. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
                    ]])
                )
            finally:
                db.close()
                
        # Handle daily quests button
        elif query.data == 'daily_quests':
            # Create quests keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create database session to get user quest progress
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                
                # Placeholder quest data (would normally come from database)
                quests = [
                    {"name": "Play 1 game", "completed": user.games_played > 0 if user else False},
                    {"name": "Win a game", "completed": user.wins > 0 if user else False},
                    {"name": "Mark 10 numbers", "completed": False}
                ]
                
                # Format quests message
                quests_text = "🎯 Daily Quests\n\n"
                for quest in quests:
                    status = "✅" if quest["completed"] else "⬜"
                    quests_text += f"{status} {quest['name']}\n"
                
                quests_text += "\nComplete all to earn bonus XP/coins!"
                
                # Send quests message
                await query.message.edit_text(
                    quests_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error showing quests: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to load quests. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="back_to_main")
                    ]])
                )
            finally:
                db.close()
        
        # Handle back to main menu button
        elif query.data == 'back_to_main':
            # Create main menu keyboard based on UI/UX design plan
            keyboard = [
                [
                    InlineKeyboardButton("🔹 Start Game", callback_data="start_game_menu")
                ],
                [
                    InlineKeyboardButton("📊 Leaderboard", callback_data="leaderboard"),
                    InlineKeyboardButton("🧩 Daily Quests", callback_data="daily_quests")
                ],
                [
                    InlineKeyboardButton("👤 Profile", callback_data="profile"),
                    InlineKeyboardButton("🛒 Shop", callback_data="shop")
                ],
                [
                    InlineKeyboardButton("📢 Support Group", url="https://t.me/bingobot_support"),
                    InlineKeyboardButton("🔔 Updates Channel", url="https://t.me/Bot_SOURCEC")
                ],
                [
                    InlineKeyboardButton(
                        "➕ Add to Group", 
                        url=f"https://t.me/BINGOOGAME_BOT?startgroup=true"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send welcome message with full keyboard
            await query.message.edit_text(
                f"👋 Welcome to BINGO BOT 🎉\n\n"
                f"Choose a mode below to begin:",
                reply_markup=reply_markup
            )
            
        # Handle AI difficulty selection
        elif query.data.startswith('ai_'):
            difficulty = query.data.split('_')[1]
            
            # Create game start keyboard
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Back", callback_data="solo_game")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message about starting AI game
            await query.message.edit_text(
                f"🤖 Starting {difficulty.capitalize()} AI Game...\n\n"
                f"Your bingo card will be sent to you in a private message.\n"
                f"The AI will call numbers automatically.",
                reply_markup=reply_markup
            )
            
            # Send bingo card to user in private message
            try:
                # Generate a 5x5 bingo card
                bingo_card = generate_bingo_card()
                
                # Format the card for display
                card_text = format_bingo_card(bingo_card)
                
                # Create card marking keyboard
                card_keyboard = create_card_keyboard(bingo_card)
                card_reply_markup = InlineKeyboardMarkup(card_keyboard)
                
                # Send private message with card
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎰 Your Bingo Card (vs {difficulty.capitalize()} AI):\n\n{card_text}\n\nTap numbers to mark them. Get 5 in a row to win!",
                    reply_markup=card_reply_markup
                )
            except Exception as e:
                logger.error(f"Error sending bingo card: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to start game. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back", callback_data="solo_game")
                    ]])
                )
                
        # Handle leave room button
        elif query.data == 'leave_room':
            # Create database session
            db = SessionLocal()
            try:
                # Find player in any active rooms
                player = db.query(Player).join(Room).filter(
                    Player.user_id == user_id,
                    Room.status != 'FINISHED'
                ).first()
                
                if player:
                    # Remove player from room
                    db.delete(player)
                    db.commit()
                    
                    # Check if this was the host
                    room = db.query(Room).filter(Room.id == player.room_id).first()
                    if room and room.host_id == user_id:
                        # If host leaves, end the room
                        room.status = RoomStatus.CANCELLED
                        db.commit()
                        
                        # Notify other players if possible
                        try:
                            other_players = db.query(Player).filter(
                                Player.room_id == room.id,
                                Player.user_id != user_id
                            ).all()
                            
                            for other_player in other_players:
                                try:
                                    await context.bot.send_message(
                                        chat_id=other_player.user_id,
                                        text=f"❌ The host has left room #{room.room_code}. The game has been cancelled."
                                    )
                                except Exception as e:
                                    logger.error(f"Error notifying player {other_player.user_id}: {str(e)}")
                        except Exception as e:
                            logger.error(f"Error notifying other players: {str(e)}")
                    
                    # Return to main menu
                    await query.message.edit_text(
                        "❌ You have left the room.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                        ]])
                    )
                else:
                    # No active room found
                    await query.message.edit_text(
                        "You are not currently in any active rooms.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error leaving room: {str(e)}")
                await query.message.edit_text(
                    "❌ Failed to leave room. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                    ]])
                )
            finally:
                db.close()
        
        # Handle other buttons
        else:
            # For any other button, provide a helpful response
            await query.message.edit_text(
                f"The '{query.data}' feature is coming soon!\n\nStay tuned for updates.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
                ]])
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

# Move bot username logging into an async function
async def log_bot_username():
    username = (await application.bot.get_me()).username
    logger.info("Bot username: @%s", username)

# Call it during initialization
async def main():
    application = None
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", start_handler))
        
        await application.initialize()
        await application.start()
        
        # Start polling with proper cleanup handling
        async with application:
            await application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            while True:
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if application:
            if application.updater:
                await application.updater.stop()
            await application.stop()
            await application.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
