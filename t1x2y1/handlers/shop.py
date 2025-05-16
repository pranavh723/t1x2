from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from rewards.coin_system import coin_system
from utils.ui import create_shop_keyboard

async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the shop interface"""
    user_id = update.effective_user.id
    
    # Get shop items and user coins
    items = coin_system.get_shop_items()
    user_coins = coin_system.get_user_coins(user_id)
    
    # Create shop keyboard
    keyboard = create_shop_keyboard(items, user_coins)
    
    await update.message.reply_text(
        f"Welcome to the Shop! 🏪\n\n"
        f"Your Coins: {user_coins} 🪙\n\n"
        "Select an item to purchase:",
        reply_markup=keyboard
    )

async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle item purchase"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get item from callback data
    item = query.data.split('_')[1]
    
    # Try to purchase item
    success = coin_system.purchase_item(user_id, item)
    
    if success:
        await query.answer(text=f"Successfully purchased {item}!")
    else:
        await query.answer(text="Not enough coins!", show_alert=True)
    
    # Refresh shop interface
    await show_shop(query.message, context)

# Shop keyboard layout
def create_shop_keyboard(items: Dict, user_coins: int) -> InlineKeyboardMarkup:
    """Create shop interface keyboard"""
    keyboard = []
    
    # Add shop items
    for item, price in items.items():
        if user_coins >= price:
            button = InlineKeyboardButton(
                f"{item} ({price} 🪙)",
                callback_data=f"buy_{item}"
            )
        else:
            button = InlineKeyboardButton(
                f"{item} ({price} 🪙) 🔒",
                callback_data=f"locked_{item}"
            )
        keyboard.append([button])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("Back", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(keyboard)
