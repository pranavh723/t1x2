import os
import sys
import logging
from telegram import Update
from telegram.ext import ContextTypes

# Add the project root directory to the Python path for deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import with fallback paths for both local development and deployment
from t1x2y1.db.models import Maintenance
from t1x2y1.db.database import SessionLocal
from t1x2y1.config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
        print("Error: Could not import database modules")
        MAINTENANCE_MODE = False
        MAINTENANCE_MESSAGE = "Bot is currently under maintenance. Please try again later."

# Set up logger
maintenance_logger = logging.getLogger(__name__)

def maintenance_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if bot is in maintenance mode"""
    # First check the config variable
    if MAINTENANCE_MODE:
        maintenance_logger.info("Maintenance mode is enabled in config")
        if update.message:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=MAINTENANCE_MESSAGE
            )
        return True
        
    # Then check the database
    db = SessionLocal()
    try:
        maintenance = db.query(Maintenance).first()
        if maintenance and maintenance.enabled:
            maintenance_logger.info("Maintenance mode is enabled in database")
            if update.message:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=maintenance.message or MAINTENANCE_MESSAGE
                )
            return True
    except Exception as e:
        maintenance_logger.error(f"Error checking maintenance mode: {str(e)}")
    finally:
        db.close()
        
    return False
