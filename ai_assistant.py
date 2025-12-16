import anthropic
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AnthropicAssistant:
    """AI Assistant using Anthropic's Claude API"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Anthropic API key is required")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"  # Claude 3 Opus
    
    async def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        Send a message to Claude and get a response
        
        Args:
            message: User's message
            conversation_history: List of previous messages in format [{"role": "user", "content": "..."}, ...]
        
        Returns:
            Claude's response text
        """
        try:
            # Build messages list
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})
            
            # Create system message for hotel assistant context
            system_message = """You are a helpful London hotel price monitoring assistant. You help users:
1. Find hotels in different London areas (Westminster, Camden, Kensington, etc.)
2. Track hotel prices and set up price alerts
3. Understand hotel pricing trends in London
4. Get recommendations for the best areas to stay based on their interests
5. Provide London travel tips and area information

Be concise, friendly, and helpful. Prices are in GBP (£).
Always prioritize user privacy and data security."""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_message,
                messages=messages
            )
            
            return response.content[0].text
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return "I'm having trouble processing your request right now. Please try again later."
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "An unexpected error occurred. Please try again."
    
    async def analyze_hotel_data(self, hotel_info: Dict) -> str:
        """Analyze hotel data and provide insights"""
        try:
            prompt = f"""Analyze this London hotel information and provide a brief summary (2-3 sentences max):
            
Hotel: {hotel_info.get('name')}
Area: {hotel_info.get('address', 'London')}
Price: £{hotel_info.get('price')} total
Rating: {hotel_info.get('rating')}/10
Stars: {hotel_info.get('stars')}

Is this a good deal? Should the user book now or wait?"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error analyzing hotel data: {e}")
            return "Unable to analyze hotel data at this time."
    
    async def suggest_areas(self, interests: str = "general tourism") -> str:
        """Suggest London areas based on user interests"""
        try:
            prompt = f"""A user is looking for a hotel in London. Their interests: {interests}

Suggest 3 London areas (e.g., Westminster, Camden, Shoreditch) they should consider.
For each area, provide 1 sentence explaining why it's good for their interests."""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error getting area suggestions: {e}")
            return "Unable to provide suggestions at this time."
