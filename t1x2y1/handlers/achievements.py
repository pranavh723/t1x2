from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from achievements.achievement_system import achievement_system
from utils.ui import create_achievements_keyboard

async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show achievements interface"""
    user_id = update.effective_user.id
    
    # Get user's achievements
    achievements = achievement_system.get_user_achievements(user_id)
    all_achievements = achievement_system.get_all_achievements()
    
    # Create achievements keyboard
    keyboard = create_achievements_keyboard()
    
    # Format achievements message
    message = "Achievements\n\nCompleted:\n"
    for name, data in achievements.items():
        if data['completed']:
            message += f"• {data['description']}\n"
            message += f"  Progress: {data['progress']}/{data['target']}\n\n"
    
    message += "\nIn Progress:\n"
    for name, data in achievements.items():
        if not data['completed']:
            message += f"• {data['description']}\n"
            message += f"  Progress: {data['progress']}/{data['target']}\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def show_achievement_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed information about an achievement"""
    query = update.callback_query
    achievement_name = query.data.split('_')[1]
    
    # Get achievement info
    achievement = achievement_system.get_achievement_info(achievement_name)
    
    if achievement:
        message = f"{achievement['description']}\n\n"
        message += f"XP Reward: {achievement['xp_reward']}\n"
        message += f"Coins Reward: {achievement['coin_reward']} 🪙\n"
        message += f"Target: {achievement['target']}\n"
        
        await query.answer()
        await query.message.reply_text(text=message)
    else:
        await query.answer(text="Achievement not found", show_alert=True)
    
    # Refresh achievements interface
    await show_achievements(query.message, context)

# Achievements keyboard layout
def create_achievements_keyboard() -> InlineKeyboardMarkup:
    """Create achievements interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("View Details", callback_data="view_details"),
            InlineKeyboardButton("Refresh", callback_data="refresh_achievements")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
