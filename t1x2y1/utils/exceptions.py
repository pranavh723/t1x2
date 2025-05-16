from typing import Optional
from telegram import Update

class BingoError(Exception):
    """Base exception for all bingo-related errors"""
    def __init__(self, message: str, update: Optional[Update] = None):
        self.message = message
        self.update = update
        super().__init__(message)

# Game state errors
class InvalidGameState(BingoError):
    """Raised when game state is invalid"""
    pass

class InvalidRoomState(BingoError):
    """Raised when room state is invalid"""
    pass

class InvalidUserState(BingoError):
    """Raised when user state is invalid"""
    pass

# User-related errors
class InvalidUserError(BingoError):
    """Raised when user is invalid"""
    pass

class BannedUserError(BingoError):
    """Raised when user is banned"""
    pass

# Room-related errors
class RoomNotFoundError(BingoError):
    """Raised when room is not found"""
    pass

class RoomLimitExceededError(BingoError):
    """Raised when room limit is exceeded"""
    pass

class RoomCreationError(BingoError):
    """Raised when room creation fails"""
    pass

class AlreadyJoinedError(BingoError):
    """Raised when user is already in a room"""
    pass

# Game-related errors
class GameLimitExceededError(BingoError):
    """Raised when game limit is exceeded"""
    pass

class CardGenerationError(BingoError):
    """Raised when card generation fails"""
    pass

class InvalidCardError(BingoError):
    """Raised when card is invalid"""
    pass

# Chat-related errors
class InvalidChatTypeError(BingoError):
    """Raised when chat type is invalid"""
    pass

# System-related errors
class MaintenanceModeError(BingoError):
    """Raised when bot is in maintenance mode"""
    pass

class RateLimitExceeded(BingoError):
    """Raised when rate limit is exceeded"""
    pass

class InvalidCommandError(BingoError):
    """Raised when command is invalid"""
    pass

class InvalidRoomCodeError(BingoError):
    """Raised when room code is invalid"""
    pass

class RoomNotFoundError(BingoError):
    """Raised when room is not found"""
    pass

class RoomFullError(BingoError):
    """Raised when room is full"""
    pass

class AlreadyJoinedError(BingoError):
    """Raised when user is already in a room/game"""
    pass

class RoomLimitExceededError(BingoError):
    """Raised when room limit is exceeded"""
    pass

class GameLimitExceededError(BingoError):
    """Raised when game limit is exceeded"""
    pass

class AlreadyInGameError(BingoError):
    """Raised when user is already in a game"""
    pass

class CardGenerationError(BingoError):
    """Raised when card generation fails"""
    pass

class InvalidCardError(BingoError):
    """Raised when card is invalid"""
    pass

class BannedUserError(BingoError):
    """Raised when user is banned"""
    pass

class MaintenanceModeError(BingoError):
    """Raised when bot is in maintenance mode"""
    pass

class InvalidChatTypeError(BingoError):
    """Raised when chat type is invalid"""
    pass

class RateLimitExceeded(BingoError):
    """Raised when rate limit is exceeded"""
    pass

class InvalidUserError(BingoError):
    """Raised when user is invalid"""
    pass

class RoomCreationError(BingoError):
    """Raised when room creation fails"""
    pass
