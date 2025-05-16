import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration constants
OWNER_ID = int(os.getenv('OWNER_ID', 0))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Get environment
ENV = os.getenv('ENV', 'development').lower()

# Database configuration
# Use DATABASE_URL if provided, otherwise use SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bingo_bot.db')

# In production, log a warning if no DATABASE_URL is set
if ENV == 'production' and DATABASE_URL == 'sqlite:///bingo_bot.db':
    logger.warning("No DATABASE_URL found. Using SQLite in production.")

# Maintenance mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "The bot is currently in maintenance mode. Please try again later."

# Rate limiting constants
ONE_MINUTE = 60
FIVE_MINUTES = 300
TEN_MINUTES = 600

# Command rate limits (calls per period)
RATE_LIMITS = {
    'start': (10, ONE_MINUTE),  # 10 calls per minute
    'game': (5, FIVE_MINUTES),  # 5 calls per 5 minutes
    'shop': (20, TEN_MINUTES),  # 20 calls per 10 minutes
    'default': (30, ONE_MINUTE)  # Default rate limit
}
