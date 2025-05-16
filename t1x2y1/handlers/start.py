from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.models import User
from db.db import SessionLocal

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    
    # Create database session
    db = SessionLocal()
    try:
        # Check if user exists, if not create new user
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(new_user)
            db.commit()
    finally:
        db.close()

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
            InlineKeyboardButton("🎮 Start Game", callback_data="create_room"),
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
