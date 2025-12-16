"""
London Hotel Price Monitor Telegram Bot
A secure bot for monitoring hotel prices in London using Anthropic's Claude AI
"""

import os
import logging
from telethon import TelegramClient, events
from telethon.tl.custom import Button
from datetime import datetime, timedelta
import asyncio

# Import our secure modules
from secure_config import Config
from database import FlightDatabase as HotelDatabase  # Using same base class
from hotel_service import HotelPriceService
from ai_assistant import AnthropicAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(str(e))
    exit(1)

# Initialize services
db_folder = os.path.join(os.path.dirname(__file__), "db")
os.makedirs(db_folder, exist_ok=True)
session_file = os.path.join(db_folder, "bot_session")

# Initialize database
db = HotelDatabase(Config.DATABASE_PATH)

# Initialize hotel service with Amadeus
hotel_service = HotelPriceService(
    amadeus_key=Config.AMADEUS_API_KEY if hasattr(Config, 'AMADEUS_API_KEY') else None,
    amadeus_secret=Config.AMADEUS_API_SECRET if hasattr(Config, 'AMADEUS_API_SECRET') else None
)

# Initialize AI assistant
ai_assistant = AnthropicAssistant(Config.ANTHROPIC_API_KEY)

# Initialize Telegram client
client = TelegramClient(
    session_file, 
    Config.TELEGRAM_API_ID, 
    Config.TELEGRAM_API_HASH
).start(bot_token=Config.TELEGRAM_BOT_TOKEN)

# User conversation context
user_conversations = {}

def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded daily message limit"""
    user = db.get_or_create_user(user_id)
    current_date = datetime.now().date()
    
    if user['last_interaction']:
        last_date = datetime.fromisoformat(str(user['last_interaction'])).date()
        if last_date < current_date:
            db.reset_daily_message_count(user_id)
            return True
    
    message_count = db.get_user_message_count(user_id)
    return message_count < Config.MAX_MESSAGES_PER_DAY


@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command with interactive buttons"""
    user_id = event.sender_id
    sender = await event.get_sender()
    
    db.get_or_create_user(
        user_id=user_id,
        username=sender.username,
        first_name=sender.first_name
    )
    
    welcome_message = """**London Hotel Price Monitor Bot**

Track hotel prices in London and get alerts when prices drop.

Choose an action below:"""
    
    # Simplified inline keyboard - core features only
    buttons = [
        [Button.inline("🔍 Search Hotels", b"action_search")],
        [Button.inline("🔔 Set Price Alert", b"action_alerts"),
         Button.inline("📋 My Alerts", b"action_myalerts")],
        [Button.inline("🗺️ London Areas", b"action_areas"),
         Button.inline("💬 AI Assistant", b"action_chat")],
        [Button.inline("❓ Help", b"action_help")]
    ]
    
    await event.respond(welcome_message, buttons=buttons, parse_mode='Markdown')


@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command"""
    help_text = """
**London Hotel Monitor Bot - Commands**

**Search Hotels**
`/search` - Find hotels in London
Example: Westminster, Dec 25-27, 2 guests

**Price Alerts**
`/alert` - Create price alert
`/myalerts` - View active alerts
`/delete` - Remove alert

**Areas**
`/areas` - Show London neighborhoods

**AI Assistant**
`/chat` - Ask about hotels and London

**Tips:**
Popular areas: Westminster (sights), Shoreditch (nightlife), Camden (markets)
Book in advance for better prices

