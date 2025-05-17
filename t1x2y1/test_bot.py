import os
import logging
from dotenv import load_dotenv
from telegram import Bot
from db.db import init_db, SessionLocal
from db.models import Room
import asyncio

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_database():
    """Test database connection and operations"""
    try:
        # Initialize database
        init_db()
        db = SessionLocal()
        
        # Test room creation
        test_room = Room(
            room_code="TEST123",
            owner_id=12345,
            name="Test Room",
            status="waiting"
        )
        db.add(test_room)
        db.commit()
        
        # Test room query
        room = db.query(Room).filter(Room.room_code == "TEST123").first()
        if room:
            logger.info("✅ Database test passed")
        else:
            logger.error("❌ Database test failed")
            
        # Cleanup
        db.delete(room)
        db.commit()
        
    except Exception as e:
        logger.error(f"❌ Database error: {str(e)}")
    finally:
        db.close()

async def test_bot_token():
    """Test bot token and basic functionality"""
    try:
        # Load environment
        load_dotenv()
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not token:
            logger.error("❌ No bot token found")
            return
            
        # Test bot connection
        bot = Bot(token)
        bot_info = await bot.get_me()
        
        if bot_info:
            logger.info(f"✅ Bot connected: @{bot_info.username}")
        else:
            logger.error("❌ Failed to connect to bot")
            
    except Exception as e:
        logger.error(f"❌ Bot token test failed: {str(e)}")

async def main():
    """Run all tests"""
    logger.info("Starting bot tests...")
    
    # Test database
    await test_database()
    
    # Test bot token
    await test_bot_token()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    asyncio.run(main())
