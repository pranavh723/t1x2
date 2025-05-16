import os
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration constants
OWNER_ID = int(os.getenv('OWNER_ID', 0))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Get environment
ENV = os.getenv('ENV', 'development').lower()

# Database configuration
DATABASE_URL = 'sqlite:///bingo_bot.db'

# In development, log a warning if no TELEGRAM_BOT_TOKEN is set
if ENV == 'development' and not TELEGRAM_BOT_TOKEN:
    logger.warning("No TELEGRAM_BOT_TOKEN found. Please set it in your environment variables.")

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
