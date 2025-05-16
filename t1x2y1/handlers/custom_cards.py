from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from custom_cards.card_builder import card_builder
from utils.ui import create_card_builder_keyboard

async def show_card_builder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show card builder interface"""
    user_id = update.effective_user.id
    
    # Get user's cards
    cards = card_builder.get_user_cards(user_id)
    
    # Create card builder keyboard
    keyboard = create_card_builder_keyboard()
    
    # Format message
    message = "Custom Card Builder\n\n"
    if cards:
        message += "Your Cards:\n"
        for card in cards:
            message += f"• Card {card['id']}\n"
            message += f"  Created: {card['created_at']}\n\n"
    else:
        message += "No custom cards yet\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def create_custom_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle custom card creation"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get numbers from callback data
    numbers = context.user_data.get('card_numbers', [])
    if len(numbers) != 25:
        await query.answer(text="Please select exactly 25 numbers!", show_alert=True)
        return
    
    # Create card
    success = card_builder.create_custom_card(user_id, numbers)
    
    if success:
        await query.answer(text="Custom card created successfully!")
    else:
        await query.answer(text="Failed to create card. Check your coins and card limits.", show_alert=True)
    
    # Clear numbers from context
    context.user_data.pop('card_numbers', None)
    
    # Refresh card builder interface
    await show_card_builder(query.message, context)

async def delete_custom_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle custom card deletion"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get card ID from callback data
    card_id = int(query.data.split('_')[1])
    
    # Delete card
    success = card_builder.delete_card(user_id, card_id)
    
    if success:
        await query.answer(text="Card deleted successfully!")
    else:
        await query.answer(text="Failed to delete card.", show_alert=True)
    
    # Refresh card builder interface
    await show_card_builder(query.message, context)

# Card builder keyboard layout
def create_card_builder_keyboard() -> InlineKeyboardMarkup:
    """Create card builder interface keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Create New Card", callback_data="create_card"),
            InlineKeyboardButton("Delete Card", callback_data="delete_card")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
