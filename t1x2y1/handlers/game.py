from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from db.models import Room, Game, User
from db.db import SessionLocal
import random
from datetime import datetime

# Game keyboard layout
def create_game_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Game", callback_data="join_game")]
    ])

async def create_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new game room"""
    user = update.effective_user
    
    # Create database session
    db = SessionLocal()
    try:
        # Create new room
        room = Room(
            room_code=f"ROOM_{random.randint(10000, 99999)}",
            owner_id=user.id,
            name=f"Room by {user.first_name}",
            status=RoomStatus.WAITING
        )
        db.add(room)
        db.commit()
        
        keyboard = [
            [InlineKeyboardButton("Join Game", callback_data=f"join_game_{room.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Created a new game room!\n"
            f"Room Code: {room.room_code}\n"
            "Waiting for players to join...",
            reply_markup=reply_markup
        )
    finally:
        db.close()

async def join_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Join an existing game room"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await query.answer("Room not found!", show_alert=True)
            return
            
        if room.status != RoomStatus.WAITING:
            await query.answer("Game has already started!", show_alert=True)
            return
            
        # Add player to room
        room.players.append(query.from_user.id)
        db.commit()
        
        await query.answer()
        await query.edit_message_text(
            f"{query.from_user.first_name} has joined the game!\n"
            f"Players in room: {len(room.players)}"
        )
    finally:
        db.close()

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the game"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            await query.answer("Room not found!", show_alert=True)
            return
            
        if room.status != RoomStatus.WAITING:
            await query.answer("Game has already started!", show_alert=True)
            return
            
        # Create new game
        game = Game(
            room_id=room.id,
            room_code=room.room_code,
            status=GameStatus.IN_PROGRESS,
            start_time=datetime.utcnow()
        )
        db.add(game)
        
        # Generate cards for each player
        for player_id in room.players:
            card = generate_card()
            card_data = {
                'numbers': card,
                'marked': [False] * 25
            }
            
            new_card = Card(
                user_id=player_id,
                card_data=card_data,
                is_custom=False,
                active_game_id=game.id
            )
            db.add(new_card)
            game.cards.append(new_card)
            
        room.status = RoomStatus.STARTED
        db.commit()
        
        await query.answer()
        await query.edit_message_text(
            "Game is starting!\n"
            "Good luck!\n"
            f"Players: {len(room.players)}\n"
            "Waiting for first number..."
        )
    finally:
        db.close()

async def generate_card() -> list:
    """Generate a random bingo card"""
    numbers = []
    for i in range(5):
        # Generate numbers for each column
        start = i * 15 + 1
        end = (i + 1) * 15
        column = random.sample(range(start, end + 1), 5)
        numbers.extend(column)
    
    # Shuffle the numbers
    random.shuffle(numbers)
    return numbers

async def ai_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI moves in the game"""
    query = update.callback_query
    room_id = int(query.data.split('_')[1])
    
    # Create database session
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_id == room_id).first()
        if not game:
            await query.answer("Game not found!", show_alert=True)
            return
            
        if game.status != GameStatus.IN_PROGRESS:
            await query.answer("Game is not in progress!", show_alert=True)
            return
            
        # Draw a new number
        all_numbers = list(range(1, 76))
        available_numbers = [num for num in all_numbers if num not in game.numbers_drawn]
        
        if not available_numbers:
            await query.answer()
            await query.edit_message_text("All numbers have been drawn!")
            return
            
        new_number = random.choice(available_numbers)
        game.numbers_drawn.append(new_number)
        
        # Check for bingo
        winner = await check_for_bingo(game, db)
        if winner:
            game.status = GameStatus.COMPLETED
            game.winner_id = winner
            game.end_time = datetime.utcnow()
            db.commit()
            
            await query.answer()
            await query.edit_message_text(
                f"BINGO! Player {winner} wins!\n"
                f"Winning number: {new_number}"
            )
            return
            
        await query.answer()
        await query.edit_message_text(
            f"Number drawn: {new_number}\n"
            "Waiting for next move..."
        )
    finally:
        db.close()

async def check_for_bingo(game: Game, db: SessionLocal) -> Optional[int]:
    """Check if any player has bingo"""
    for card in game.cards:
        numbers = card.card_data['numbers']
        marked = card.card_data['marked']
        
        # Check rows
        for i in range(5):
            row = marked[i*5:(i+1)*5]
            if all(row):
                return card.user_id
                
        # Check columns
        for i in range(5):
            column = [marked[i + j*5] for j in range(5)]
            if all(column):
                return card.user_id
                
        # Check diagonals
        diagonal1 = [marked[i*6] for i in range(5)]
        diagonal2 = [marked[i*4] for i in range(4, -1, -1)]
        if all(diagonal1) or all(diagonal2):
            return card.user_id
            
    return None
