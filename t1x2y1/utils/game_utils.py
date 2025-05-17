import random
import logging
import asyncio
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime
from telegram import InlineKeyboardButton

# Set up logging
game_logger = logging.getLogger(__name__)

# Standalone functions for bingo game
def generate_bingo_card() -> List[List[int]]:
    """Generate a 5x5 bingo card with unique numbers"""
    card = []
    for i in range(5):
        start = i * 15 + 1
        end = (i + 1) * 15
        column = random.sample(range(start, end + 1), 5)
        card.append(column)
    
    # Transpose the card to have rows instead of columns
    return [list(row) for row in zip(*card)]

def format_bingo_card(card: List[List[int]]) -> str:
    """Format a bingo card for display"""
    header = "B   I   N   G   O"
    formatted = [header]
    
    for row in card:
        row_str = " ".join(f"{num:2d}" for num in row)
        formatted.append(row_str)
    
    return "\n".join(formatted)

def create_card_keyboard(card: List[List[int]]):
    """Create an inline keyboard for a bingo card"""
    keyboard = []
    for row in card:
        keyboard_row = []
        for num in row:
            keyboard_row.append(InlineKeyboardButton(str(num), callback_data=f"mark_{num}"))
        keyboard.append(keyboard_row)
    
    # Add bingo button at bottom
    keyboard.append([InlineKeyboardButton("🎯 BINGO!", callback_data="call_bingo")])
    
    return keyboard

def check_bingo_pattern(marked: List[List[bool]]) -> bool:
    """Check if there is a winning pattern in the marked card"""
    # Check rows
    for row in marked:
        if all(row):
            return True
    
    # Check columns
    for col in range(5):
        if all(marked[row][col] for row in range(5)):
            return True
    
    # Check diagonals
    if all(marked[i][i] for i in range(5)):
        return True
    if all(marked[i][4-i] for i in range(5)):
        return True
    
    return False

def generate_random_number(excluded: List[int] = None) -> int:
    """Generate a random number for bingo (1-75) excluding already called numbers"""
    if excluded is None:
        excluded = []
    
    available = [num for num in range(1, 76) if num not in excluded]
    if not available:
        return None
    
    return random.choice(available)

class BingoGame:
    def __init__(self, room_code: str, players: List[int]):
        self.room_code = room_code
        self.players = players
        self.cards = {}
        self.marked = {}
        self.numbers_drawn = []
        self.current_number = None
        self.winner = None
        self.start_time = datetime.now()
        self.status = "active"
        
    def generate_card(self) -> List[List[int]]:
        """Generate a 5x5 bingo card with unique numbers"""
        try:
            numbers = list(range(1, 26))
            random.shuffle(numbers)
            
            # Ensure no duplicate numbers
            card = [numbers[i:i+5] for i in range(0, 25, 5)]
            
            # Validate card
            if not validate_card(card):
                raise ValueError("Generated invalid card")
                
            return card
        except Exception as e:
            game_logger.error(f"Error generating card: {str(e)}")
            return None

    def initialize_game(self):
        """Initialize game by generating cards for all players"""
        for player in self.players:
            card = self.generate_card()
            self.cards[player] = card
            self.marked[player] = [[False]*5 for _ in range(5)]
    
    async def call_number(self) -> int:
        """Call a new number for the game with validation"""
        try:
            if not self.numbers_drawn:
                self.numbers_drawn = []
                
            available_numbers = list(range(1, 26))
            available_numbers = [num for num in available_numbers if num not in self.numbers_drawn]
            
            if not available_numbers:
                game_logger.info("All numbers have been called")
                return None
                
            # Add delay for better UX
            await asyncio.sleep(1)
            
            number = random.choice(available_numbers)
            self.numbers_drawn.append(number)
            self.current_number = number
            return number
        except Exception as e:
            game_logger.error(f"Error calling number: {str(e)}")
            return None
    
    def mark_number(self, player_id: int, number: int) -> bool:
        """Mark a number on the card with validation"""
        try:
            card = self.cards[player_id]
            marked = self.marked[player_id]
            
            if not validate_card(card):
                return False
                
            if number not in range(1, 26):
                return False
                
            # Check if number is on card
            for i, row in enumerate(card):
                if number in row:
                    # Check if already marked
                    if not marked[i][row.index(number)]:
                        marked[i][row.index(number)] = True
                        return True
                    return False
            
            return False
        except Exception as e:
            game_logger.error(f"Error marking number: {str(e)}")
            return False
        
    def check_bingo(self, player_id: int) -> bool:
        """Check if a player has bingo"""
        if player_id not in self.marked:
            return False
        
        card = self.cards[player_id]
        marked = self.marked[player_id]
        
        return check_bingo(card, marked)

def validate_card(card: List[List[int]]) -> bool:
    """Validate a bingo card"""
    try:
        # Check dimensions
        if len(card) != 5:
            return False
            
        for row in card:
            if len(row) != 5:
                return False
                
        # Check for duplicates
        all_numbers = [num for row in card for num in row]
        if len(set(all_numbers)) != len(all_numbers):
            return False
            
        # Check number range
        if not all(1 <= num <= 25 for num in all_numbers):
            return False
            
        return True
    except Exception:
        return False

def check_bingo(card: List[List[int]], marked: List[List[bool]]) -> bool:
    """Check if a player has bingo with validation"""
    try:
        # Check rows
        for row in marked:
            if all(row):
                return True
                
        # Check columns
        for col in range(5):
            if all(marked[row][col] for row in range(5)):
                return True
                
        # Check diagonals
        if all(marked[i][i] for i in range(5)):
            return True
        if all(marked[i][4-i] for i in range(5)):
            return True
            
        return False
    except Exception as e:
        game_logger.error(f"Error checking bingo: {str(e)}")
        return False

class GameManager:
    def __init__(self):
        self.games = {}
        self.rooms = {}
    
    def create_game(self, room_code: str, players: List[int]) -> BingoGame:
        """Create a new game"""
        game = BingoGame(room_code, players)
        game.initialize_game()
        self.games[room_code] = game
        return game
    
    def get_game(self, room_code: str) -> BingoGame:
        """Get game by room code"""
        return self.games.get(room_code)
    
    def end_game(self, room_code: str):
        """End a game"""
        if room_code in self.games:
            self.games[room_code].status = "ended"
            del self.games[room_code]
    
    def create_room(self, room_code: str, owner_id: int, max_players: int = 5):
        """Create a new room"""
        self.rooms[room_code] = {
            'owner_id': owner_id,
            'players': [owner_id],
            'max_players': max_players,
            'status': 'waiting'
        }
    
    def join_room(self, room_code: str, player_id: int) -> bool:
        """Join a room if not full"""
        if room_code not in self.rooms:
            return False
        
        room = self.rooms[room_code]
        if len(room['players']) >= room['max_players']:
            return False
        
        if player_id not in room['players']:
            room['players'].append(player_id)
        return True
    
    def get_room_info(self, room_code: str) -> Dict:
        """Get room information"""
        return self.rooms.get(room_code, {})
    
    def close_room(self, room_code: str):
        """Close a room"""
        if room_code in self.rooms:
            del self.rooms[room_code]
            if room_code in self.games:
                self.end_game(room_code)

game_manager = GameManager()
