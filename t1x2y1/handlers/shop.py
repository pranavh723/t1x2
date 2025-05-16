from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from db.models import User, Card
from db.db import SessionLocal
import logging
from ratelimit import sleep_and_retry, limits
from functools import wraps
from handlers.room_management import generate_bingo_card

logger = logging.getLogger(__name__)

SHOP_ITEMS = {
    'card_pack': {'name': 'Card Pack', 'price': 50, 'description': 'Get 5 random cards'},
    'xp_boost': {'name': 'XP Boost', 'price': 100, 'description': 'Double XP for next game'},
    'skip_queue': {'name': 'Skip Queue', 'price': 200, 'description': 'Skip to next game immediately'}
}

@sleep_and_retry
@limits(calls=1, period=60)
async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the shop interface"""
    try:
        # Get user data
        user_id = update.effective_user.id
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await update.message.reply_text("Please start a game first!")
            return
            
        # Create shop keyboard
        keyboard = create_shop_keyboard(user.coins)
        
        await update.message.reply_text(
            f"Welcome to the Shop! 🏪\n\n"
            f"Your Coins: {user.coins} 🪙\n\n"
            "Select an item to purchase:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in show_shop: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again later.")
    finally:
        db.close()

async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle item purchase"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get item from callback data
        item = query.data.split('_')[1]
        
        # Process purchase
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                await query.answer("User not found!", show_alert=True)
                return
                
            item_data = SHOP_ITEMS.get(item)
            if not item_data:
                await query.answer("Invalid item!", show_alert=True)
                return
                
            if user.coins < item_data['price']:
                await query.answer("Not enough coins!", show_alert=True)
                return
                
            # Process purchase
            user.coins -= item_data['price']
            
            if item == 'card_pack':
                # Add 5 random cards
                for _ in range(5):
                    card = generate_card()
                    new_card = Card(
                        user_id=user_id,
                        card_data=card,
                        is_custom=False,
                        timestamp=datetime.utcnow()
                    )
                    db.add(new_card)
            elif item == 'xp_boost':
                user.items['xp_boost'] = True
            elif item == 'skip_queue':
                user.items['skip_queue'] = True
                
            db.commit()
            
            await query.answer(text=f"Successfully purchased {item_data['name']}!")
            
            # Refresh shop interface
            keyboard = create_shop_keyboard(user.coins)
            await query.edit_message_text(
                f"Welcome to the Shop! 🏪\n\n"
                f"Your Coins: {user.coins} 🪙\n\n"
                "Select an item to purchase:",
                reply_markup=keyboard
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing purchase: {str(e)}")
            await query.answer("An error occurred during purchase!", show_alert=True)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error in handle_purchase: {str(e)}")
        await query.answer("An unexpected error occurred!", show_alert=True)

def create_shop_keyboard(coins: int) -> InlineKeyboardMarkup:
    """Create shop interface keyboard"""
    keyboard = []
    
    for item, data in SHOP_ITEMS.items():
        if coins >= data['price']:
            button = InlineKeyboardButton(
                f"{data['name']} ({data['price']} 🪙)",
                callback_data=f"buy_{item}"
            )
        else:
            button = InlineKeyboardButton(
                f"{data['name']} ({data['price']} 🪙) 🔒",
                callback_data=f"locked_{item}"
            )
        keyboard.append([button])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("Back", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def generate_card() -> list:
    """Generate a random bingo card"""
    numbers = []
    for i in range(5):
        start = i * 15 + 1
        end = (i + 1) * 15
        column = random.sample(range(start, end + 1), 5)
        numbers.extend(column)
    
    random.shuffle(numbers)
    return numbers
