from typing import List, Dict, Tuple
from db.models import User, Card
from db.db import SessionLocal
from rewards.coin_system import coin_system

class CardBuilder:
    def __init__(self):
        self.card_size = 5
        self.max_cards = 3  # Default max cards per user
        self.card_cost = 5  # Default cost in coins
        
    def create_custom_card(self, user_id: int, numbers: List[int]) -> bool:
        """Create a custom card for a user"""
        if not self._validate_numbers(numbers):
            return False
            
        if not self._check_card_limit(user_id):
            return False
            
        if not self._check_coins(user_id):
            return False
            
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
                
            # Deduct coins
            user.coins -= self.card_cost
            
            # Create card
            card = Card(
                user_id=user.id,
                card_data=numbers,
                is_custom=True,
                active_game_id=None
            )
            db.add(card)
            db.commit()
            
            return True
    
    def _validate_numbers(self, numbers: List[int]) -> bool:
        """Validate card numbers"""
        if len(numbers) != self.card_size * self.card_size:
            return False
            
        if len(set(numbers)) != len(numbers):  # Check for duplicates
            return False
            
        if any(num < 1 or num > 25 for num in numbers):  # Check range
            return False
            
        return True
    
    def _check_card_limit(self, user_id: int) -> bool:
        """Check if user has reached card limit"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
                
            # Get current card count
            card_count = db.query(Card).filter(Card.user_id == user.id).count()
            return card_count < self.max_cards
    
    def _check_coins(self, user_id: int) -> bool:
        """Check if user has enough coins"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
                
            return user.coins >= self.card_cost
    
    def get_user_cards(self, user_id: int) -> List[Dict]:
        """Get all custom cards for a user"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
                
            cards = db.query(Card).filter(Card.user_id == user.id).all()
            return [{
                'id': card.id,
                'numbers': card.card_data,
                'is_custom': card.is_custom,
                'created_at': card.created_at
            } for card in cards]
    
    def delete_card(self, user_id: int, card_id: int) -> bool:
        """Delete a custom card"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
                
            card = db.query(Card).filter(
                Card.id == card_id,
                Card.user_id == user.id
            ).first()
            if not card:
                return False
                
            db.delete(card)
            db.commit()
            return True
    
    def get_card_cost(self) -> int:
        """Get the cost to create a custom card"""
        return self.card_cost
    
    def get_max_cards(self) -> int:
        """Get the maximum number of cards a user can have"""
        return self.max_cards

card_builder = CardBuilder()
