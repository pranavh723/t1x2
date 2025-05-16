#!/usr/bin/env python
"""
Entry point script for the Bingo Bot
This script ensures the database is properly initialized before starting the bot
"""
import os
import sys
import logging
import importlib

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting Bingo Bot initialization...")
        
        # Add the project root to the Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        
        # First initialize the database
        try:
            from t1x2y1.db.database import init_db
            logger.info("Initializing database...")
            success = init_db()
            if not success:
                logger.warning("Database initialization had issues, but continuing...")
        except ImportError:
            try:
                from db.database import init_db
                logger.info("Initializing database...")
                success = init_db()
                if not success:
                    logger.warning("Database initialization had issues, but continuing...")
            except ImportError:
                logger.error("Could not import database module")
                return 1
        
        # Now import and run the main module
        try:
            import t1x2y1.main
            logger.info("Bot started successfully")
            return 0
        except ImportError:
            try:
                import main
                logger.info("Bot started successfully")
                return 0
            except ImportError:
                logger.error("Could not import main module")
                return 1
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
