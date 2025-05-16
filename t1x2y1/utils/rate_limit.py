from functools import wraps
from datetime import datetime, timedelta
from typing import Callable, Optional
from telegram.ext import ContextTypes
from telegram import Update

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
                await update.message.reply_text(
                    f"Too many requests! Please wait a moment before trying again."
                )
                return
            
            self.requests[user_id].append(now)
            return await func(update, context)
        
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
