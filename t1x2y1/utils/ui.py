from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎮 Start Game", callback_data="start_game"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("quests", callback_data="quests"),
            InlineKeyboardButton("shop", callback_data="shop")
        ],
        [
            InlineKeyboardButton("", callback_data="support"),
            InlineKeyboardButton("", callback_data="updates")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_leaderboard_keyboard(page=1):
    """Create leaderboard keyboard with pagination"""
    keyboard = [
        [
            InlineKeyboardButton("◀️ Previous", callback_data=f"leaderboard_{page-1}"),
            InlineKeyboardButton("Next ▶️", callback_data=f"leaderboard_{page+1}")
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_bingo_card_keyboard(card_data):
    """Create a 5x5 bingo card keyboard"""
    keyboard = []
    for row in card_data:
        row_buttons = []
        for num in row:
            # Use emoji for marked numbers
            if num == 'marked':
                button = InlineKeyboardButton("✅", callback_data=f"mark_{num}")
            else:
                button = InlineKeyboardButton(str(num), callback_data=f"mark_{num}")
            row_buttons.append(button)
        keyboard.append(row_buttons)
    
    # Add action buttons at the bottom
    keyboard.append([
        InlineKeyboardButton("", callback_data="call_number"),
        InlineKeyboardButton("", callback_data="check_bingo")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_room_creation_keyboard():
    """Create keyboard for room creation options"""
    keyboard = [
        [
            InlineKeyboardButton("Public Room", callback_data="room_public"),
            InlineKeyboardButton("Private Room", callback_data="room_private")
        ],
        [
            InlineKeyboardButton("", callback_data="room_size_2"),
            InlineKeyboardButton("", callback_data="room_size_3"),
            InlineKeyboardButton("", callback_data="room_size_4"),
            InlineKeyboardButton("", callback_data="room_size_5")
        ],
        [
            InlineKeyboardButton("", callback_data="call_auto"),
            InlineKeyboardButton("", callback_data="call_player")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_room_join_keyboard(room_code):
    """Create keyboard for joining a room"""
    keyboard = [
        [InlineKeyboardButton(f"Join Room {room_code}", callback_data=f"join_{room_code}")]
    ]
    return InlineKeyboardMarkup(keyboard)
