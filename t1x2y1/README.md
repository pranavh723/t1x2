# Telegram Bingo Bot

A feature-rich Bingo game bot for Telegram with multiplayer support, AI opponents, and various game modes.

## Features

- Multiplayer Bingo games
- AI opponents with different difficulty levels
- XP and coin system
- Shop system with items and power-ups
- Leaderboard
- Daily and weekly quests
- Anti-cheat system
- Custom card builder
- Event system
- Achievement system
- Social features (friends, invites)
- Analytics dashboard
- Admin panel with maintenance mode
- Rate limiting
- User banning system

## Deployment on Render

This bot is configured for easy deployment on Render.com.

### One-Click Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deployment

1. Fork this repository to your GitHub account
2. Create a new Web Service on Render
   - Go to https://dashboard.render.com/
   - Click "New +"
   - Select "Web Service"
3. Connect your GitHub repository
   - Click "Connect GitHub Repository"
   - Select your repository
   - Click "Connect"
4. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Add the following environment variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather (7662693814:AAH48vJMmVqzyP0v3OmmwzqTyaMloNHFAec)
   - `OWNER_ID`: Your Telegram user ID
   - `DATABASE_URL`: Database connection string (SQLite by default)
   - `ENV`: Set to `production`

### Configuration

The bot uses the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `OWNER_ID`: Your Telegram user ID (for admin commands)
- `DATABASE_URL`: Database connection string
- `ENV`: Environment (`development` or `production`)
- `MAINTENANCE_MODE`: Set to `true` to enable maintenance mode
     - `OWNER_ID`: 69855055204
     - `ENV`: production

4. Database Setup:
   - Click "New +"
   - Select "PostgreSQL Database"
   - Name it (e.g., "bingo-bot-db")
   - Click "Create"
   - Copy the DATABASE_URL from "Connection Details"
   - Add it as an environment variable in your Web Service

5. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Environment: Python 3.11

6. Click "Create Web Service"

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python main.py
   ```

## Database

- Local: SQLite (bingo_bot.db)
- Production: PostgreSQL (on Render)

## Logging

- Render: Through Render's logs
- Local: `logs/bingo_bot.log`

## Error Handling

- Comprehensive error logging
- Admin notifications
- Rate limiting
- Maintenance mode

## Security

- Rate limiting
- User banning
- Maintenance mode
- Environment-based security

## License

MIT License
