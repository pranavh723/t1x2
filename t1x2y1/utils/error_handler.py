from typing import Dict, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError, NetworkError, BadRequest, TimedOut
from utils.constants import ERROR_MESSAGES, EMOJIS
from ratelimit import sleep_and_retry, limits
from functools import wraps
import time
import logging

# Set up logger
error_logger = logging.getLogger(__name__)

# Create a global instance of the error handler
error_handler = None

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass

class ErrorHandler:
    def __init__(self):
        # Rate limiting settings
        self.command_limits = {
            'create_room': (2, 30),  # 2 requests per 30 seconds
            'join_room': (5, 60),   # 5 requests per 60 seconds
            'mark_number': (10, 30), # 10 marks per 30 seconds
            'default': (10, 60)     # Default rate limit
        }
        self.user_rates = {}
        
        self.error_responses: Dict[str, Tuple[str, str]] = {
            'generic': ("❌ An error occurred. Please try again later.", "error"),
            'maintenance': ("🛠️ Bot is currently in maintenance mode. Please try again later.", "info"),
            'banned': ("❌ You are banned from using this bot.", "error"),
            'room_not_found': ("❌ Room not found!", "error"),
            'game_started': ("❌ Game has already started!", "error"),
            'not_host': ("❌ Only the host can start the game!", "error"),
            'invalid_input': ("❌ Invalid input. Please try again.", "error"),
            'rate_limit': ("⏳ Please wait a moment before trying again.", "info"),
            'network': ("🌐 Network error occurred. Please try again later.", "error"),
            'database': ("💾 Database error occurred. Please try again later.", "error"),
            'timeout': ("⏳ Request timed out. Please try again.", "info"),
            'not_in_group': ("👥 This command can only be used in a group chat.", "error"),
            'not_in_dm': ("👤 This command can only be used in private messages.", "error"),
            'invalid_room_code': ("❌ Invalid room code format.", "error"),
            'room_full': ("👥 Room is full!", "error"),
            'already_joined': ("❌ You're already in this room!", "error"),
            'invalid_card': ("❌ Invalid bingo card.", "error"),
            'number_already_called': ("❌ This number has already been called.", "error"),
            'invalid_number': ("❌ Invalid number. Must be between 1-25.", "error"),
            'no_active_game': ("❌ No active game in this room.", "error"),
            'game_ended': ("🏁 Game has ended.", "info"),
            'not_enough_players': ("👥 Not enough players to start game.", "error"),
            'invalid_command': ("❌ Invalid command. Please use the buttons.", "error"),
            'invalid_state': ("❌ Invalid game state.", "error"),
            'invalid_number_range': ("❌ Number must be between 1-25.", "error"),
            'invalid_card_format': ("❌ Invalid card format.", "error"),
            'invalid_room_status': ("❌ Room status is invalid.", "error"),
            'invalid_game_status': ("❌ Game status is invalid.", "error"),
            'invalid_user_status': ("❌ User status is invalid.", "error")
        }

    def rate_limited(self, limit: Tuple[int, int]):
        """Decorator for rate limiting commands"""
        def decorator(func):
            @wraps(func)
            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user_id = update.effective_user.id
                command = update.callback_query.data.split('_')[0] if update.callback_query else 'default'
                
                # Check rate limit
                if not self._check_rate_limit(user_id, command):
                    raise RateLimitExceeded("Rate limit exceeded")
                
                return await func(update, context)
            return wrapper
        return decorator

    def _check_rate_limit(self, user_id: int, command: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = time.time()
        limit = self.command_limits.get(command, self.command_limits['default'])
        
        if user_id not in self.user_rates:
            self.user_rates[user_id] = {
                'last_request': now,
                'request_count': 1
            }
            return True
            
        user_data = self.user_rates[user_id]
        time_diff = now - user_data['last_request']
        
        if time_diff < limit[1]:  # within time window
            if user_data['request_count'] >= limit[0]:
                return False
            user_data['request_count'] += 1
        else:
            user_data['last_request'] = now
            user_data['request_count'] = 1
            
        return True

    async def handle_error(self, update: Update, error: Exception) -> None:
        """Handle and respond to errors"""
        error_type = self._get_error_type(error)
        response = self.error_responses.get(error_type, self.error_responses['generic'])
        
        try:
            # Send error message
            if update.callback_query:
                await update.callback_query.answer(response[0], show_alert=True)
            elif update.message:
                await update.message.reply_text(
                    f"{EMOJIS[response[1]]} {response[0]}"
                )
        except TelegramError as e:
            # Log if we can't send error message
            print(f"Error sending error message: {str(e)}")
        
        # Log the error
        self._log_error(error, error_type)

    def _get_error_type(self, error: Exception) -> str:
        """Determine error type based on exception"""
        if isinstance(error, TelegramError):
            if isinstance(error, TimedOut):
                return 'timeout'
            elif isinstance(error, NetworkError):
                return 'network'
            elif isinstance(error, BadRequest):
                return 'invalid_input'
        elif isinstance(error, ValueError):
            if 'room code' in str(error).lower():
                return 'invalid_room_code'
            elif 'card' in str(error).lower():
                return 'invalid_card'
        elif isinstance(error, KeyError):
            return 'invalid_command'
        
        return 'generic'

    def _log_error(self, error: Exception, error_type: str) -> None:
        """Log the error with type and details"""
        print(f"[ERROR] Type: {error_type}, Message: {str(error)}")
        
        # Additional logging for specific error types
        if error_type == 'database':
            print(f"Database error details: {error.__cause__}")
        elif error_type == 'network':
            print(f"Network error details: {error.__cause__}")

# Create singleton instance
error_handler = ErrorHandler()