**Security:**
Your data is encrypted and secure.
    """
    
    await event.respond(help_text, parse_mode='Markdown')


@client.on(events.NewMessage(pattern='/areas'))
async def areas_handler(event):
    """Show London areas"""
    areas = hotel_service.get_london_areas()
    
    response = "**Popular London Areas:**\n\n"
    
    area_info = {
        "westminster": "Parliament, Big Ben, London Eye",
        "kensington": "Museums, Royal Albert Hall, Hyde Park",
        "camden": "Markets, live music, canal walks",
        "shoreditch": "Nightlife, street art, trendy cafes",
        "covent garden": "Shopping, theatres, restaurants",
        "city": "Financial district, St. Paul's Cathedral",
        "notting hill": "Portobello Market, colorful houses",
        "greenwich": "Maritime history, Royal Observatory",
        "paddington": "Transport hub, Little Venice",
        "soho": "Entertainment, dining, nightlife"
    }
    
    for area_key, area_data in areas.items():
        name = area_data['name']
        info = area_info.get(area_key, "Great area to explore")
        response += f"**{name}** - {info}\n"
    
    response += "\nUse `/search` to find hotels in any area"
    
    await event.respond(response, parse_mode='Markdown')


@client.on(events.NewMessage(pattern='/search'))
async def search_handler(event):
    """Handle hotel search"""
    user_id = event.sender_id
    
    if not check_rate_limit(user_id):
        await event.respond("Rate limit reached. Try again tomorrow.")
        return
    
    try:
        async with client.conversation(await event.get_chat(), exclusive=False, timeout=Config.SESSION_TIMEOUT) as conv:
            # Get area
            await conv.send_message("**Hotel Search in London**\n\nWhich area? (e.g., Westminster, Camden, Kensington)\n\nType 'cancel' to cancel.\nUse /areas to see all options.")
            area_msg = await conv.get_response()
            area = area_msg.text.strip().lower()
            
            if area == 'cancel':
                await conv.send_message("Search cancelled")
                return
            
            areas = hotel_service.get_london_areas()
            if area not in areas:
                await conv.send_message(f"Unknown area. Use /areas to see valid options.")
                return
            
            # Get check-in date
            await conv.send_message("Check-in date (YYYY-MM-DD):")
            checkin_msg = await conv.get_response()
            checkin_date = checkin_msg.text.strip()
            
            try:
                checkin_dt = datetime.strptime(checkin_date, '%Y-%m-%d')
                if checkin_dt < datetime.now():
                    await conv.send_message("Check-in date must be in the future.")
                    return
            except ValueError:
                await conv.send_message("Invalid date format. Use YYYY-MM-DD.")
                return
            
            # Get checkout date
            await conv.send_message("Check-out date (YYYY-MM-DD):")
            checkout_msg = await conv.get_response()
            checkout_date = checkout_msg.text.strip()
            
            try:
                checkout_dt = datetime.strptime(checkout_date, '%Y-%m-%d')
                if checkout_dt <= checkin_dt:
                    await conv.send_message("Check-out must be after check-in.")
                    return
            except ValueError:
                await conv.send_message("Invalid date format. Use YYYY-MM-DD.")
                return
            
            # Get number of guests
            await conv.send_message("Number of guests:")
            guests_msg = await conv.get_response()
            
            try:
                guests = int(guests_msg.text.strip())
                if guests < 1 or guests > 10:
                    await conv.send_message("Guests must be between 1-10.")
                    return
            except ValueError:
                await conv.send_message("Invalid number.")
                return
            
            # Search for hotels
            await conv.send_message("Searching for hotels...")
            
            hotels = await hotel_service.search_hotels_rapidapi(
                area, checkin_date, checkout_date, guests
            )
            
            if not hotels:
                error_msg = """**No hotels found**

This could be because:
- Amadeus API is not configured (add AMADEUS_API_KEY and AMADEUS_API_SECRET to .env)
- No available hotels for these dates
- Hotels in this area don't have availability

