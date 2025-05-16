from typing import Dict, List
from datetime import datetime, timedelta
from db.models import User
from db.db import SessionLocal

class XPSystem:
    def __init__(self):
        self.daily_quests = {
            "play_game": 25,
            "win_game": 50,
            "mark_numbers": 10,
            "share_invite": 20,
            "streak": {
                3: 30,
                5: 50,
                7: 100
            }
        }
        self.weekly_quests = {
            "play_5_games": 100,
            "win_3_games": 150,
            "refer_friends": 50
        }
    
    def award_xp(self, user_id: int, action: str, amount: int = None) -> int:
        """Award XP to a user for a specific action"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return 0
            
            if amount:
                xp_to_add = amount
            else:
                xp_to_add = self.daily_quests.get(action, 0)
            
            user.xp += xp_to_add
            user.last_seen = datetime.now()
            db.commit()
            
            return user.xp
    
    def check_daily_streak(self, user_id: int) -> int:
        """Check and update user's daily streak"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return 0
            
            now = datetime.now()
            if user.last_seen.date() != now.date():
                user.streak += 1
                user.last_seen = now
                
                # Award streak bonus
                if user.streak in self.daily_quests["streak"]:
                    bonus = self.daily_quests["streak"][user.streak]
                    user.xp += bonus
                
                db.commit()
            
            return user.streak
    
    def reset_weekly_quests(self, user_id: int) -> None:
        """Reset weekly quests at the start of each week"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            now = datetime.now()
            if now.weekday() == 0:  # Monday
                user.items['weekly_quests'] = {
                    'play_5_games': 0,
                    'win_3_games': 0,
                    'refer_friends': 0
                }
                db.commit()
    
    def get_quest_status(self, user_id: int) -> Dict:
        """Get user's quest completion status"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
            
            return user.items.get('quests', {
                'daily': {
                    'play_game': 0,
                    'win_game': 0,
                    'mark_numbers': 0,
                    'share_invite': 0
                },
                'weekly': {
                    'play_5_games': 0,
                    'win_3_games': 0,
                    'refer_friends': 0
                }
            })

xp_system = XPSystem()
