# Quick Start - London Hotel Monitor Bot

Get the bot running in 5 minutes!

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Get Free API Keys

**Telegram** (required)
- Message @BotFather → create bot → copy token
- Visit https://my.telegram.org/apps → get API ID and hash

**Amadeus** (required for live prices)
- Sign up: https://developers.amadeus.com/
- Create app → copy API key and secret
- Free: 2,000 requests/month

**Anthropic** (required for AI)
- Sign up: https://console.anthropic.com/
- Create API key

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_BOT_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
AMADEUS_API_KEY=your_amadeus_key
AMADEUS_API_SECRET=your_amadeus_secret
```

## 4. Run

```bash
python hotel_monitor_bot.py
```

## First Search

```
/search
> westminster
> 2024-12-25
> 2024-12-27
> 2

Bot returns top 5 hotels with prices
```

## Commands

- `/search` - Find hotels
- `/alert` - Set price alert
- `/areas` - List London areas
- `/chat` - Ask AI about hotels
- `/help` - Show commands

## Troubleshooting

**Missing environment variables**: Check .env file has all required values

**Module errors**: Run `pip install -r requirements.txt`

**Bot not responding**: Verify bot token, ensure bot is running

**Unknown area**: Use `/areas` for valid names

## Next Steps

See README.md for full documentation
