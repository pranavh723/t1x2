from telegram import Update
from telegram.ext import ContextTypes
from anti_cheat.cheat_detector import cheat_detector
from datetime import datetime

class AntiCheatMiddleware:
    def __init__(self):
        self.cheat_detector = cheat_detector
    
    async def process_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, data: Dict = None) -> bool:
        """Process and validate user action"""
        user_id = update.effective_user.id
        
        # Check if user is banned
        if self.cheat_detector.is_user_banned(user_id):
            await update.message.reply_text("You are banned from using this bot.")
            return False
            
        # Check if user is muted
        if self.cheat_detector.is_user_muted(user_id):
            await update.message.reply_text("You are currently muted.")
            return False
            
        # Check rate limits
        if not self.cheat_detector.check_rate_limit(user_id, action):
            await update.message.reply_text(f"Too many {action} actions. Please wait a minute.")
            return False
            
        # Check suspicious patterns for specific actions
        if action in ['win', 'mark', 'create_room', 'join_room', 'bingo']:
            if not self.cheat_detector.check_suspicious_patterns(user_id, action, data or {}):
                await update.message.reply_text("Suspicious activity detected. Please play fair!")
                return False
            
        return True
    
    async def validate_game_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, data: Dict) -> bool:
        """Validate game-related actions"""
        # Add game-specific validation logic here
        return await self.process_action(update, context, action, data)
    
    async def validate_room_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, data: Dict) -> bool:
        """Validate room-related actions"""
        # Add room-specific validation logic here
        return await self.process_action(update, context, action, data)
    
    async def validate_user_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, data: Dict) -> bool:
        """Validate user actions"""
        # Add user-specific validation logic here
        return await self.process_action(update, context, action, data)

anti_cheat_middleware = AntiCheatMiddleware()
