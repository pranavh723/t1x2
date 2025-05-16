from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User
from db.db import SessionLocal
from rewards.xp_system import xp_system
from rewards.coin_system import coin_system

class AchievementSystem:
    def __init__(self):
        self.achievements = {
            "first_win": {
                "description": "Win your first game",
                "xp_reward": 50,
                "coin_reward": 20,
                "type": "win",
                "target": 1
            },
            "bingo_master": {
                "description": "Win 10 games",
                "xp_reward": 200,
                "coin_reward": 50,
                "type": "win",
                "target": 10
            },
            "number_cruncher": {
                "description": "Mark 100 numbers",
                "xp_reward": 100,
                "coin_reward": 30,
                "type": "mark",
                "target": 100
            },
            "social_butterfly": {
                "description": "Play with 5 different players",
                "xp_reward": 75,
                "coin_reward": 35,
                "type": "unique_players",
                "target": 5
            },
            "tournament_champion": {
                "description": "Win a tournament",
                "xp_reward": 150,
                "coin_reward": 40,
                "type": "tournament_win",
                "target": 1
            }
        }
    
    def check_achievement(self, user_id: int, achievement_type: str, amount: int = 1) -> bool:
        """Check and award achievement if conditions are met"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            achievements = user.items.get('achievements', {})
            
            for achievement_name, achievement in self.achievements.items():
                if achievement['type'] == achievement_type:
                    current = achievements.get(achievement_name, 0)
                    new_total = current + amount
                    
                    if new_total >= achievement['target']:
                        # Award rewards
                        xp_system.award_xp(user_id, achievement_name, achievement['xp_reward'])
                        coin_system.award_coins(user_id, achievement_name, achievement['coin_reward'])
                        
                        # Mark achievement as completed
                        achievements[achievement_name] = achievement['target']
                        user.items['achievements'] = achievements
                        db.commit()
                        return True
            
            return False
    
    def get_user_achievements(self, user_id: int) -> Dict:
        """Get user's achievement progress"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
            
            achievements = user.items.get('achievements', {})
            progress = {}
            
            for achievement_name, achievement in self.achievements.items():
                current = achievements.get(achievement_name, 0)
                progress[achievement_name] = {
                    'description': achievement['description'],
                    'progress': current,
                    'target': achievement['target'],
                    'completed': current >= achievement['target']
                }
            
            return progress
    
    def get_achievement_info(self, achievement_name: str) -> Dict:
        """Get information about a specific achievement"""
        if achievement_name not in self.achievements:
            return None
            
        achievement = self.achievements[achievement_name]
        return {
            'name': achievement_name,
            'description': achievement['description'],
            'xp_reward': achievement['xp_reward'],
            'coin_reward': achievement['coin_reward'],
            'type': achievement['type'],
            'target': achievement['target']
        }
    
    def get_all_achievements(self) -> List[Dict]:
        """Get all available achievements"""
        return [{
            'name': name,
            'description': achievement['description'],
            'xp_reward': achievement['xp_reward'],
            'coin_reward': achievement['coin_reward'],
            'type': achievement['type'],
            'target': achievement['target']
        } for name, achievement in self.achievements.items()]

achievement_system = AchievementSystem()
