from telegram import Update
from telegram.ext import ContextTypes
from db.models import Maintenance
from db.db import SessionLocal
from config import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
import logging

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