To use real hotel prices, get free Amadeus API keys at: https://developers.amadeus.com"""
                await conv.send_message(error_msg, parse_mode='Markdown')
                return
            
            # Show results
            nights = (checkout_dt - checkin_dt).days
            area_name = areas[area]['name']
            
            response = f"""
**Top Hotels in {area_name}**

Dates: {checkin_date} to {checkout_date} ({nights} nights)
Guests: {guests}

"""
            
            for i, hotel in enumerate(hotels[:5], 1):
                price_per_night = hotel.get('price_per_night', hotel['price'] / nights)
                stars = '* ' * hotel['stars']
                response += f"""
**{i}. {hotel['name']}** {stars}
Price: £{hotel['price']:.2f} total (£{price_per_night:.1f}/night)
Rating: {hotel['rating']}/10
Location: {hotel.get('distance_to_center', 'Central London')}

"""
            
            response += "Use `/alert` to track price changes"
            
            await conv.send_message(response, parse_mode='Markdown')
            
            # Get AI recommendation
            if hotels:
                analysis = await ai_assistant.analyze_hotel_data(hotels[0])
                await conv.send_message(f"**AI Recommendation:**\n{analysis}", parse_mode='Markdown')
            
            db.update_user_interaction(user_id)
            
    except asyncio.TimeoutError:
        await event.respond("Session timed out. Use /search to start over.")
    except Exception as e:
        logger.error(f"Error in search: {e}")
        await event.respond("An error occurred. Please try again.")


@client.on(events.NewMessage(pattern='/alert'))
async def alert_handler(event):
    """Handle price alert creation"""
    user_id = event.sender_id
    
    if not check_rate_limit(user_id):
        await event.respond("[WARN] You've reached your daily limit. Try again tomorrow.")
        return
    
    try:
        async with client.conversation(await event.get_chat(), exclusive=False, timeout=Config.SESSION_TIMEOUT) as conv:
            await conv.send_message("🔔 **Create Price Alert**\n\nWhich London area? (e.g., Westminster, Camden)\n\nType 'cancel' to cancel.")
            area_msg = await conv.get_response()
            area = area_msg.text.strip().lower()
            
            if area == 'cancel':
                await conv.send_message("Alert creation cancelled")
                return
            
            areas = hotel_service.get_london_areas()
            if area not in areas:
                await conv.send_message("[ERROR] Unknown area. Use /areas to see options.")
                return
            
            await conv.send_message(" Check-in date (YYYY-MM-DD):")
            checkin_msg = await conv.get_response()
            checkin_date = checkin_msg.text.strip()
            
            await conv.send_message(" Check-out date (YYYY-MM-DD):")
            checkout_msg = await conv.get_response()
            checkout_date = checkout_msg.text.strip()
            
            await conv.send_message(" Number of guests:")
            guests_msg = await conv.get_response()
            
            try:
                guests = int(guests_msg.text.strip())
            except ValueError:
                await conv.send_message("[ERROR] Invalid number.")
                return
            
            await conv.send_message(" Maximum price per night (£):")
            price_msg = await conv.get_response()
            
            try:
                max_price = float(price_msg.text.strip())
            except ValueError:
                await conv.send_message("[ERROR] Invalid price.")
                return
            
            await conv.send_message(" Specific hotel name (or 'any' for all hotels):")
            hotel_msg = await conv.get_response()
            hotel_name = hotel_msg.text.strip()
            
            if hotel_name.lower() == 'any':
                hotel_name = None
            
            # Create alert
            alert_id = db.create_hotel_alert(
                user_id=user_id,
                area=area,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                hotel_name=hotel_name,
                max_price=max_price,
                guests=guests
            )
            
            area_name = areas[area]['name']
            response = f"""
[OK] **Price Alert Created!**

**Alert ID:** {alert_id}
**Area:** {area_name}
**Dates:** {checkin_date} to {checkout_date}
**Guests:** {guests}
**Max Price:** £{max_price}/night
**Hotel:** {hotel_name or 'Any hotel'}

I'll notify you when prices drop below your target!

Use /myalerts to view all alerts.
            """
            
            await conv.send_message(response, parse_mode='Markdown')
            db.update_user_interaction(user_id)
            
    except asyncio.TimeoutError:
        await event.respond(" Session timed out.")
    except Exception as e:
        logger.error(f"Error in alert: {e}")
        await event.respond("[ERROR] An error occurred.")


