#!/usr/bin/env python
"""
Entry point script for the Bingo Bot
This script ensures the database is properly initialized before starting the bot
and starts a web server to keep the service alive on Render
"""
import os
import sys
import logging
import importlib
import threading
import time

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
        project_root = os.path.dirname(current_dir)
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # Start the web server first (required for Render)
        try:
            # Try different import paths
            try:
                from t1x2y1.web_server import start_web_server
            except ImportError:
                logger.error("Could not import web_server module")
                raise
            
            # Start the web server
            httpd = start_web_server()
            logger.info("Web server started successfully")
        except Exception as e:
            logger.error(f"Error starting web server: {str(e)}")
            # Continue even if web server fails
        
        # Initialize the database
        try:
            try:
                from t1x2y1.db.database import init_db
            except ImportError:
                logger.error("Could not import database module")
                raise
            
            logger.info("Initializing database...")
            success = init_db()
            if not success:
                logger.warning("Database initialization had issues, but continuing...")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            # Continue even if database initialization fails
        
        # Now import and run the main module in a separate thread
        def run_bot():
            try:
                try:
                    import t1x2y1.main
                    logger.info("Bot started successfully")
                except ImportError:
                    try:
                        import main
                        logger.info("Bot started successfully")
                    except ImportError:
                        logger.error("Could not import main module")
                        raise
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
    sys.exit(main())
