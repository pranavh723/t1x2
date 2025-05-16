from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User, Game
from db.db import SessionLocal

class AnalyticsSystem:
    def __init__(self):
        self.metrics = {
            'daily': {
                'games_played': 0,
                'games_won': 0,
                'numbers_marked': 0,
                'active_users': 0
            },
            'weekly': {
                'games_played': 0,
                'games_won': 0,
                'numbers_marked': 0,
                'active_users': 0
            },
            'monthly': {
                'games_played': 0,
                'games_won': 0,
                'numbers_marked': 0,
                'active_users': 0
            }
        }
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
                
            # Get user's games
            games = db.query(Game).filter(
                Game.players.contains([user_id])
            ).all()
            
            # Calculate stats
            stats = {
                'total_games': len(games),
                'wins': sum(1 for game in games if game.winner_id == user_id),
                'xp': user.xp,
                'coins': user.coins,
                'streak': user.streak,
                'last_seen': user.last_seen,
                'friends': len(user.items.get('friends', []))
            }
            
            return stats
    
    def get_global_stats(self) -> Dict:
        """Get global statistics"""
        with SessionLocal() as db:
            # Get total users
            total_users = db.query(User).count()
            
            # Get active users (last 24 hours)
            active_users = db.query(User).filter(
                User.last_seen >= datetime.now() - timedelta(days=1)
            ).count()
            
            # Get total games
            total_games = db.query(Game).count()
            
            # Get total wins
            total_wins = db.query(Game).filter(Game.winner_id.isnot(None)).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'total_games': total_games,
                'total_wins': total_wins
            }
    
    def get_time_based_stats(self, time_range: str = 'daily') -> Dict:
        """Get statistics for a specific time range"""
        with SessionLocal() as db:
            now = datetime.now()
            
            if time_range == 'daily':
                start_time = now - timedelta(days=1)
            elif time_range == 'weekly':
                start_time = now - timedelta(weeks=1)
            else:  # monthly
                start_time = now - timedelta(days=30)
            
            # Get games in time range
            games = db.query(Game).filter(
                Game.start_time >= start_time
            ).all()
            
            # Calculate stats
            stats = {
                'games_played': len(games),
                'games_won': sum(1 for game in games if game.winner_id is not None),
                'active_users': len(set(p for game in games for p in game.players)),
                'time_range': time_range
            }
            
            return stats
    
    def track_event(self, event_type: str, user_id: int, data: Dict = None) -> None:
        """Track an event for analytics"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
                
            # Update user stats
            user.items['analytics'] = user.items.get('analytics', {})
            user.items['analytics'][event_type] = user.items['analytics'].get(event_type, 0) + 1
            
            db.commit()
    
    def get_user_event_history(self, user_id: int) -> Dict:
        """Get user's event history"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
                
            return user.items.get('analytics', {})
    
    def get_top_players(self, metric: str = 'xp', limit: int = 10) -> List[Dict]:
        """Get top players based on a metric"""
        with SessionLocal() as db:
            users = db.query(User).order_by(getattr(User, metric).desc()).limit(limit).all()
            return [{
                'username': user.username,
                'metric_value': getattr(user, metric),
                'xp': user.xp,
                'coins': user.coins
            } for user in users]

analytics_system = AnalyticsSystem()
