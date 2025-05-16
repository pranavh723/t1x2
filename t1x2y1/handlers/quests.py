from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from quests.quest_system import quest_system
from utils.ui import create_quests_keyboard

async def show_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the quests interface"""
    user_id = update.effective_user.id
    
    # Get quest status
    quest_status = quest_system.get_quest_status(user_id)
    
    # Format quests message
    message = "quests\n\nDaily quests:\n"
    for quest, data in quest_status['daily'].items():
        progress = data['progress']
        target = data['target']
        message += f"• {quest}: {progress}/{target}\n"
        message += f"  XP: {data['reward']['xp']}\n"
        message += f"  Coins: {data['reward']['coins']} 🪙\n\n"
    
    message += "\nWeekly quests:\n"
    for quest, data in quest_status['weekly'].items():
        progress = data['progress']
        target = data['target']
        message += f"• {quest}: {progress}/{target}\n"
        message += f"  XP: {data['reward']['xp']}\n"
        message += f"  Coins: {data['reward']['coins']} 🪙\n\n"
    
    # Create quests keyboard
    keyboard = create_quests_keyboard()
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def handle_quest_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle quest-related actions"""
    query = update.callback_query
    action = query.data.split('_')[1]
    
    if action == 'reset':
        await query.answer(text="Quests will reset automatically at midnight!", show_alert=True)
    elif action == 'help':
        await query.answer(text="Complete quests to earn XP and coins!", show_alert=True)
    
    # Refresh quests interface
    await show_quests(query.message, context)

# Quests keyboard layout
def create_quests_keyboard() -> InlineKeyboardMarkup:
    """Create quests interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("", callback_data="quest_reset"),
            InlineKeyboardButton("", callback_data="quest_help")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
