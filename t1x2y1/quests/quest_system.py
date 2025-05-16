from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User
from db.db import SessionLocal
from rewards.xp_system import xp_system
from rewards.coin_system import coin_system

class QuestSystem:
    def __init__(self):
        self.daily_quests = {
            "play_game": {
                "description": "Play a game",
                "xp_reward": 25,
                "coin_reward": 10,
                "target": 1
            },
            "win_game": {
                "description": "Win a game",
                "xp_reward": 50,
                "coin_reward": 15,
                "target": 1
            },
            "mark_numbers": {
                "description": "Mark 10 numbers",
                "xp_reward": 10,
                "coin_reward": 5,
                "target": 10
            },
            "share_invite": {
                "description": "Share invite link",
                "xp_reward": 20,
                "coin_reward": 10,
                "target": 1
            }
        }
        
        self.weekly_quests = {
            "play_5_games": {
                "description": "Play 5 games",
                "xp_reward": 100,
                "coin_reward": 30,
                "target": 5
            },
            "win_3_games": {
                "description": "Win 3 games",
                "xp_reward": 150,
                "coin_reward": 40,
                "target": 3
            },
            "refer_friends": {
                "description": "Refer 2 friends",
                "xp_reward": 50,
                "coin_reward": 20,
                "target": 2
            }
        }
    
    def get_daily_quests(self, user_id: int) -> Dict:
        """Get user's daily quests"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
            
            quests = user.items.get('quests', {}).get('daily', {})
            if not quests:
                quests = {quest: 0 for quest in self.daily_quests}
            
            return quests
    
    def get_weekly_quests(self, user_id: int) -> Dict:
        """Get user's weekly quests"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
            
            quests = user.items.get('quests', {}).get('weekly', {})
            if not quests:
                quests = {quest: 0 for quest in self.weekly_quests}
            
            return quests
    
    def update_quest_progress(self, user_id: int, quest_type: str, amount: int = 1) -> None:
        """Update quest progress"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            quests = user.items.get('quests', {})
            
            # Update daily quest
            if quest_type in self.daily_quests:
                current = quests.get('daily', {}).get(quest_type, 0)
                quests['daily'][quest_type] = min(current + amount, self.daily_quests[quest_type]['target'])
                
                # Check if completed
                if quests['daily'][quest_type] == self.daily_quests[quest_type]['target']:
                    self._award_quest_rewards(user_id, quest_type, 'daily')
            
            # Update weekly quest
            elif quest_type in self.weekly_quests:
                current = quests.get('weekly', {}).get(quest_type, 0)
                quests['weekly'][quest_type] = min(current + amount, self.weekly_quests[quest_type]['target'])
                
                # Check if completed
                if quests['weekly'][quest_type] == self.weekly_quests[quest_type]['target']:
                    self._award_quest_rewards(user_id, quest_type, 'weekly')
            
            user.items['quests'] = quests
            db.commit()
    
    def _award_quest_rewards(self, user_id: int, quest_type: str, quest_period: str) -> None:
        """Award rewards for completed quest"""
        quest = self.daily_quests[quest_type] if quest_type == 'daily' else self.weekly_quests[quest_type]
        
        xp_system.award_xp(user_id, quest_type, quest['xp_reward'])
        coin_system.award_coins(user_id, quest_type, quest['coin_reward'])
    
    def reset_daily_quests(self, user_id: int) -> None:
        """Reset daily quests at midnight"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            user.items['quests']['daily'] = {quest: 0 for quest in self.daily_quests}
            db.commit()
    
    def reset_weekly_quests(self, user_id: int) -> None:
        """Reset weekly quests on Monday"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return
            
            user.items['quests']['weekly'] = {quest: 0 for quest in self.weekly_quests}
            db.commit()
    
    def get_quest_status(self, user_id: int) -> Dict:
        """Get quest completion status"""
        daily = self.get_daily_quests(user_id)
        weekly = self.get_weekly_quests(user_id)
        
        return {
            'daily': {
                quest: {
                    'progress': daily[quest],
                    'target': self.daily_quests[quest]['target'],
                    'reward': {
                        'xp': self.daily_quests[quest]['xp_reward'],
                        'coins': self.daily_quests[quest]['coin_reward']
                    }
                } for quest in daily
            },
            'weekly': {
                quest: {
                    'progress': weekly[quest],
                    'target': self.weekly_quests[quest]['target'],
                    'reward': {
                        'xp': self.weekly_quests[quest]['xp_reward'],
                        'coins': self.weekly_quests[quest]['coin_reward']
                    }
                } for quest in weekly
            }
        }

quest_system = QuestSystem()
