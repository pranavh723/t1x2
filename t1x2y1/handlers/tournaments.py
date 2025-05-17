from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tournaments.tournament import tournament_system
from utils.ui import create_tournament_keyboard

async def show_tournaments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show tournament interface"""
    user_id = update.effective_user.id
    
    # Get available tournaments
    tournaments = tournament_system.current_tournaments
    
    # Create tournament keyboard
    keyboard = create_tournament_keyboard()
    
    # Format tournaments message
    message = "Tournaments\n\n"
    if tournaments:
        for code, tournament in tournaments.items():
            if tournament['status'] == 'waiting':
                message += f"• {tournament['type']} Tournament\n"
                message += f"  Players: {len(tournament['players'])}/{tournament['max_players']}\n"
                message += f"  Created by: {tournament['creator_id']}\n\n"
    else:
        message += "No active tournaments\n\n"
    
    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )

async def create_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new tournament"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get tournament type from callback data
    tournament_type = query.data.split('_')[1]
    
    # Create tournament
    tournament_code = tournament_system.create_tournament(user_id, tournament_type)
    
    if tournament_code:
        await query.answer(text=f"Tournament created! Code: {tournament_code}")
    else:
        await query.answer(text="Failed to create tournament", show_alert=True)
    
    # Refresh tournaments interface
    await show_tournaments(query.message, context)

async def join_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Join a tournament"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get tournament code from callback data
    tournament_code = query.data.split('_')[1]
    
    # Join tournament
    success = tournament_system.join_tournament(user_id, tournament_code)
    
    if success:
        await query.answer(text="Joined tournament!")
    else:
        await query.answer(text="Failed to join tournament", show_alert=True)
    
    # Refresh tournaments interface
    await show_tournaments(query.message, context)

# Tournament keyboard layout
def create_tournament_keyboard() -> InlineKeyboardMarkup:
    """Create tournament selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("4 Players", callback_data="create_tournament_4_players"),
            InlineKeyboardButton("8 Players", callback_data="create_tournament_8_players")
        ],
        [
            InlineKeyboardButton("16 Players", callback_data="create_tournament_16_players")
        ],
        [
            InlineKeyboardButton("Back", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
