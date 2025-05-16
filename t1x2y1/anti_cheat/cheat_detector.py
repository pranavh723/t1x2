from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from db.models import User, Game
from db.db import SessionLocal
import random

class CheatDetector:
    def __init__(self):
        self.rate_limits = {
            'mark_number': 5,  # per minute
            'call_number': 3,  # per minute
            'join_room': 2,    # per minute
            'create_room': 1   # per minute
        }
        self.suspicious_patterns = {
            'too_fast_wins': 3,    # wins in less than 2 minutes
            'too_many_marks': 5,   # marks in less than 10 seconds
            'invalid_numbers': 3,  # trying to mark non-existent numbers
            'multiple_rooms': 3,   # creating/joining too many rooms
            'fake_bingo': 2       # declaring bingo without valid pattern
        }
        self.action_thresholds = {
            'warning': 3,
            'mute': 5,
            'ban': 8
        }
        self.user_history = {}
        
    def check_rate_limit(self, user_id: int, action: str) -> bool:
        """Check if user is within rate limits"""
        if user_id not in self.user_history:
            self.user_history[user_id] = {}
        
        user_data = self.user_history[user_id]
        if action not in user_data:
            user_data[action] = {'count': 1, 'last_time': datetime.now()}
            return True
        
        now = datetime.now()
        last_action = user_data[action]['last_time']
        time_diff = (now - last_action).total_seconds() / 60  # minutes
        
        if time_diff < 1:  # within last minute
            if user_data[action]['count'] >= self.rate_limits[action]:
                return False
            user_data[action]['count'] += 1
        else:
            user_data[action]['count'] = 1
        
        user_data[action]['last_time'] = now
        return True
    
    def check_suspicious_patterns(self, user_id: int, action: str, data: Dict) -> bool:
        """Check for suspicious patterns"""
        if user_id not in self.user_history:
            self.user_history[user_id] = {'suspicious': 0}
        
        user_data = self.user_history[user_id]
        
        if action == 'win':
            if data['time'] < 120:  # less than 2 minutes
                user_data['suspicious'] += self.suspicious_patterns['too_fast_wins']
        
        elif action == 'mark':
            if data['time'] < 10:  # less than 10 seconds
                user_data['suspicious'] += self.suspicious_patterns['too_many_marks']
            if not self._validate_number(data['number'], data['card']):
                user_data['suspicious'] += self.suspicious_patterns['invalid_numbers']
        
        elif action == 'create_room' or action == 'join_room':
            if user_data.get('room_count', 0) >= 3:
                user_data['suspicious'] += self.suspicious_patterns['multiple_rooms']
            user_data['room_count'] = user_data.get('room_count', 0) + 1
        
        elif action == 'bingo':
            if not self._validate_bingo(data['card'], data['marked']):
                user_data['suspicious'] += self.suspicious_patterns['fake_bingo']
        
        self._take_action(user_id)
        return True
    
    def _validate_number(self, number: int, card: List[List[int]]) -> bool:
        """Validate if number exists on card"""
        return any(number in row for row in card)
    
    def _validate_bingo(self, card: List[List[int]], marked: List[List[bool]]) -> bool:
        """Validate if bingo is valid"""
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
    
    def _take_action(self, user_id: int) -> None:
        """Take action based on suspicious score"""
        user_data = self.user_history[user_id]
        
        if user_data['suspicious'] >= self.action_thresholds['ban']:
            self._ban_user(user_id)
        elif user_data['suspicious'] >= self.action_thresholds['mute']:
            self._mute_user(user_id)
        elif user_data['suspicious'] >= self.action_thresholds['warning']:
            self._warn_user(user_id)
    
    def _warn_user(self, user_id: int) -> None:
        """Send warning to suspicious user"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.items['warnings'] = user.items.get('warnings', 0) + 1
                db.commit()
    
    def _mute_user(self, user_id: int) -> None:
        """Mute suspicious user"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.items['muted_until'] = (datetime.now() + timedelta(hours=1)).isoformat()
                db.commit()
    
    def _ban_user(self, user_id: int) -> None:
        """Ban suspicious user"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.items['banned'] = True
                db.commit()
    
    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            return user.items.get('banned', False) if user else False
    
    def is_user_muted(self, user_id: int) -> bool:
        """Check if user is muted"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                muted_until = user.items.get('muted_until')
                if muted_until:
                    return datetime.fromisoformat(muted_until) > datetime.now()
            return False

cheat_detector = CheatDetector()
