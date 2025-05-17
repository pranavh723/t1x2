from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from events.event_system import event_system
from utils.ui import create_events_keyboard

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show events interface"""
    user_id = update.effective_user.id
    
    # Get current events
    events = event_system.get_current_events()
    
    # Create events keyboard
    keyboard = create_events_keyboard()
    
    # Format events message
    message = "Current Events\n\n"
    if events:
        for event in events:
            message += f"• {event['name']}\n"
            message += f"  Ends: {event['end_time']}\n"
            message += f"  XP: {event['reward']['xp']}\n"
            message += f"  Coins: {event['reward']['coins']} 🪙\n\n"
    else:
        message += "No active events\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def claim_event_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle event reward claiming"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get event name from callback data
    event_name = query.data.split('_')[1]
    
    # Claim reward
    success = event_system.get_event_rewards(user_id, event_name)
    
    if success:
        await query.answer(text="Reward claimed successfully!")
    else:
        await query.answer(text="Event has ended or reward already claimed.", show_alert=True)
    
    # Refresh events interface
    await show_events(query.message, context)

# Events keyboard layout
def create_events_keyboard() -> InlineKeyboardMarkup:
    """Create events interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Claim Rewards", callback_data="claim_rewards"),
            InlineKeyboardButton("Event Info", callback_data="event_info")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
