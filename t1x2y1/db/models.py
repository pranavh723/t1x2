from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, BigInteger, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum
from datetime import datetime

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

# Association tables
room_players = Table('room_players', Base.metadata,
    Column('room_id', Integer, ForeignKey('rooms.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

game_players = Table('game_players', Base.metadata,
    Column('game_id', Integer, ForeignKey('games.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class Maintenance(Base):
    __tablename__ = "maintenance"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# User model
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    xp = Column(Integer, default=0)
    coins = Column(Integer, default=100)  # Start with 100 coins
    streak = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    theme = Column(String, default="classic")
    last_daily_quest = Column(DateTime, nullable=True)
    daily_quest_progress = Column(JSON, default={})
    items = Column(JSON, default=dict)
    achievements = Column(JSON, default=dict)
    quests = Column(JSON, default=dict)
    inventory = Column(JSON, default=dict)
    cards = Column(JSON, default=list)
    banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    rooms = relationship("Room", secondary="room_players", back_populates="players")
    games = relationship("Game", secondary="game_players", back_populates="players")
    hosted_rooms = relationship("Room", foreign_keys="Room.host_id", back_populates="host")
    cards = relationship("Card", back_populates="user")

# Room model
class Room(Base):
    __tablename__ = 'rooms'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    room_code = Column(String, unique=True, nullable=False)
    host_id = Column(Integer, ForeignKey('users.id'))
    chat_id = Column(BigInteger, nullable=True)
    name = Column(String, nullable=True)
    room_type = Column(String, default='public')
    max_players = Column(Integer, default=5)
    auto_call = Column(Boolean, default=True)
    status = Column(RoomStatusEnum, default=RoomStatus.WAITING)
    created_at = Column(DateTime, default=datetime.utcnow)
    numbers_called = Column(JSON, default=list)
    current_turn = Column(Integer, default=0)
    
    # Relationships
    games = relationship("Game", back_populates="room")
    host = relationship("User", foreign_keys=[host_id], back_populates="hosted_rooms")
    players = relationship("User", secondary=room_players, back_populates="rooms")

# Game model
class Game(Base):
    __tablename__ = 'games'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    room_code = Column(String)
    winner_id = Column(Integer, ForeignKey('users.id'))
    status = Column(GameStatusEnum, default=GameStatus.PENDING)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    room = relationship("Room", back_populates="games")
    players = relationship("User", secondary=game_players, back_populates="games")
    cards = relationship("Card", back_populates="game")
    numbers_drawn = Column(JSON, default=list)

# Card model
class Card(Base):
    __tablename__ = 'cards'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    card_data = Column(JSON)
    is_custom = Column(Boolean, default=False)
    active_game_id = Column(Integer, ForeignKey('games.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="cards")
    game = relationship("Game", back_populates="cards")

# Player model for tracking players in rooms
class Player(Base):
    __tablename__ = 'players'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    room_id = Column(Integer, ForeignKey('rooms.id'))
    card_data = Column(JSON, nullable=True)  # Player's bingo card
    marked_numbers = Column(JSON, default=list)  # Numbers marked by the player
    has_bingo = Column(Boolean, default=False)  # Whether player has called bingo
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    room = relationship("Room")
