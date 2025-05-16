from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.ui import create_main_menu_keyboard

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    
    # Create main menu keyboard
    keyboard = create_main_menu_keyboard()
    
    # Add support and source links
    support_keyboard = [
        [
            InlineKeyboardButton("Support", url="https://t.me/bingobot_support"),
            InlineKeyboardButton("Source", url="https://t.me/Bot_SOURCEC")
        ]
    ]
    support_markup = InlineKeyboardMarkup(support_keyboard)
    
    # Send welcome message
    await update.message.reply_text(
        f"Welcome to Bingo Bot, {user.first_name}!\n"
        "Play Bingo with friends or against AI!\n\n"
        "Use the buttons below to get started.",
        reply_markup=keyboard
    )
    
    # Send support and source links
    await update.message.reply_text(
        "Need help or want to see the source code?",
        reply_markup=support_markup
    )

# Main menu keyboard layout
def create_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎮 Start Game", callback_data="start_game"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("quests", callback_data="quests"),
            InlineKeyboardButton("shop", callback_data="shop")
        ],
        [
            InlineKeyboardButton("ℹ️ Support", callback_data="support"),
            InlineKeyboardButton("🔔 Updates", callback_data="updates")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
