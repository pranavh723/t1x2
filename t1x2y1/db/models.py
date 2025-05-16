from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator

# Define enums using Python's Enum
from enum import Enum as PythonEnum

Base = declarative_base()

class RoomStatus(str, PythonEnum):
    WAITING = "waiting"
    STARTED = "started"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class GameStatus(str, PythonEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Define SQLAlchemy enums
RoomStatusEnum = SQLAlchemyEnum(RoomStatus)
GameStatusEnum = SQLAlchemyEnum(GameStatus)

class Card(Base):
    __tablename__ = 'cards'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    card_data = Column(JSON)
    is_custom = Column(Boolean, default=False)
    active_game_id = Column(Integer, ForeignKey('games.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="cards")
    game = relationship("Game", back_populates="cards")

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room_code = Column(String)
    players = Column(JSON)
    cards = Column(JSON)
    marked = Column(JSON)
    numbers_drawn = Column(JSON, default=list)
    winner_id = Column(Integer)
    status = Column(GameStatusEnum, default=GameStatus.PENDING)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    room = relationship("Room", back_populates="games")
    cards = relationship("Card", back_populates="game")

class Room(Base):
    __tablename__ = 'rooms'
    
    id = Column(Integer, primary_key=True)
    room_code = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    is_private = Column(Boolean, default=False)
    max_players = Column(Integer, default=5)
    call_type = Column(String, default='auto')
    status = Column(RoomStatusEnum, default=RoomStatus.WAITING)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="rooms")
    games = relationship("Game", back_populates="room")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    xp = Column(Integer, default=0)
    coins = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    items = Column(JSON, default=dict)
    achievements = Column(JSON, default=dict)
    quests = Column(JSON, default=dict)
    inventory = Column(JSON, default=dict)
    cards = Column(JSON, default=list)
    banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rooms = relationship("Room", back_populates="owner")
    games = relationship("Game", back_populates="players")
    cards = relationship("Card", back_populates="user")

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    xp = Column(Integer, default=0)
    coins = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    items = Column(JSON, default=dict)
    achievements = Column(JSON, default=dict)
    quests = Column(JSON, default=dict)
    inventory = Column(JSON, default=dict)
    cards = Column(JSON, default=list)
    banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rooms = relationship("Room", back_populates="owner")
    games = relationship("Game", back_populates="players")
    cards = relationship("Card", back_populates="user")


