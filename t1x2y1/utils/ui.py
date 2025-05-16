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

# Shop keyboard layout
def create_shop_keyboard():
    """Create shop keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Buy Coins", callback_data="buy_coins"),
            InlineKeyboardButton("Buy XP", callback_data="buy_xp")
        ],
        [
            InlineKeyboardButton("Buy Items", callback_data="buy_items"),
            InlineKeyboardButton("Buy Cards", callback_data="buy_cards")
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_quests_keyboard(quests: list) -> InlineKeyboardMarkup:
    """Create quests keyboard with available quests"""
    keyboard = []
    
    # Add quests
    for quest in quests:
        keyboard.append([
            InlineKeyboardButton(
                f"{quest['name']} - {quest['progress']}/{quest['target']}",
                callback_data=f"quest_{quest['id']}")
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_card_builder_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for custom card builder"""
    keyboard = [
        [
            InlineKeyboardButton("Add Number", callback_data="add_number"),
            InlineKeyboardButton("Remove Number", callback_data="remove_number")
        ],
        [
            InlineKeyboardButton("Save Card", callback_data="save_card"),
            InlineKeyboardButton("Cancel", callback_data="cancel_builder")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_events_keyboard(events: list) -> InlineKeyboardMarkup:
    """Create keyboard for events"""
    keyboard = []
    
    # Add events
    for event in events:
        keyboard.append([
            InlineKeyboardButton(
                f"{event['name']} - {event['status']}",
                callback_data=f"event_{event['id']}")
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_achievements_keyboard(achievements: list) -> InlineKeyboardMarkup:
    """Create keyboard for achievements"""
    keyboard = []
    
    # Add achievements
    for achievement in achievements:
        keyboard.append([
            InlineKeyboardButton(
                f"{achievement['name']} - {achievement['progress']}/{achievement['target']}",
                callback_data=f"achievement_{achievement['id']}")
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("Back to Menu", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_social_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for social features"""
    keyboard = [
        [
            InlineKeyboardButton("Friends", callback_data="social_friends"),
            InlineKeyboardButton("Leaderboard", callback_data="social_leaderboard")
        ],
        [
            InlineKeyboardButton("Invite Friends", callback_data="social_invite"),
            InlineKeyboardButton("Chat", callback_data="social_chat")
        ],
        [
            InlineKeyboardButton("Back to Menu", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_analytics_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for analytics features"""
    keyboard = [
        [
            InlineKeyboardButton("Game Stats", callback_data="analytics_games"),
            InlineKeyboardButton("Win Rate", callback_data="analytics_win_rate")
        ],
        [
            InlineKeyboardButton("Daily Activity", callback_data="analytics_daily"),
            InlineKeyboardButton("Leaderboard", callback_data="analytics_leaderboard")
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
