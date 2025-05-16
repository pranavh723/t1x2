from functools import wraps
from datetime import datetime, timedelta
from typing import Callable, Optional
from telegram.ext import ContextTypes
from telegram import Update, CallbackQuery
from config import RATE_LIMITS

class RateLimiter:
    def __init__(self, limit: int, period: int):
        """Initialize rate limiter
        Args:
            limit: Number of requests allowed
            period: Time period in seconds
        """
        self.limit = limit
        self.period = period
        self.requests = {}

    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply rate limiting"""
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                user_id = update.effective_user.id
                
                if user_id not in self.requests:
                    self.requests[user_id] = []
                
                # Remove expired requests
                now = datetime.now()
                self.requests[user_id] = [
                    t for t in self.requests[user_id]
                    if now - t < timedelta(seconds=self.period)
                ]
                
                if len(self.requests[user_id]) >= self.limit:
                    message = update.message or (update.callback_query.message if update.callback_query else None)
                    if message:
                        await message.reply_text(
                            f"Too many requests! Please wait {self.period//60} minutes before trying again."
                        )
                    return None
                
                self.requests[user_id].append(now)
                return await func(update, context)
            except Exception as e:
                print(f"Rate limiting error: {str(e)}")
                return None
        
        return wrapper

def rate_limited(limit: int, period: int) -> Callable:
    """Create a rate limiter decorator
    Args:
        limit: Number of requests allowed
        period: Time period in seconds
    Returns:
        Decorator function
    """
    return RateLimiter(limit, period)
