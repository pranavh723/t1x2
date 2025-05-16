from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from db.models import Room, Game, User, RoomStatus, GameStatus, Player
from db.database import SessionLocal
from config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
from utils.game_utils import generate_bingo_card, format_bingo_card, create_card_keyboard, check_bingo_pattern
from utils.user_utils import is_user_banned
from handlers.room_management import create_room as create_room_func, join_room as join_room_func, generate_bingo_card, validate_bingo_card, create_card_keyboard
from utils.error_handler import error_handler
from utils.exceptions import (
    InvalidUserError, InvalidChatTypeError, MaintenanceModeError, BannedUserError, 
    RoomNotFoundError, RateLimitExceeded, AlreadyJoinedError, RoomLimitExceededError, 
    RoomCreationError, GameLimitExceededError, InvalidGameState, InvalidRoomState, 
    InvalidUserState, CardGenerationError, InvalidCardError
)
from ratelimit import sleep_and_retry, limits
from functools import wraps

# Set up logger
game_logger = logging.getLogger(__name__)

# Game keyboard layout
def create_game_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Game", callback_data="join_game")]
    ])

@error_handler.rate_limited(limit=(2, 30))
async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new game room with validation and logging"""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        game_logger.info(f"User {user_id} attempting to create room in chat {chat_id}")
        
        # Validate update
        if not update.effective_user:
            raise InvalidUserError("User not found")
            
        # Validate chat type
        if update.effective_chat.type not in ['group', 'supergroup']:
            # If this is a callback query in private chat, provide a helpful message
            if update.callback_query:
                await update.callback_query.answer("This feature can only be used in a group chat")
                await update.effective_message.reply_text(
                    "🔄 To create a game room:\n\n"
                    "1. Add this bot to a group\n"
                    "2. Use /create_room command in the group\n\n"
                    "Click the 'Add to Group' button below to add the bot to your group!"
                )
                return
            else:
                raise InvalidChatTypeError("This command can only be used in a group chat")
            
        # Check maintenance mode
        if MAINTENANCE_MODE:
            game_logger.info(f"Room creation blocked for user {user_id} due to maintenance mode")
            raise MaintenanceModeError("Bot is currently in maintenance mode")
            
        # Check if user is banned
        if is_user_banned(user_id):
            game_logger.warning(f"Banned user {user_id} attempted to create room")
            raise BannedUserError("You are banned from using this bot")
            
        # Initialize database session
        db = None
        try:
            # Create database session
            db = SessionLocal()
            
            # Check if user has active room
            active_room = db.query(Room).filter(
                Room.host_id == user_id,
                Room.status != RoomStatus.FINISHED
            ).first()
            if active_room:
                game_logger.info(f"User {user_id} already has active room {active_room.room_code}")
                raise AlreadyJoinedError(f"You already have an active room: {active_room.room_code}")
                
            # Validate room count for user
            user_rooms = db.query(Room).filter(
                Room.host_id == user_id,
                Room.status == RoomStatus.FINISHED
            ).count()
            if user_rooms >= MAX_ROOMS_PER_USER:
                raise RoomLimitExceededError(f"You've reached the maximum number of rooms ({MAX_ROOMS_PER_USER})")
                
            # Validate chat room count
            chat_rooms = db.query(Room).filter(
                Room.chat_id == chat_id,
                Room.status != RoomStatus.FINISHED
            ).count()
            if chat_rooms >= MAX_ROOMS_PER_CHAT:
                raise RoomLimitExceededError(f"This chat has reached the maximum number of rooms ({MAX_ROOMS_PER_CHAT})")
                
        finally:
            # Close database session if it was created
            if db is not None:
                db.close()
            
        # Create room
        room = create_room_func(
            host_id=user_id,
            chat_id=chat_id,
            room_type='public',
            max_players=5,
            auto_call=True
        )
        
        if not room:
            raise RoomCreationError("Failed to create room")
            
        game_logger.info(f"Room {room.room_code} created by user {user_id} in chat {chat_id}")
        
        # Create keyboard with room info
        keyboard = [
            [InlineKeyboardButton("Join Game", callback_data=f"join_room_{room.room_code}")],
            [InlineKeyboardButton("Start Game", callback_data=f"start_game_{room.room_code}")],
            [InlineKeyboardButton("Share Room", switch_inline_query=f"room_{room.room_code}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send group message
        await update.message.reply_text(
            f"🎲 Room Created: {room.room_code}\n"
            f"Players Joined: 1/{room.max_players}\n\n"
            "Tap 'Join Game' to invite friends!\n"
            "Use 'Share Room' to send invite link.",
            reply_markup=reply_markup
        )
        
        # Send private message with instructions
        await context.bot.send_message(
            chat_id=user_id,
            text="You've created a room!\n"
                 "Players will receive their cards in private messages.\n"
                 "Use the buttons in group chat to manage the game.\n"
                 f"Room Code: {room.room_code}",
            reply_markup=reply_markup
        )
        
        game_logger.info(f"Room {room.room_code} creation completed successfully")
        
    except RateLimitExceeded as e:
        game_logger.warning(f"Rate limit exceeded for create_room by user {user_id}")
        raise
    except InvalidGameState as e:
        game_logger.error(f"Invalid game state for user {user_id}: {str(e)}")
        raise
    except InvalidRoomState as e:
        game_logger.error(f"Invalid room state for user {user_id}: {str(e)}")
        raise
    except InvalidUserState as e:
        game_logger.error(f"Invalid user state for user {user_id}: {str(e)}")
        raise
    except Exception as e:
        game_logger.error(f"Error in create_room for user {user_id}: {str(e)}", exc_info=True)
        await error_handler.handle_error(update, e)
    finally:
        if db:
            db.close()

@error_handler.rate_limited(limit=(5, 60))
async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle joining a room with validation and logging"""
    try:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        game_logger.info(f"User {user_id} attempting to join room in chat {chat_id}")
        
        # Validate update
        if not update.callback_query:
            raise InvalidCommandError("Invalid callback query")
            
        query = update.callback_query
        
        # Extract room code
        try:
            room_code = query.data.split('_')[2]
            if not room_code.startswith('#ROOM_'):
                raise InvalidRoomCodeError("Invalid room code format")
        except (IndexError, ValueError) as e:
            game_logger.warning(f"Invalid room code format for user {user_id}")
            await query.answer("❌ Invalid room code", show_alert=True)
            raise
            
        # Validate room code length
        if len(room_code) != ROOM_CODE_LENGTH:
            raise InvalidRoomCodeError(f"Room code must be {ROOM_CODE_LENGTH} characters long")
            
        # Check maintenance mode
        if MAINTENANCE_MODE:
            game_logger.info(f"Room join blocked for user {user_id} due to maintenance mode")
            raise MaintenanceModeError("Bot is currently in maintenance mode")
            
        # Check if user is banned
        if is_user_banned(user_id):
            game_logger.warning(f"Banned user {user_id} attempted to join room")
            raise BannedUserError("You are banned from using this bot")
            
        # Validate user status
        db = SessionLocal()
        try:
            # Check if user already has active game
            active_game = db.query(Game).filter(
                Game.player_id == user_id,
                Game.status != GameStatus.FINISHED
            ).first()
            if active_game:
                raise AlreadyInGameError(f"You already have an active game: {active_game.room_code}")
                
            # Check if user has reached game limit
            user_games = db.query(Game).filter(
                Game.player_id == user_id,
                Game.status == GameStatus.FINISHED
            ).count()
            if user_games >= MAX_GAMES_PER_USER:
                raise GameLimitExceededError(f"You've reached the maximum number of games ({MAX_GAMES_PER_USER})")
                
        finally:
            db.close()
            
        # Join room
        room = join_room_func(room_code, user_id)
        if not room:
            game_logger.error(f"Failed to join room {room_code} for user {user_id}")
            raise RoomNotFoundError(f"Room {room_code} not found")
            
        # Validate room status
        if room.status != RoomStatus.ACTIVE:
            raise InvalidRoomState(f"Room is in invalid state: {room.status}")
            
        # Validate player count
        if len(room.members) >= room.max_players:
            raise RoomFullError(f"Room {room_code} is full")
            
        game_logger.info(f"User {user_id} joined room {room_code} in chat {chat_id}")
        
        # Update group message
        keyboard = [
            [InlineKeyboardButton("Join Game", callback_data=f"join_room_{room_code}")],
            [InlineKeyboardButton("Start Game", callback_data=f"start_game_{room_code}")],
            [InlineKeyboardButton("Share Room", switch_inline_query=f"room_{room_code}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎲 Room Code: {room_code}\n"
            f"Players Joined: {len(room.members)}/{room.max_players}\n\n"
            "Tap 'Join Game' to enter!\n"
            "Use 'Share Room' to invite more friends.",
            reply_markup=reply_markup
        )
        
        # Send private message with card
        card = generate_bingo_card()
        if not card:
            game_logger.error(f"Failed to generate card for user {user_id}")
            raise CardGenerationError("Failed to generate bingo card")
            
        # Validate card
        if not validate_bingo_card(card):
            raise InvalidCardError("Generated card is invalid")
            
        card_keyboard = create_card_keyboard(card)
        await context.bot.send_message(
            chat_id=user_id,
            text="Welcome to the game!\n"
                 "Your scorecard is ready.\n"
                 "Wait for the host to start the game.",
            reply_markup=card_keyboard
        )
        
        game_logger.info(f"User {user_id} received valid card for room {room_code}")
        
    except RateLimitExceeded as e:
        game_logger.warning(f"Rate limit exceeded for join_room by user {user_id}")
        raise
    except InvalidGameState as e:
        game_logger.error(f"Invalid game state for user {user_id}: {str(e)}")
        raise
    except InvalidRoomState as e:
        game_logger.error(f"Invalid room state for user {user_id}: {str(e)}")
        raise
    except InvalidUserState as e:
        game_logger.error(f"Invalid user state for user {user_id}: {str(e)}")
        raise
    except Exception as e:
        game_logger.error(f"Error in join_room for user {user_id}: {str(e)}", exc_info=True)
        await error_handler.handle_error(update, e)
    finally:
        if db:
            db.close()

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the game"""
    query = update.callback_query
    room_code = query.data.split('_')[2]
    
    # Create database session
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_code == room_code).first()
        if not room:
            await query.answer("Room not found!", show_alert=True)
            return
            
        if room.status != RoomStatus.WAITING:
            await query.answer("Game has already started!", show_alert=True)
            return
            
        # Create new game
        game = Game(
            room_id=room.id,
            room_code=room.room_code,
            status=GameStatus.IN_PROGRESS,
            start_time=datetime.utcnow()
        )
        db.add(game)
        
        # Generate cards for each player
        for player_id in room.players:
            card = generate_card()
            card_data = {
                'numbers': card,
                'marked': [False] * 25
            }
            
            new_card = Card(
                user_id=player_id,
                card_data=card_data,
                is_custom=False,
                active_game_id=game.id
            )
            db.add(new_card)
            game.cards.append(new_card)
            
        room.status = RoomStatus.STARTED
        db.commit()
        
        await query.answer()
        await query.edit_message_text(
            "Game is starting!\n"
            "Good luck!\n"
            f"Players: {len(room.players)}\n"
            "Waiting for first number..."
        )
    finally:
        db.close()

async def generate_card() -> dict:
    """Generate a random bingo card"""
    try:
        numbers = []
        for i in range(5):
            # Generate numbers for each column
            start = i * 15 + 1
            end = (i + 1) * 15
            column = random.sample(range(start, end + 1), 5)
            numbers.extend(column)
        
        # Shuffle the numbers
        random.shuffle(numbers)
        
        # Create card data structure
        card_data = {
            'numbers': numbers,
            'marked': [False] * 25,
            'timestamp': datetime.utcnow().isoformat()
        }
        return card_data
    except Exception as e:
        logger.error(f"Error generating card: {str(e)}")
        raise

async def ai_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI moves in the game"""
    query = update.callback_query
    room_code = query.data.split('_')[2]
    
    # Create database session
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()
        if not game:
            await query.answer("Game not found!", show_alert=True)
            return
            
        if game.status != GameStatus.IN_PROGRESS:
            await query.answer("Game is not in progress!", show_alert=True)
            return
            
        # Draw a new number
        all_numbers = list(range(1, 76))
        available_numbers = [num for num in all_numbers if num not in game.numbers_drawn]
        
        if not available_numbers:
            await query.answer()
            await query.edit_message_text("All numbers have been drawn!")
            return
            
        new_number = random.choice(available_numbers)
        game.numbers_drawn.append(new_number)
        
        # Check for bingo
        winner = await check_for_bingo(game, db)
        if winner:
            game.status = GameStatus.COMPLETED
            game.winner_id = winner
            game.end_time = datetime.utcnow()
            db.commit()
            
            await query.answer()
            await query.edit_message_text(
                f"BINGO! Player {winner} wins!\n"
                f"Winning number: {new_number}"
            )
            return
            
        await query.answer()
        await query.edit_message_text(
            f"Number drawn: {new_number}\n"
            "Waiting for next move..."
        )
    finally:
        db.close()

async def check_for_bingo(game: Game, db: SessionLocal) -> Optional[int]:
    """Check if any player has bingo"""
    for card in game.cards:
        numbers = card.card_data['numbers']
        marked = card.card_data['marked']
        
        # Check rows
        for i in range(5):
            row = marked[i*5:(i+1)*5]
            if all(row):
                return card.user_id
                
        # Check columns
        for i in range(5):
            column = [marked[i + j*5] for j in range(5)]
            if all(column):
                return card.user_id
                
        # Check diagonals
        diagonal1 = [marked[i*6] for i in range(5)]
        diagonal2 = [marked[i*4] for i in range(4, -1, -1)]
        if all(diagonal1) or all(diagonal2):
            return card.user_id
            
    return None
