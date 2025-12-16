import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Secure configuration management using environment variables"""
    
    # Telegram Configuration
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Anthropic API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Amadeus Hotel API Configuration
    AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
    AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')
    
    # London Settings
    DEFAULT_CITY = os.getenv('DEFAULT_CITY', 'London')
    DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'GBP')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', './db/hotel_monitor.db')
    
    # Security Settings
    MAX_MESSAGES_PER_DAY = int(os.getenv('MAX_MESSAGES_PER_DAY', '50'))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '600'))
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set"""
        required_vars = [
            ('TELEGRAM_API_ID', cls.TELEGRAM_API_ID),
            ('TELEGRAM_API_HASH', cls.TELEGRAM_API_HASH),
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('ANTHROPIC_API_KEY', cls.ANTHROPIC_API_KEY),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please create a .env file based on .env.example"
            )
        
        return True
