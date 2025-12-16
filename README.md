# London Hotel Price Monitor Bot

A Telegram bot for monitoring hotel prices in London using Amadeus Hotel API and Anthropic's Claude AI.

## Features

- **Hotel Search** - Find hotels in 10 popular London areas
- **Price Alerts** - Set alerts for specific areas and budgets
- **Real-Time Pricing** - Live hotel prices via Amadeus API
- **AI Assistant** - Get hotel recommendations from Claude AI
- **Area Guide** - Browse Westminster, Kensington, Camden, Shoreditch, and more

## Supported London Areas

Westminster, South Kensington, Camden, Shoreditch, Covent Garden, City of London, Notting Hill, Greenwich, Paddington, Soho

## Quick Start

1. **Get API Keys** (all free):
   - Telegram: https://my.telegram.org/apps
   - Amadeus: https://developers.amadeus.com/
   - Anthropic: https://console.anthropic.com/

2. **Clone & Install**:
```bash
git clone <repo>
cd Friday-Telegram-Bot
pip install -r requirements.txt
```

3. **Configure**:
```bash
cp .env.example .env
# Add your API keys to .env
```

4. **Run**:
```bash
python hotel_monitor_bot.py
```

## Bot Commands

- `/start` - Open main menu with buttons
- `/search` - Search hotels by area and dates
- `/alert` - Set price alert for an area
- `/myalerts` - View active alerts
- `/areas` - Browse London neighborhoods
- `/chat` - Chat with AI assistant
- `/help` - Show help message

## Technology Stack

- **Bot Framework**: Telethon (async Telegram client)
- **Hotel API**: Amadeus Hotel Search API (2,000 free requests/month)
- **AI**: Anthropic Claude 3 Opus
- **Database**: SQLite with async operations
- **Concurrency**: Python asyncio for non-blocking operations

## Architecture

- `hotel_monitor_bot.py` - Main bot with inline keyboard UI
- `hotel_service.py` - Amadeus API integration
- `ai_assistant.py` - Claude AI for recommendations
- `database.py` - SQLite for user data and alerts
- `secure_config.py` - Environment variable management

### Concurrency Model

The bot uses Python's `asyncio` for concurrent operations:
- Async HTTP requests to hotel APIs
- Non-blocking database operations
- Concurrent user conversation handling
- Background price monitoring tasks

### Project Structure

```
hotel_monitor_bot.py    # Main bot with async event handlers
hotel_service.py         # Async hotel API client
database.py              # SQLite with async-safe operations
ai_assistant.py          # Anthropic Claude integration
secure_config.py         # Environment configuration
```

## Security

- Environment variables for all secrets
- No hardcoded API keys
- Rate limiting (50 messages/day default)
- Gitignore protection for .env
- Parameterized SQL queries

## Database Schema

- `users` - User profiles and rate limits
- `hotel_alerts` - Price alert configuration  
- `price_history` - Price tracking over time

## Deployment

Works on Heroku, Railway, Render, or any Python 3.8+ platform.

Set environment variables and run `python hotel_monitor_bot.py`.

## Development

### Testing Without API Keys

The bot includes realistic mock data for all London areas. Perfect for development without API costs.

### Adding Features

- Hotel service: `hotel_service.py`
- Bot commands: `hotel_monitor_bot.py`  
- Database schema: `database.py`

