import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hardcoded configuration values
TELEGRAM_BOT_TOKEN = "7662693814:AAH48vJMmVqzyP0v3OmmwzqTyaMloNHFAec"
OWNER_ID = 6985505204
ADMIN_ID = 6985505204
ENV = "production"

# Bot support and channel links
BOT_SUPPORT_LINK = "https://t.me/bingobot_support"
BOT_CHANNEL_LINK = "https://t.me/Bot_SOURCEC"

# Database configuration
DATABASE_URL = "sqlite:///bingo.db"

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
