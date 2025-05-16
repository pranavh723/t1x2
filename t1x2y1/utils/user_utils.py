from db.models import User
from db.db import SessionLocal
import logging

# Set up logger
user_logger = logging.getLogger(__name__)

def is_user_banned(user_id: int) -> bool:
    """Check if user is banned"""
    user_logger.info(f"Checking if user {user_id} is banned")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        return user and user.banned
    except Exception as e:
        user_logger.error(f"Error checking if user {user_id} is banned: {str(e)}")
        return False
    finally:
        db.close()
