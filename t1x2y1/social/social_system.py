from typing import Dict, List, Tuple
from datetime import datetime
from db.models import User
from db.db import SessionLocal

class SocialSystem:
    def __init__(self):
        self.friend_request_limit = 10  # Daily limit
        self.invite_limit = 5  # Daily limit
        self.message_limit = 20  # Daily limit
    
    def add_friend(self, user_id: int, friend_id: int) -> bool:
        """Add a friend"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            friend = db.query(User).filter(User.telegram_id == friend_id).first()
            
            if not user or not friend:
                return False
                
            # Check if already friends
            friends = user.items.get('friends', [])
            if friend_id in friends:
                return False
                
            # Add to both users' friend lists
            user.items['friends'] = friends + [friend_id]
            friend.friends = friend.items.get('friends', []) + [user_id]
            
            db.commit()
            return True
    
    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """Remove a friend"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            friend = db.query(User).filter(User.telegram_id == friend_id).first()
            
            if not user or not friend:
                return False
                
            # Remove from both users' friend lists
            user.friends = [f for f in user.items.get('friends', []) if f != friend_id]
            friend.friends = [f for f in friend.items.get('friends', []) if f != user_id]
            
            db.commit()
            return True
    
    def get_friends(self, user_id: int) -> List[Dict]:
        """Get user's friends list"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
                
            friends = []
            for friend_id in user.items.get('friends', []):
                friend = db.query(User).filter(User.id == friend_id).first()
                if friend:
                    friends.append({
                        'id': friend_id,
                        'username': friend.username,
                        'xp': friend.xp,
                        'coins': friend.coins
                    })
            
            return friends
    
    def send_friend_request(self, sender_id: int, receiver_id: int) -> bool:
        """Send a friend request"""
        with SessionLocal() as db:
            sender = db.query(User).filter(User.telegram_id == sender_id).first()
            receiver = db.query(User).filter(User.telegram_id == receiver_id).first()
            
            if not sender or not receiver:
                return False
                
            # Check if already friends
            if receiver_id in sender.items.get('friends', []):
                return False
                
            # Check if already sent request
            if receiver_id in sender.items.get('sent_requests', []):
                return False
                
            # Add to sent requests
            sender.items['sent_requests'] = sender.items.get('sent_requests', []) + [receiver_id]
            db.commit()
            return True
    
    def accept_friend_request(self, user_id: int, sender_id: int) -> bool:
        """Accept a friend request"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            sender = db.query(User).filter(User.telegram_id == sender_id).first()
            
            if not user or not sender:
                return False
                
            # Add to friends
            user.friends = user.items.get('friends', []) + [sender_id]
            sender.friends = sender.items.get('friends', []) + [user_id]
            
            # Remove from pending requests
            user.items['pending_requests'] = [r for r in user.items.get('pending_requests', []) if r != sender_id]
            sender.items['sent_requests'] = [r for r in sender.items.get('sent_requests', []) if r != user_id]
            
            db.commit()
            return True
    
    def decline_friend_request(self, user_id: int, sender_id: int) -> bool:
        """Decline a friend request"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            sender = db.query(User).filter(User.telegram_id == sender_id).first()
            
            if not user or not sender:
                return False
                
            # Remove from pending requests
            user.items['pending_requests'] = [r for r in user.items.get('pending_requests', []) if r != sender_id]
            sender.items['sent_requests'] = [r for r in sender.items.get('sent_requests', []) if r != user_id]
            
            db.commit()
            return True
    
    def get_pending_requests(self, user_id: int) -> List[int]:
        """Get pending friend requests"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
                
            return user.items.get('pending_requests', [])
    
    def get_sent_requests(self, user_id: int) -> List[int]:
        """Get sent friend requests"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
                
            return user.items.get('sent_requests', [])

social_system = SocialSystem()
