import random
from typing import List, Tuple
from utils.game_utils import BingoGame

class BingoAI:
    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty
        self.card = None
        self.marked = None
        self.numbers_drawn = []
    
    def set_game_state(self, game: BingoGame, player_id: int):
        """Set AI's game state"""
        self.card = game.cards[player_id]
        self.marked = game.marked[player_id]
        self.numbers_drawn = game.numbers_drawn
    
    def make_move(self) -> Tuple[int, int]:
        """Make a move based on difficulty level"""
        if not self.card:
            return None
        
        if self.difficulty == "easy":
            return self._random_move()
        elif self.difficulty == "medium":
            return self._strategic_move()
        else:  # hard
            return self._optimal_move()
    
    def _random_move(self) -> Tuple[int, int]:
        """Choose a random unmarked number"""
        available = [(i, j) for i in range(5) for j in range(5) 
                    if not self.marked[i][j]]
        if not available:
            return None
        return random.choice(available)
    
    def _strategic_move(self) -> Tuple[int, int]:
        """Choose numbers that could complete rows/columns"""
        # Check rows and columns that are close to completion
        best_moves = []
        for i in range(5):
            # Check row
            row_marks = sum(self.marked[i])
            if row_marks >= 3:
                for j in range(5):
                    if not self.marked[i][j]:
                        best_moves.append((i, j))
            
            # Check column
            col_marks = sum(self.marked[row][i] for row in range(5))
            if col_marks >= 3:
                for j in range(5):
                    if not self.marked[j][i]:
                        best_moves.append((j, i))
        
        if best_moves:
            return random.choice(best_moves)
        return self._random_move()
    
    def _optimal_move(self) -> Tuple[int, int]:
        """Choose moves that maximize winning chances"""
        # Check all possible winning lines
        best_moves = []
        max_score = 0
        
        # Check rows
        for i in range(5):
            row_marks = sum(self.marked[i])
            score = 5 - row_marks
            if score > max_score:
                max_score = score
                best_moves = [(i, j) for j in range(5) if not self.marked[i][j]]
        
        # Check columns
        for j in range(5):
            col_marks = sum(self.marked[row][j] for row in range(5))
            score = 5 - col_marks
            if score > max_score:
                max_score = score
                best_moves = [(i, j) for i in range(5) if not self.marked[i][j]]
        
        # Check diagonals
        main_diag_marks = sum(self.marked[i][i] for i in range(5))
        score = 5 - main_diag_marks
        if score > max_score:
            max_score = score
            best_moves = [(i, i) for i in range(5) if not self.marked[i][i]]
        
        anti_diag_marks = sum(self.marked[i][4-i] for i in range(5))
        score = 5 - anti_diag_marks
        if score > max_score:
            max_score = score
            best_moves = [(i, 4-i) for i in range(5) if not self.marked[i][4-i]]
        
        if best_moves:
            return random.choice(best_moves)
        return self._strategic_move()

class AIManager:
    def __init__(self):
        self.ais = {}
    
    def create_ai(self, room_code: str, difficulty: str = "medium") -> BingoAI:
        """Create an AI player for a room"""
        ai = BingoAI(difficulty)
        self.ais[room_code] = ai
        return ai
    
    def get_ai(self, room_code: str) -> BingoAI:
        """Get AI for a room"""
        return self.ais.get(room_code)
    
    def remove_ai(self, room_code: str):
        """Remove AI from a room"""
        if room_code in self.ais:
            del self.ais[room_code]

ai_manager = AIManager()
