from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from analytics.analytics_system import analytics_system
from utils.ui import create_analytics_keyboard

async def show_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show analytics interface"""
    user_id = update.effective_user.id
    
    # Get user stats
    user_stats = analytics_system.get_user_stats(user_id)
    
    # Get global stats
    global_stats = analytics_system.get_global_stats()
    
    # Create analytics keyboard
    keyboard = create_analytics_keyboard()
    
    # Format analytics message
    message = "Analytics\n\nYour Stats:\n"
    if user_stats:
        message += f"• Games Played: {user_stats['total_games']}\n"
        message += f"• Wins: {user_stats['wins']}\n"
        message += f"• XP: {user_stats['xp']}\n"
        message += f"• Coins: {user_stats['coins']} 🪙\n"
        message += f"• Friends: {user_stats['friends']}\n\n"
    
    message += "Global Stats:\n"
    message += f"• Total Users: {global_stats['total_users']}\n"
    message += f"• Active Users: {global_stats['active_users']}\n"
    message += f"• Total Games: {global_stats['total_games']}\n"
    message += f"• Total Wins: {global_stats['total_wins']}\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def show_time_based_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show time-based statistics"""
    query = update.callback_query
    time_range = query.data.split('_')[1]
    
    # Get time-based stats
    stats = analytics_system.get_time_based_stats(time_range)
    
    message = f"{stats['time_range'].capitalize()} Stats\n\n"
    message += f"• Games Played: {stats['games_played']}\n"
    message += f"• Games Won: {stats['games_won']}\n"
    message += f"• Active Users: {stats['active_users']}\n\n"
    
    await query.answer()
    await query.message.reply_text(text=message)
    
    # Refresh analytics interface
    await show_analytics(query.message, context)

async def show_top_players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show top players"""
    query = update.callback_query
    metric = query.data.split('_')[1]
    
    # Get top players
    top_players = analytics_system.get_top_players(metric)
    
    message = f"Top Players by {metric}\n\n"
    for i, player in enumerate(top_players, 1):
        message += f"{i}. {player['username']}\n"
        message += f"  {metric}: {player['metric_value']}\n"
        message += f"  XP: {player['xp']}\n"
        message += f"  Coins: {player['coins']} 🪙\n\n"
    
    await query.answer()
    await query.message.reply_text(text=message)
    
    # Refresh analytics interface
    await show_analytics(query.message, context)

# Analytics keyboard layout
def create_analytics_keyboard() -> InlineKeyboardMarkup:
    """Create analytics interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Daily Stats", callback_data="time_stats_daily"),
            InlineKeyboardButton("Weekly Stats", callback_data="time_stats_weekly")
        ],
        [
            InlineKeyboardButton("Monthly Stats", callback_data="time_stats_monthly")
        ],
        [
            InlineKeyboardButton("Top Players", callback_data="top_players_xp")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
