from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import random
import string

from models import Room, Game, User
from utils.constants import ROOM_SIZE_LIMIT

def generate_room_code() -> str:
    """Generate a unique room code"""
    while True:
        code = "#ROOM_" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        db = SessionLocal()
        try:
            if not db.query(Room).filter(Room.room_code == code).first():
                return code
        finally:
            db.close()

def create_room(host_id: int, is_private: bool = False, max_players: int = 5) -> Room:
    """Create a new room"""
    db = SessionLocal()
    try:
        room_code = generate_room_code()
        room = Room(
            room_code=room_code,
            host_id=host_id,
            is_private=is_private,
            max_players=max_players,
            status="waiting",
            created_at=datetime.utcnow()
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        return room
    finally:
        db.close()

def join_room(room_code: str, user_id: int) -> Optional[Room]:
    """Join a user to a room"""
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_code == room_code).first()
        if not room:
            return None
            
        if room.status != "waiting":
            return None
            
        # Check if user is already in room
        if user_id in room.members:
            return None
            
        # Check room capacity
        if len(room.members) >= room.max_players:
            return None
            
        # Add user to room
        room.members.append(user_id)
        db.commit()
        db.refresh(room)
        return room
    finally:
        db.close()

def get_room(room_code: str) -> Optional[Room]:
    """Get room details"""
    db = SessionLocal()
    try:
        return db.query(Room).filter(Room.room_code == room_code).first()
    finally:
        db.close()

def start_game(room_code: str) -> Optional[Game]:
    """Start a game in the room"""
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_code == room_code).first()
        if not room:
            return None
            
        if room.status != "waiting":
            return None
            
        # Create game
        game = Game(
            room_code=room_code,
            status="in_progress",
            start_time=datetime.utcnow()
        )
        
        # Generate cards for all players
        for player_id in room.members:
            card = generate_bingo_card()
            game.cards[player_id] = card
            game.marked[player_id] = []
            
        # Update room status
        room.status = "active"
        room.current_game_id = game.id
        
        db.add(game)
        db.commit()
        db.refresh(game)
        return game
    finally:
        db.close()

def generate_bingo_card() -> List[List[int]]:
    """Generate a 5x5 bingo card with unique numbers 1-25"""
    numbers = list(range(1, 26))
    random.shuffle(numbers)
    return [numbers[i:i+5] for i in range(0, 25, 5)]
