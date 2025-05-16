import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Required environment variables
required_vars = ['TELEGRAM_BOT_TOKEN', 'OWNER_ID', 'ADMIN_ID', 'DATABASE_URL', 'ENV']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuration constants
OWNER_ID = int(os.getenv('OWNER_ID'))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Get environment
ENV = os.getenv('ENV', 'development').lower()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')

# In development, log a warning if no TELEGRAM_BOT_TOKEN is set
if ENV == 'development' and not TELEGRAM_BOT_TOKEN:
    logger.warning("No TELEGRAM_BOT_TOKEN found. Please set it in your environment variables.")

# Maintenance mode
MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
MAINTENANCE_MESSAGE = os.getenv('MAINTENANCE_MESSAGE', "The bot is currently in maintenance mode. Please try again later.")

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

# Banned users list
BANNED_USERS = []

# Game configuration
MAX_PLAYERS = 5
MIN_PLAYERS = 2
GAME_TIMEOUT = 600  # 10 minutes in seconds

# Achievement system
ACHIEVEMENTS = {
    'first_game': {
        'name': 'First Game',
        'description': 'Play your first game',
        'points': 10
    },
    'bingo_winner': {
        'name': 'Bingo Winner',
        'description': 'Win a game',
        'points': 50
    },
    'five_games': {
        'name': 'Five Games',
        'description': 'Play 5 games',
        'points': 25
    }
}