@client.on(events.NewMessage(pattern='/myalerts'))
async def myalerts_handler(event):
    """Show user's active alerts"""
    user_id = event.sender_id
    
    alerts = db.get_user_alerts(user_id, active_only=True)
    
    if not alerts:
        await event.respond("You don't have any active alerts. Use /alert to create one!")
        return
    
    response = "🔔 **Your Active Price Alerts:**\n\n"
    
    for alert in alerts:
        response += f"""
**Alert #{alert['id']}**
Area: {alert['area'].title()}
Hotel: {alert['hotel_name'] or 'Any'}
Dates: {alert['checkin_date']} to {alert['checkout_date']}
Guests: {alert['guests']}
Max Price: £{alert['max_price']}/night
Created: {alert['created_at']}
---
        """
    
    response += "\nUse /delete to remove an alert."
    await event.respond(response, parse_mode='Markdown')


@client.on(events.NewMessage(pattern='/delete'))
async def delete_alert_handler(event):
    """Delete a price alert"""
    user_id = event.sender_id
    
    try:
        async with client.conversation(await event.get_chat(), exclusive=False, timeout=120) as conv:
            await conv.send_message("Enter Alert ID to delete (or 'cancel'):")
            msg = await conv.get_response()
            
            if msg.text.strip().lower() == 'cancel':
                await conv.send_message("Cancelled.")
                return
            
            try:
                alert_id = int(msg.text.strip())
            except ValueError:
                await conv.send_message("[ERROR] Invalid ID.")
                return
            
            success = db.delete_alert(alert_id, user_id)
            
            if success:
                await conv.send_message(f"[OK] Alert #{alert_id} deleted.")
            else:
                await conv.send_message(f"[ERROR] Alert not found.")
                
    except asyncio.TimeoutError:
        await event.respond(" Timed out.")
    except Exception as e:
        logger.error(f"Error deleting: {e}")
        await event.respond("[ERROR] Error occurred.")


@client.on(events.NewMessage(pattern='/chat'))
async def chat_handler(event):
    """Handle AI chat"""
    user_id = event.sender_id
    
    if not check_rate_limit(user_id):
        await event.respond("[WARN] Daily limit reached.")
        return
    
    try:
        async with client.conversation(await event.get_chat(), exclusive=False, timeout=Config.SESSION_TIMEOUT) as conv:
            if user_id not in user_conversations:
                user_conversations[user_id] = []
            
            keyboard_stop = [[Button.inline("Stop Chat", b"stop_chat")]]
            
            await conv.send_message(
                " **AI London Hotel Assistant**\n\nAsk about hotels, areas, or London travel tips!\n\nType 'done' or 'cancel' to end.",
                buttons=keyboard_stop
            )
            
            while True:
                msg_event = await conv.get_response()
                
                if msg_event.text.strip().lower() in ['done', 'exit', 'quit', 'stop', 'cancel']:
                    await conv.send_message("Chat ended. Use /chat to start again!")
                    user_conversations[user_id] = []
                    break
                
                user_message = msg_event.text.strip()
                thinking_msg = await conv.send_message("🤔 Thinking...")
                
                response = await ai_assistant.chat(
                    user_message,
                    conversation_history=user_conversations[user_id]
                )
                
                user_conversations[user_id].append({"role": "user", "content": user_message})
                user_conversations[user_id].append({"role": "assistant", "content": response})
                
                if len(user_conversations[user_id]) > 20:
                    user_conversations[user_id] = user_conversations[user_id][-20:]
                
                await thinking_msg.delete()
                await conv.send_message(f" {response}", buttons=keyboard_stop)
                
                db.update_user_interaction(user_id)
                
    except asyncio.TimeoutError:
        await event.respond(" Chat timed out.")
        if user_id in user_conversations:
            user_conversations[user_id] = []
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        await event.respond("[ERROR] Error occurred.")



