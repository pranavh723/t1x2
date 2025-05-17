from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from social.social_system import social_system
from utils.ui import create_social_keyboard

async def show_social(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show social interface"""
    user_id = update.effective_user.id
    
    # Get user's friends
    friends = social_system.get_friends(user_id)
    
    # Create social keyboard
    keyboard = create_social_keyboard()
    
    # Format friends message
    message = "Social\n\nFriends:\n"
    if friends:
        for friend in friends:
            message += f"• {friend['username']}\n"
            message += f"  XP: {friend['xp']}\n"
            message += f"  Coins: {friend['coins']} 🪙\n\n"
    else:
        message += "No friends yet\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def send_friend_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle friend request sending"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get friend ID from callback data
    friend_id = int(query.data.split('_')[1])
    
    # Send friend request
    success = social_system.send_friend_request(user_id, friend_id)
    
    if success:
        await query.answer(text="Friend request sent!")
    else:
        await query.answer(text="Failed to send friend request.", show_alert=True)
    
    # Refresh social interface
    await show_social(query.message, context)

async def accept_friend_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle friend request acceptance"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get sender ID from callback data
    sender_id = int(query.data.split('_')[1])
    
    # Accept friend request
    success = social_system.accept_friend_request(user_id, sender_id)
    
    if success:
        await query.answer(text="Friend request accepted!")
    else:
        await query.answer(text="Failed to accept friend request.", show_alert=True)
    
    # Refresh social interface
    await show_social(query.message, context)

# Social keyboard layout
def create_social_keyboard() -> InlineKeyboardMarkup:
    """Create social interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Add Friend", callback_data="add_friend"),
            InlineKeyboardButton("View Friends", callback_data="view_friends")
        ],
        [
            InlineKeyboardButton("Pending Requests", callback_data="pending_requests")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
