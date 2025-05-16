import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration constants
OWNER_ID = int(os.getenv('OWNER_ID', 0))
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