# Button callback handlers
@client.on(events.CallbackQuery(pattern=b"action_search"))
async def callback_search(event):
    """Redirect to search command"""
    await event.answer()
    await search_handler(event)


@client.on(events.CallbackQuery(pattern=b"action_alerts"))
async def callback_alerts(event):
    """Show alert options"""
    await event.answer()
    
    message = """**Price Alert Options**

1. Specific Hotel Alert - Track a particular hotel's price
2. Area Budget Alert - Get notified when any hotel in an area drops below your budget

Choose below:"""
    
    buttons = [
        [Button.inline("Alert for Specific Hotel", b"alert_specific")],
        [Button.inline("Area Budget Alert", b"alert_area")],
        [Button.inline("Back to Menu", b"action_menu")]
    ]
    
    await event.respond(message, buttons=buttons, parse_mode='Markdown')


@client.on(events.CallbackQuery(pattern=b"alert_specific"))
async def callback_alert_specific(event):
    """Handle specific hotel alert creation"""
    await event.answer()
    await event.respond("Use /search to find a hotel first, then you can set an alert for it.")


@client.on(events.CallbackQuery(pattern=b"alert_area"))
async def callback_alert_area(event):
    """Handle area budget alert"""
    await event.answer()
    await alert_handler(event)


@client.on(events.CallbackQuery(pattern=b"action_myalerts"))
async def callback_myalerts(event):
    """Redirect to myalerts command"""
    await event.answer()
    await myalerts_handler(event)


@client.on(events.CallbackQuery(pattern=b"action_areas"))
async def callback_areas(event):
    """Show areas with buttons"""
    await event.answer()
    
    areas = hotel_service.get_london_areas()
    response = "**Popular London Areas:**\n\n"
    
    area_info = {
        "westminster": "Parliament, Big Ben, London Eye",
        "kensington": "Museums, Royal Albert Hall, Hyde Park",
        "camden": "Markets, live music, canal walks",
        "shoreditch": "Nightlife, street art, trendy cafes",
        "covent garden": "Shopping, theatres, restaurants",
        "city": "Financial district, St. Paul's Cathedral",
        "notting hill": "Portobello Market, colorful houses",
        "greenwich": "Maritime history, Royal Observatory",
        "paddington": "Transport hub, Little Venice",
        "soho": "Entertainment, dining, nightlife"
    }
    
    for area_key, area_data in areas.items():
        name = area_data['name']
        info = area_info.get(area_key, "Great area to explore")
        response += f"**{name}** - {info}\n"
    
    response += "\nClick below to search hotels in an area:"
    
    # Create area buttons
    buttons = [[Button.inline(area_info['name'], f"searcharea_{key}".encode()) 
               for key, area_info in list(areas.items())[i:i+2]]
              for i in range(0, len(areas), 2)]
    buttons.append([Button.inline("Back to Menu", b"action_menu")])
    
    await event.respond(response, buttons=buttons, parse_mode='Markdown')


@client.on(events.CallbackQuery(pattern=b"action_chat"))
async def callback_chat(event):
    """Redirect to chat command"""
    await event.answer()
    await chat_handler(event)


@client.on(events.CallbackQuery(pattern=b"action_help"))
async def callback_help(event):
    """Redirect to help command"""
    await event.answer()
    await help_handler(event)


@client.on(events.CallbackQuery(pattern=b"action_menu"))
async def callback_menu(event):
    """Return to main menu"""
    await event.answer()
    await start_handler(event)


@client.on(events.CallbackQuery(pattern=b"stop_chat"))
async def stop_chat_callback(event):
    """Handle stop chat button"""
    user_id = event.sender_id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await event.answer()
    await event.respond("Chat ended!")


def main():
    """Main entry point"""
    logger.info("🚀 London Hotel Price Monitor Bot starting...")
    logger.info("Bot is ready and listening for messages!")
    
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
