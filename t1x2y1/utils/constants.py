from enum import Enum
from typing import Dict, List, Tuple

# Game Constants
ROOM_SIZE_LIMIT = 10
GAME_NUMBER_RANGE = (1, 25)
MAX_PLAYERS = 10
MIN_PLAYERS = 2

# Validation Constants
ROOM_CODE_LENGTH = 10
MAX_ROOMS_PER_USER = 5
MAX_ROOMS_PER_CHAT = 3
MAX_GAMES_PER_USER = 10

# Rate Limits
RATE_LIMITS = {
    'create_room': (2, 30),     # 2 requests per 30 seconds
    'join_room': (5, 60),      # 5 requests per 60 seconds
    'mark_number': (10, 30),   # 10 marks per 30 seconds
    'start_game': (1, 60),     # 1 start per minute
    'ai_play': (3, 30),        # 3 AI plays per 30 seconds
    'shop': (5, 60),           # 5 shop requests per minute
    'leaderboard': (3, 60),    # 3 leaderboard requests per minute
    'status': (5, 60),         # 5 status requests per minute
    'default': (10, 60)        # Default rate limit
}

# Card Constants
CARD_SIZE = 5
CARD_NUMBERS = 25

# Game States
class GameStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

# Room States
class RoomStatus(Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

# Maintenance Mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "The bot is currently in maintenance mode. Please try again later."

# Emojis
EMOJIS = {
    'success': "✅",
    'error': "❌",
    'warning': "⚠️",
    'info': "ℹ️",
    'dice': "🎲",
    'game': "🎮",
    'star': "⭐",
    'trophy': "🏆",
    'money': "💰",
    'clock': "⏰",
    'wait': "⏳"
}

# Error Messages
ERROR_MESSAGES = {
    'generic': "An error occurred. Please try again later.",
    'maintenance': "Bot is currently in maintenance mode. Please try again later.",
    'banned': "You are banned from using this bot.",
    'room_not_found': "Room not found!",
    'game_started': "Game has already started!",
    'not_host': "Only the host can start the game!",
    'invalid_input': "Invalid input. Please try again.",
    'rate_limit': "Please wait a moment before trying again.",
    'network': "Network error occurred. Please try again later.",
    'database': "Database error occurred. Please try again later.",
    'timeout': "Request timed out. Please try again.",
    'not_in_group': "This command can only be used in a group chat.",
    'not_in_dm': "This command can only be used in private messages.",
    'invalid_room_code': "Invalid room code format.",
    'room_full': "Room is full!",
    'already_joined': "You're already in this room!",
    'invalid_card': "Invalid bingo card.",
    'number_already_called': "This number has already been called.",
    'invalid_number': "Invalid number. Must be between 1-25.",
    'no_active_game': "No active game in this room.",
    'game_ended': "Game has ended.",
    'not_enough_players': "Not enough players to start game.",
    'invalid_command': "Invalid command. Please use the buttons.",
    'invalid_state': "Invalid game state.",
    'invalid_number_range': "Number must be between 1-25.",
    'invalid_card_format': "Invalid card format.",
    'invalid_room_status': "Room status is invalid.",
    'invalid_game_status': "Game status is invalid.",
    'invalid_user_status': "User status is invalid.",
    'invalid_chat_type': "This command can only be used in a group chat.",
    'room_limit_exceeded': "You've reached the maximum number of rooms.",
    'game_limit_exceeded': "You've reached the maximum number of games.",
    'invalid_room_code_length': "Room code must be 10 characters long.",
    'invalid_card_validation': "Card validation failed.",
    'invalid_game_start': "Game cannot be started in current state.",
    'invalid_number_mark': "Number cannot be marked in current state.",
    'invalid_bingo_claim': "Bingo cannot be claimed in current state."
}

