from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from t1x2y1.config import OWNER_ID, ADMIN_ID
from t1x2y1.db.database import SessionLocal
from t1x2y1.db.models import User, Room, Game, Maintenance
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
from typing import Optional

logger = logging.getLogger(__name__)

# Admin commands
ADMIN_COMMANDS = {
    'stats': '📊 Show bot statistics',
    'maintenance': '🔧 Toggle maintenance mode',
    'ban': '🔒 Ban a user',
    'unban': '🔓 Unban a user',
    'broadcast': '📢 Broadcast message',
    'reset': '🔄 Reset user data'
}

async def create_admin_keyboard():
    """Create admin menu keyboard"""
    keyboard = []
    for cmd, desc in ADMIN_COMMANDS.items():
        keyboard.append([InlineKeyboardButton(desc, callback_data=f"admin_{cmd}")])
    return InlineKeyboardMarkup(keyboard)

def create_admin_handler():
    """Create admin command handlers"""
    return CommandHandler("admin", admin_menu)

def create_admin_callback_handler():
    """Create callback query handler for admin menu"""
    return CallbackQueryHandler(handle_admin_callback, pattern="^admin_")

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin menu"""
    user_id = update.effective_user.id
    if user_id not in [OWNER_ID, ADMIN_ID]:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    keyboard = await create_admin_keyboard()
    await update.message.reply_text("Admin Menu:", reply_markup=keyboard)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin menu callbacks"""
    query = update.callback_query
    if query.from_user.id not in [OWNER_ID, ADMIN_ID]:
        await query.answer("Unauthorized!", show_alert=True)
        return

    await query.answer()

    try:
        action = query.data.split('_')[1]
        if action == "maintenance":
            await toggle_maintenance(query)
        elif action == "stats":
            await show_stats(query)
        elif action == "ban":
            await ban_user(query)
        elif action == "unban":
            await unban_user(query)
        elif action == "broadcast":
            await broadcast_message(query)
        elif action == "reset":
            await reset_user(query)
    except Exception as e:
        logger.error(f"Error handling admin callback: {str(e)}")
        await query.message.reply_text("An error occurred while processing your request.")

async def toggle_maintenance(query: Update) -> None:
    """Toggle maintenance mode"""
    try:
        with SessionLocal() as db:
            maintenance = db.query(Maintenance).first()
            if not maintenance:
                maintenance = Maintenance()
                db.add(maintenance)
            
            maintenance.enabled = not maintenance.enabled
            maintenance.updated_at = datetime.utcnow()
            maintenance.message = "Bot maintenance is in progress. Please try again later."
            db.commit()

        if maintenance.enabled:
            await query.message.reply_text("✅ Maintenance mode enabled.")
        else:
            await query.message.reply_text("✅ Maintenance mode disabled.")
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {str(e)}")
        await query.message.reply_text("❌ Failed to toggle maintenance mode.")

async def show_stats(query: Update) -> None:
    """Show bot statistics"""
    try:
        with SessionLocal() as db:
            user_count = db.query(User).count()
            active_users = db.query(User).filter(User.last_seen > datetime.utcnow() - timedelta(days=7)).count()
            room_count = db.query(Room).count()
            game_count = db.query(Game).count()
            
            # Get top players by XP
            top_players = db.query(User).order_by(User.xp.desc()).limit(5).all()
            
            stats = f"""
📊 Bot Statistics:

👥 Users:
• Total: {user_count}
• Active (7d): {active_users}

🎮 Games:
• Total Rooms: {room_count}
• Total Games: {game_count}

🏆 Top Players:
"""
            
            for i, player in enumerate(top_players, 1):
                stats += f"\n{i}. {player.first_name} ({player.xp} XP)"
                
        await query.message.reply_text(stats)
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        await query.message.reply_text("❌ Failed to fetch statistics.")

async def ban_user(query: Update) -> None:
    """Ban a user"""
    try:
        await query.message.reply_text("Please provide the user ID to ban:")
        
        # Wait for user input
        response = await query.message.bot.wait_for(
            "message",
            timeout=30,
            check=lambda m: m.from_user.id == query.from_user.id
        )
        
        user_id = int(response.text)
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await query.message.reply_text("❌ User not found!")
                return
                
            user.banned = True
            user.ban_reason = "Banned by admin"
            db.commit()
            
        await query.message.reply_text(f"✅ User {user_id} has been banned.")
    except ValueError:
        await query.message.reply_text("❌ Invalid user ID.")
    except Exception as e:
        logger.error(f"Error in ban_user: {str(e)}")
        await query.message.reply_text("❌ Failed to ban user.")
        await query.message.reply_text("An error occurred.")

async def unban_user(query: Update) -> None:
    """Unban a user"""
    try:
        await query.message.reply_text("Please provide the user ID to unban.")
    except Exception as e:
        logger.error(f"Error in unban_user: {str(e)}")
        await query.message.reply_text("An error occurred.")
        total_games = db.query(Game).count()
        completed_games = db.query(Game).filter(Game.winner_id.isnot(None)).count()
        
        # Economy stats
        total_coins = db.query(User).with_entities(func.sum(User.coins)).scalar() or 0
        total_xp = db.query(User).with_entities(func.sum(User.xp)).scalar() or 0
        
        # Top players
        top_players = db.query(User).order_by(User.xp.desc()).limit(3).all()
        
        message = "📊 Bot Statistics\n\n"
        message += f"👥 Users:\n"
        message += f"  Total: {total_users}\n"
        message += f"  Active: {active_users}\n\n"
        
        message += f"🎮 Games:\n"
        message += f"  Total: {total_games}\n"
        message += f"  Completed: {completed_games}\n\n"
        
        message += f"💰 Economy:\n"
        message += f"  Total Coins: {total_coins} 🪙\n"
        message += f"  Total XP: {total_xp}\n\n"
        
        message += f"🏆 Top Players:\n"
        for i, player in enumerate(top_players, 1):
            message += f"  {i}. {player.username} - {player.xp} XP\n"
        
        await update.message.reply_text(message)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    """Broadcast message to all users with options"""
    if not args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return
        
    message = " ".join(args)
    with SessionLocal() as db:
        users = db.query(User).filter(User.banned == False).all()
        total_users = len(users)
        
        # Send broadcast with progress
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📢 Broadcast Message:\n\n{message}"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user.telegram_id}: {str(e)}")
                failed_count += 1
            
            # Update progress every 10 users
            if sent_count % 10 == 0:
                progress = f"Broadcasting... {sent_count}/{total_users} sent"
                await update.message.reply_text(progress)
        
        # Send final report
        report = f"Broadcast Complete:\n"
        report += f"Total users: {total_users}\n"
        report += f"Successfully sent: {sent_count}\n"
        report += f"Failed: {failed_count}\n"
        
        await update.message.reply_text(report)

async def reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list) -> None:
    """Reset user's data with options"""
    if not args:
        await update.message.reply_text("Please provide a user ID to reset.")
        return
        
    try:
        user_id = int(args[0])
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("User not found.")
                return
                
            # Reset options
            reset_all = "all" in args
            reset_economy = "economy" in args
            reset_progress = "progress" in args
            reset_inventory = "inventory" in args
            
            # Reset based on options
            if reset_all or reset_economy:
                user.coins = 0
                user.xp = 0
                user.streak = 0
            
            if reset_all or reset_progress:
                user.items = {}
                user.achievements = {}
                user.quests = {}
            
            if reset_all or reset_inventory:
                user.inventory = {}
                user.cards = []
            
            db.commit()
            
            await update.message.reply_text(f"User {user_id} has been reset.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
