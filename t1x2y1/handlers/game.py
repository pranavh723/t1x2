from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from db.models import Room, Game, User
from db.db import SessionLocal
import random
from datetime import datetime

# Game keyboard layout
def create_game_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Game", callback_data="join_game")]
    ])

async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new game room"""
    user = update.effective_user
    
    # Create database session
    db = SessionLocal()
    try:
        # Create new room
        room = Room(
            room_code=f"ROOM_{random.randint(10000, 99999)}",
            owner_id=user.id,
            name=f"Room by {user.first_name}",
            status=RoomStatus.WAITING
        )
        db.add(room)
        db.commit()
        
        keyboard = [
            [InlineKeyboardButton("Join Game", callback_data=f"join_game_{room.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Created a new game room!\n"
            f"Room Code: {room.room_code}\n"
            "Waiting for players to join...",
            reply_markup=reply_markup
        )
    finally:
        db.close()

async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Join an existing game room"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await query.answer("Room not found!", show_alert=True)
            return
            
        if room.status != RoomStatus.WAITING:
            await query.answer("Game has already started!", show_alert=True)
            return
            
        # Add player to room
        room.players.append(query.from_user.id)
        db.commit()
        
        await query.answer()
        await query.edit_message_text(
            f"{query.from_user.first_name} has joined the game!\n"
            f"Players in room: {len(room.players)}"
        )
    finally:
        db.close()

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the game"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
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
            players=room.players,
            status=GameStatus.IN_PROGRESS,
            start_time=datetime.utcnow()
        )
        db.add(game)
        room.status = RoomStatus.STARTED
        db.commit()
        
        await query.answer()
        await query.edit_message_text(
            "Game is starting!\n"
            "Good luck!\n"
            f"Players: {len(game.players)}"
        )
    finally:
        db.close()

async def ai_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI moves in the game"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_id == room_id).first()
        if not game:
            await query.answer("Game not found!", show_alert=True)
            return
            
        if game.status != GameStatus.IN_PROGRESS:
            await query.answer("Game is not in progress!", show_alert=True)
            return
            
        # Generate AI move
        # TODO: Implement actual AI logic here
        await query.answer()
        await query.edit_message_text(
            "AI is making its move...\n"
            "Waiting for next move..."
        )
    finally:
        db.close()
