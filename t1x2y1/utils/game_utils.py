import random
from typing import List, Dict, Tuple
from datetime import datetime

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
        """Generate a 5x5 bingo card with unique numbers 1-25"""
        numbers = list(range(1, 26))
        random.shuffle(numbers)
        return [numbers[i:i+5] for i in range(0, 25, 5)]
    
    def initialize_game(self):
        """Initialize game by generating cards for all players"""
        for player in self.players:
            card = self.generate_card()
            self.cards[player] = card
            self.marked[player] = [[False]*5 for _ in range(5)]
    
    def call_number(self) -> int:
        """Call a random number that hasn't been called yet"""
        available_numbers = set(range(1, 26)) - set(self.numbers_drawn)
        if not available_numbers:
            return None
        
        self.current_number = random.choice(list(available_numbers))
        self.numbers_drawn.append(self.current_number)
        return self.current_number
    
    def mark_number(self, player_id: int, number: int) -> bool:
        """Mark a number on a player's card if it exists"""
        if player_id not in self.cards:
            return False
        
        card = self.cards[player_id]
        marked = self.marked[player_id]
        
        for i, row in enumerate(card):
            for j, num in enumerate(row):
                if num == number:
                    marked[i][j] = True
                    return True
        return False
    
    def check_bingo(self, player_id: int) -> bool:
        """Check if a player has bingo"""
        if player_id not in self.marked:
            return False
        
        marked = self.marked[player_id]
        
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
    
    def get_card_state(self, player_id: int) -> List[List[Tuple[int, bool]]]:
        """Get player's card with marked/unmarked state"""
        if player_id not in self.cards:
            return []
        
        card = self.cards[player_id]
        marked = self.marked[player_id]
        
        return [[(num, marked[i][j]) for j, num in enumerate(row)]
                for i, row in enumerate(card)]

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
