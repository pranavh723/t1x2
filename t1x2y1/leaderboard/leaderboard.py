from typing import List, Dict, Tuple
from db.models import User, Game
from db.db import SessionLocal
from datetime import datetime, timedelta

class Leaderboard:
    def __init__(self):
        self.leaderboard_types = {
            'global': self.get_global_leaderboard,
            'daily': self.get_daily_leaderboard,
            'weekly': self.get_weekly_leaderboard,
            'friends': self.get_friends_leaderboard
        }
    
    def get_global_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get global leaderboard by XP"""
        with SessionLocal() as db:
            users = db.query(User).order_by(User.xp.desc()).limit(limit).all()
            return self._format_leaderboard(users)
    
    def get_daily_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get daily leaderboard by wins"""
        today = datetime.now().date()
        with SessionLocal() as db:
            users = db.query(User).filter(
                Game.winner_id == User.id,
                Game.start_time >= today
            ).group_by(User.id).order_by(Game.start_time.desc()).limit(limit).all()
            return self._format_leaderboard(users)
    
    def get_weekly_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get weekly leaderboard by XP gains"""
        week_start = datetime.now() - timedelta(days=7)
        with SessionLocal() as db:
            users = db.query(User).filter(
                User.last_seen >= week_start
            ).order_by(User.xp.desc()).limit(limit).all()
            return self._format_leaderboard(users)
    
    def get_friends_leaderboard(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get leaderboard for user's friends"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
            
            # Get user's friends (stored in items['friends'])
            friends = user.items.get('friends', [])
            if not friends:
                return []
            
            # Get friends' data
            friends_data = db.query(User).filter(
                User.id.in_(friends)
            ).order_by(User.xp.desc()).limit(limit).all()
            
            return self._format_leaderboard(friends_data)
    
    def _format_leaderboard(self, users: List[User]) -> List[Dict]:
        """Format leaderboard data"""
        leaderboard = []
        for user in users:
            leaderboard.append({
                'rank': len(leaderboard) + 1,
                'username': user.username,
                'xp': user.xp,
                'coins': user.coins,
                'streak': user.streak,
                'last_seen': user.last_seen
            })
        return leaderboard
    
    def get_user_rank(self, user_id: int) -> Tuple[int, Dict]:
        """Get user's rank in global leaderboard"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return (-1, None)
            
            # Get user's rank
            rank = db.query(User).filter(User.xp > user.xp).count() + 1
            
            return (rank, {
                'username': user.username,
                'xp': user.xp,
                'coins': user.coins,
                'streak': user.streak
            })
    
    def update_leaderboard(self, user_id: int, action: str, amount: int = None) -> None:
        """Update leaderboard stats for a user"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            if action == 'win':
                user.wins = user.wins + 1 if user.wins else 1
            elif action == 'xp':
                user.xp += amount if amount else 0
            elif action == 'coins':
                user.coins += amount if amount else 0
            
            user.last_seen = datetime.now()
            db.commit()

leaderboard = Leaderboard()
