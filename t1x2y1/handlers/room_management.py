from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string
import logging

from t1x2y1.db.models import Room, Game, User, RoomStatus, GameStatus, Player
from t1x2y1.db.database import SessionLocal
from t1x2y1.config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
from t1x2y1.utils.game_utils import generate_bingo_card, format_bingo_card, create_card_keyboard, check_bingo_pattern

# Constants
ROOM_SIZE_LIMIT = 5
ROOM_CODE_LENGTH = 6

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

def create_room(host_id: int, chat_id: int, room_type: str = 'public', max_players: int = ROOM_SIZE_LIMIT, auto_call: bool = True) -> Optional[Room]:
    """Create a new room"""
    room_logger.info(f"Creating room for host {host_id} in chat {chat_id}")
    db = SessionLocal()
    try:
        room_code = generate_room_code()
        room = Room(
            room_code=room_code,
            host_id=host_id,
            chat_id=chat_id,
            room_type=room_type,
            max_players=max_players,
            auto_call=auto_call,
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
        # Find the room by code
        room = db.query(Room).filter(Room.room_code == room_code).first()
        if not room:
            room_logger.warning(f"Room {room_code} not found")
            return None
            
        # Check if room is in waiting state
        if room.status != 'WAITING':
            room_logger.warning(f"Room {room_code} is not in waiting state")
            return None
            
        # Check if user is already in this room
        existing_player = db.query(Player).filter(
            Player.user_id == user_id,
            Player.room_id == room.id
        ).first()
        
        if existing_player:
            room_logger.warning(f"User {user_id} is already in room {room_code}")
            return room  # Return room anyway since user is already in it
            
        # Check room capacity
        player_count = db.query(Player).filter(Player.room_id == room.id).count()
        if player_count >= room.max_players:
            room_logger.warning(f"Room {room_code} is full")
            return None
            
        # Get or create user
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            # Create user if not exists
            user = User(telegram_id=user_id)
            db.add(user)
            db.commit()
            
        # Add user to room as a player
        new_player = Player(
            user_id=user.id,
            room_id=room.id,
            joined_at=datetime.utcnow()
        )
        db.add(new_player)
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

