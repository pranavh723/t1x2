from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from config import OWNER_ID
from db.db import SessionLocal
from db.models import User, Room, Game, Maintenance
import logging
from datetime import datetime
from sqlalchemy import func

logger = logging.getLogger(__name__)

def create_admin_keyboard():
    """Create admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="admin_maintenance")],
        [InlineKeyboardButton("🔒 Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton("🔓 Unban User", callback_data="admin_unban")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_admin_handler():
    """Create admin command handlers"""
    return CommandHandler("admin", admin_menu)

def create_admin_callback_handler():
    """Create callback query handler for admin menu"""
    return CallbackQueryHandler(handle_admin_callback, pattern="^admin_")

def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin menu"""
    if update.effective_user.id != OWNER_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    keyboard = create_admin_keyboard()
    update.message.reply_text("Admin Menu:", reply_markup=keyboard)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin menu callbacks"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_maintenance":
        await toggle_maintenance(query)
    elif query.data == "admin_stats":
        await show_stats(query)
    elif query.data == "admin_ban":
        await ban_user(query)
    elif query.data == "admin_unban":
        await unban_user(query)

def toggle_maintenance(query: Update) -> None:
    """Toggle maintenance mode"""
    with SessionLocal() as db:
        maintenance = db.query(Maintenance).first()
        if not maintenance:
            maintenance = Maintenance()
            db.add(maintenance)
        maintenance.enabled = not maintenance.enabled
        db.commit()

    if maintenance.enabled:
        query.message.reply_text("Maintenance mode enabled.")
    else:
        query.message.reply_text("Maintenance mode disabled.")

def show_stats(query: Update) -> None:
    """Show bot statistics"""
    with SessionLocal() as db:
        user_count = db.query(User).count()
        room_count = db.query(Room).count()
        game_count = db.query(Game).count()

    stats = f"""
Bot Statistics:
Users: {user_count}
Rooms: {room_count}
Games: {game_count}
"""
    query.message.reply_text(stats)

def ban_user(query: Update) -> None:
    """Ban a user"""
    query.message.reply_text("Please provide the user ID to ban.")

def unban_user(query: Update) -> None:
    """Unban a user"""
    query.message.reply_text("Please provide the user ID to unban.")

async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed bot statistics"""
    with SessionLocal() as db:
        # User stats
        total_users = db.query(User).count()
        active_users = db.query(User).filter(
            User.last_seen >= datetime.now() - timedelta(days=1)
        ).count()
        
        # Game stats
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
