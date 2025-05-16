from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User, Room, Game
from db.db import SessionLocal
from utils.game_utils import GameManager
from anti_cheat.middleware import anti_cheat_middleware

class Tournament:
    def __init__(self):
        self.tournament_types = {
            '4_players': 4,
            '8_players': 8,
            '16_players': 16
        }
        self.brackets = {}
        self.current_tournaments = {}
    
    def create_tournament(self, creator_id: int, tournament_type: str) -> str:
        """Create a new tournament"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == creator_id).first()
            if not user:
                return None
            
            # Validate tournament type
            if tournament_type not in self.tournament_types:
                return None
            
            # Create tournament room
            room_code = self._generate_unique_code()
            max_players = self.tournament_types[tournament_type]
            
            # Create room in database
            room = Room(
                room_code=room_code,
                owner_id=user.id,
                name=f"Tournament {tournament_type}",
                is_private=False,
                max_players=max_players,
                call_type="auto",
                status="waiting"
            )
            db.add(room)
            db.commit()
            
            # Initialize tournament data
            self.current_tournaments[room_code] = {
                'creator_id': creator_id,
                'type': tournament_type,
                'status': 'waiting',
                'players': [creator_id],
                'start_time': None,
                'games': []
            }
            
            return room_code
    
    def join_tournament(self, user_id: int, tournament_code: str) -> bool:
        """Join a tournament"""
        if tournament_code not in self.current_tournaments:
            return False
            
        tournament = self.current_tournaments[tournament_code]
        max_players = self.tournament_types[tournament['type']]
        
        # Check if tournament is full
        if len(tournament['players']) >= max_players:
            return False
            
        # Check if user is already in tournament
        if user_id in tournament['players']:
            return False
            
        # Add user to tournament
        tournament['players'].append(user_id)
        return True
    
    def start_tournament(self, tournament_code: str) -> bool:
        """Start the tournament"""
        if tournament_code not in self.current_tournaments:
            return False
            
        tournament = self.current_tournaments[tournament_code]
        max_players = self.tournament_types[tournament['type']]
        
        # Check if tournament is full
        if len(tournament['players']) < max_players:
            return False
            
        # Create initial games
        games = self._create_initial_games(tournament['players'])
        tournament['games'] = games
        tournament['status'] = 'active'
        tournament['start_time'] = datetime.now()
        
        return True
    
    def _create_initial_games(self, players: List[int]) -> List[Dict]:
        """Create initial games for the tournament"""
        games = []
        for i in range(0, len(players), 2):
            game = {
                'players': [players[i], players[i+1]],
                'winner': None,
                'status': 'waiting'
            }
            games.append(game)
        return games
    
    def _generate_unique_code(self) -> str:
        """Generate unique tournament code"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.current_tournaments:
                return code
    
    def get_tournament_status(self, tournament_code: str) -> Dict:
        """Get tournament status"""
        if tournament_code not in self.current_tournaments:
            return None
            
        return self.current_tournaments[tournament_code]
    
    def update_game_result(self, tournament_code: str, game_index: int, winner_id: int) -> bool:
        """Update game result and progress tournament"""
        if tournament_code not in self.current_tournaments:
            return False
            
        tournament = self.current_tournaments[tournament_code]
        if game_index >= len(tournament['games']):
            return False
            
        game = tournament['games'][game_index]
        if game['winner'] is not None:
            return False
            
        # Update game result
        game['winner'] = winner_id
        game['status'] = 'completed'
        
        # Check if tournament is complete
        if all(g['status'] == 'completed' for g in tournament['games']):
            self._determine_final_winner(tournament_code)
            
        return True
    
    def _determine_final_winner(self, tournament_code: str) -> None:
        """Determine the final tournament winner"""
        tournament = self.current_tournaments[tournament_code]
        winners = [g['winner'] for g in tournament['games']]
        
        # If it's a final game (4-player tournament)
        if len(winners) == 1:
            tournament['status'] = 'completed'
            tournament['final_winner'] = winners[0]
            self._award_tournament_rewards(tournament_code)
            
        # For larger tournaments, create next round
        elif len(winners) > 1:
            next_games = self._create_initial_games(winners)
            tournament['games'] = next_games
            
    def _award_tournament_rewards(self, tournament_code: str) -> None:
        """Award rewards to tournament winner"""
        tournament = self.current_tournaments[tournament_code]
        winner_id = tournament['final_winner']
        
        # Calculate rewards based on tournament type
        tournament_type = tournament['type']
        rewards = {
            '4_players': {'xp': 100, 'coins': 50},
            '8_players': {'xp': 200, 'coins': 100},
            '16_players': {'xp': 300, 'coins': 150}
        }
        
        # Award rewards
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == winner_id).first()
            if user:
                user.xp += rewards[tournament_type]['xp']
                user.coins += rewards[tournament_type]['coins']
                db.commit()
    
    def get_tournament_bracket(self, tournament_code: str) -> Dict:
        """Get tournament bracket information"""
        if tournament_code not in self.current_tournaments:
            return None
            
        tournament = self.current_tournaments[tournament_code]
        bracket = {
            'type': tournament['type'],
            'status': tournament['status'],
            'games': tournament['games'],
            'final_winner': tournament.get('final_winner')
        }
        return bracket

tournament_system = Tournament()
