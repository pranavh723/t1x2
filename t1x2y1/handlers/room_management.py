from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string
import logging

from db.models import Room, Game, User, RoomStatus, GameStatus
from db.db import SessionLocal
from utils.constants import ROOM_SIZE_LIMIT, ROOM_CODE_LENGTH

# Set up logger
room_logger = logging.getLogger(__name__)

def generate_room_code() -> str:
    """Generate a unique room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=ROOM_CODE_LENGTH))
        db = SessionLocal()
        try:
            if not db.query(Room).filter(Room.room_code == code).first():
                return code
        finally:
            db.close()

def create_room(host_id: int, chat_id: int, is_private: bool = False, max_players: int = ROOM_SIZE_LIMIT) -> Optional[Room]:
    """Create a new room"""
    room_logger.info(f"Creating room for host {host_id} in chat {chat_id}")
    db = SessionLocal()
    try:
        room_code = generate_room_code()
        room = Room(
            room_code=room_code,
            owner_id=host_id,
            is_private=is_private,
            max_players=max_players,
            status=RoomStatus.WAITING,
            created_at=datetime.utcnow()
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        room_logger.info(f"Room {room_code} created successfully")
        return room
    except Exception as e:
        room_logger.error(f"Error creating room: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

def join_room(room_code: str, user_id: int) -> Optional[Room]:
    """Join a user to a room"""
    room_logger.info(f"User {user_id} attempting to join room {room_code}")
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_code == room_code).first()
        if not room:
            room_logger.warning(f"Room {room_code} not found")
            return None
            
        if room.status != RoomStatus.WAITING:
            room_logger.warning(f"Room {room_code} is not in waiting state")
            return None
            
        # Check if user is already in room
        if user_id in [player.id for player in room.players]:
            room_logger.warning(f"User {user_id} is already in room {room_code}")
            return None
            
        # Check room capacity
        if len(room.players) >= room.max_players:
            room_logger.warning(f"Room {room_code} is full")
            return None
            
        # Add user to room
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            # Create user if not exists
            user = User(telegram_id=user_id)
            db.add(user)
            
        room.players.append(user)
        db.commit()
        db.refresh(room)
        room_logger.info(f"User {user_id} joined room {room_code} successfully")
        return room
    except Exception as e:
        room_logger.error(f"Error joining room: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()

def generate_bingo_card() -> List[List[int]]:
    """Generate a random 5x5 bingo card"""
    card = []
    for i in range(5):
        start = i * 15 + 1
        end = (i + 1) * 15
        column = random.sample(range(start, end + 1), 5)
        card.append(column)
    
    # Transpose the card to have rows instead of columns
    return [list(row) for row in zip(*card)]

def validate_bingo_card(card: List[List[int]]) -> bool:
    """Validate a bingo card"""
    if len(card) != 5:
        return False
        
    for row in card:
        if len(row) != 5:
            return False
            
    # Check if all numbers are unique
    all_numbers = [num for row in card for num in row]
    return len(all_numbers) == len(set(all_numbers))

def create_card_keyboard(card: List[List[int]]):
    """Create an inline keyboard for a bingo card"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = []
    for row in card:
        keyboard_row = []
        for num in row:
            keyboard_row.append(InlineKeyboardButton(str(num), callback_data=f"mark_{num}"))
        keyboard.append(keyboard_row)
    
    return InlineKeyboardMarkup(keyboard)
