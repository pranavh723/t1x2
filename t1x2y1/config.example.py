import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration values - replace with your own
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
OWNER_ID = 1234567890
ADMIN_ID = 1234567890
ENV = "production"

# Bot support and channel links
BOT_SUPPORT_LINK = "https://t.me/your_support_link"
BOT_CHANNEL_LINK = "https://t.me/your_channel_link"

# Database configuration
DATABASE_URL = "sqlite:///db/bingo_bot.db"

# Maintenance mode
MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "The bot is currently in maintenance mode. Please try again later."

# Rate limiting constants
ONE_MINUTE = 60
FIVE_MINUTES = 300
TEN_MINUTES = 600

# Command rate limits (calls per period)
RATE_LIMITS = {
    'start': (10, ONE_MINUTE),
    'game': (5, FIVE_MINUTES),
    'shop': (20, TEN_MINUTES),
    'default': (30, ONE_MINUTE)
}

# Banned users list
BANNED_USERS = []

# Game configuration
MAX_PLAYERS = 5
MIN_PLAYERS = 2
GAME_TIMEOUT = 600

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