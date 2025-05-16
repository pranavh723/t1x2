from telegram import Update
from telegram.ext import ContextTypes
from t1x2y1.db.models import Room, RoomStatus
from t1x2y1.db.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status and diagnostics"""
    try:
        # Check database connection
        db = SessionLocal()
        try:
            # Count active rooms
            active_rooms = db.query(Room).filter(Room.status != RoomStatus.FINISHED).count()
            db.commit()
            db_status = "✅ Connected to DB"
        except Exception as e:
            logger.error(f"DB connection error: {str(e)}")
            db_status = "❌ DB Connection Error"
        finally:
            db.close()

        # Check admin ID
        admin_id = context.bot_data.get('admin_id', 'Not set')
        admin_status = "✅ Admin ID Set" if admin_id else "❌ Admin ID Not Set"

        # Get bot username
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username

        # Check if bot is alive
        alive_status = "✅ Bot is alive"

        # Format status message
        status_message = f"**Bot Status**\n\n"
        status_message += f"Bot Username: @{bot_username}\n"
        status_message += f"{alive_status}\n"
        status_message += f"{db_status}\n"
        status_message += f"Active Rooms: {active_rooms}\n"
        status_message += f"{admin_status}"

        await update.message.reply_text(status_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in status command: {str(e)}")
        await update.message.reply_text("❌ Error checking bot status. Please try again later.")
