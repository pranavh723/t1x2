import os
import sys
import logging

# Add the project root directory to the Python path for deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import with fallback paths for both local development and deployment
try:
    from t1x2y1.db.models import User
    from t1x2y1.db.database import SessionLocal
except ImportError:
    try:
        from db.models import User
        from db.database import SessionLocal
    except ImportError:
        print("Error: Could not import database modules")

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
