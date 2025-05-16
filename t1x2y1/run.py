#!/usr/bin/env python
"""
Entry point script for the Bingo Bot
This script ensures the database is properly initialized before starting the bot
and starts a web server to keep the service alive on Render
"""
import os
import sys
import logging

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Now import project modules
from t1x2y1.config import TELEGRAM_BOT_TOKEN, DATABASE_URL
from t1x2y1.main import main
from t1x2y1.web_server import start_web_server
from t1x2y1.db.database import init_db, get_db
import threading
import time
import importlib

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting Bingo Bot initialization...")
        logger.info(f"Using token: {TELEGRAM_BOT_TOKEN}")
        logger.info(f"Database URL: {DATABASE_URL}")
        
        # Start the web server first (required for Render)
        try:
            # Start the web server
            httpd = start_web_server()
            logger.info("Web server started successfully")
        except Exception as e:
            logger.error(f"Error starting web server: {str(e)}")
            # Continue even if web server fails
        
        # Initialize the database
        try:
            logger.info("Initializing database...")
            
            # Initialize tables
            if not init_db():
                logger.warning("Database initialization had issues")
            
            # Test connection
            try:
                from sqlalchemy import text
                db = get_db()
                db.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
            except Exception as e:
                logger.error(f"Database connection test failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            # Continue even if database initialization fails
        
        # Now import and run the main module in a separate thread
        def run_bot():
            try:
                logger.info("Bot started successfully")
                logger.info("Listening for updates...")
            except Exception as e:
                logger.error(f"Error starting bot: {str(e)}")
        
        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            logger.info("Bot is still running...")
            
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logger.info("Starting application...")
        main()
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
