from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User
from db.db import SessionLocal
from rewards.xp_system import xp_system
from rewards.coin_system import coin_system

class EventSystem:
    def __init__(self):
        self.events = {
            "daily_bonus": {
                "start_time": "00:00",
                "end_time": "23:59",
                "reward": {
                    "xp": 25,
                    "coins": 15
                }
            },
            "weekly_tournament": {
                "start_time": "Saturday 18:00",
                "end_time": "Saturday 22:00",
                "reward": {
                    "xp": 50,
                    "coins": 30
                }
            },
            "holiday_bonus": {
                "start_time": "December 24 00:00",
                "end_time": "December 26 23:59",
                "reward": {
                    "xp": 100,
                    "coins": 50
                }
            }
        }
    
    def get_current_events(self) -> List[Dict]:
        """Get currently active events"""
        now = datetime.now()
        active_events = []
        
        for event_name, event_data in self.events.items():
            start_time = self._parse_time(event_data['start_time'])
            end_time = self._parse_time(event_data['end_time'])
            
            if start_time <= now <= end_time:
                active_events.append({
                    'name': event_name,
                    'reward': event_data['reward'],
                    'end_time': end_time
                })
        
        return active_events
    
    def get_event_rewards(self, user_id: int, event_name: str) -> bool:
        """Get rewards for an event"""
        if event_name not in self.events:
            return False
            
        event = self.events[event_name]
        now = datetime.now()
        
        # Check if event is active
        start_time = self._parse_time(event['start_time'])
        end_time = self._parse_time(event['end_time'])
        if not (start_time <= now <= end_time):
            return False
            
        # Award rewards
        reward = event['reward']
        xp_system.award_xp(user_id, "event", reward['xp'])
        coin_system.award_coins(user_id, "event", reward['coins'])
        
        return True
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        try:
            if len(time_str.split()) == 2:  # If it's just time (e.g., "18:00")
                time_only = datetime.strptime(time_str, "%H:%M")
                return datetime.now().replace(
                    hour=time_only.hour,
                    minute=time_only.minute,
                    second=0,
                    microsecond=0
                )
            else:  # If it's date and time (e.g., "December 24 18:00")
                return datetime.strptime(time_str, "%B %d %H:%M")
        except ValueError:
            return datetime.now()
    
    def create_custom_event(self, name: str, start_time: str, end_time: str, 
                          xp_reward: int, coin_reward: int) -> bool:
        """Create a custom event"""
        if name in self.events:
            return False
            
        try:
            self._parse_time(start_time)
            self._parse_time(end_time)
        except:
            return False
            
        self.events[name] = {
            'start_time': start_time,
            'end_time': end_time,
            'reward': {
                'xp': xp_reward,
                'coins': coin_reward
            }
        }
        return True
    
    def get_event_info(self, event_name: str) -> Dict:
        """Get information about an event"""
        if event_name not in self.events:
            return None
            
        event = self.events[event_name]
        return {
            'name': event_name,
            'start_time': event['start_time'],
            'end_time': event['end_time'],
            'reward': event['reward']
        }

event_system = EventSystem()
