from typing import Dict, List
from db.models import User
from db.db import SessionLocal
from rewards.xp_system import xp_system

class CoinSystem:
    def __init__(self):
        self.coin_rewards = {
            "win_ai_easy": 10,
            "win_ai_medium": 15,
            "win_ai_hard": 25,
            "win_multiplayer": 30,
            "daily_login": 15,
            "refer_friend": 10,
            "custom_card": 5,
            "streak": {
                3: 20,
                5: 30,
                7: 50
            }
        }
        self.shop_items = {
            "theme_pack": 50,
            "extra_card_slot": 40,
            "instant_rematch": 20,
            "power_cut": 30,
            "gift_pack": 70
        }
    
    def award_coins(self, user_id: int, action: str, amount: int = None) -> int:
        """Award coins to a user for a specific action"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return 0
            
            if amount:
                coins_to_add = amount
            else:
                coins_to_add = self.coin_rewards.get(action, 0)
            
            user.coins += coins_to_add
            db.commit()
            
            return user.coins
    
    def purchase_item(self, user_id: int, item: str) -> bool:
        """Purchase an item from the shop"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            if item not in self.shop_items:
                return False
            
            price = self.shop_items[item]
            if user.coins < price:
                return False
            
            user.coins -= price
            user.items = user.items or {}
            user.items['owned_items'] = user.items.get('owned_items', [])
            user.items['owned_items'].append(item)
            db.commit()
            
            return True
    
    def get_shop_items(self) -> Dict:
        """Get all available shop items"""
        return self.shop_items
    
    def get_user_inventory(self, user_id: int) -> Dict:
        """Get user's owned items"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return {}
            
            return user.items.get('owned_items', [])
    
    def use_item(self, user_id: int, item: str) -> bool:
        """Use a purchased item"""
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            inventory = user.items.get('owned_items', [])
            if item not in inventory:
                return False
            
            # Handle item usage logic here
            # For now, just remove the item from inventory
            inventory.remove(item)
            user.items['owned_items'] = inventory
            db.commit()
            
            return True

coin_system = CoinSystem()
