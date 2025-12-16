import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class FlightDatabase:
    """Secure database management for flight monitoring"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    message_count INTEGER DEFAULT 0,
                    last_interaction TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Hotel alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hotel_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    hotel_name TEXT,
                    area TEXT NOT NULL,
                    checkin_date TEXT NOT NULL,
                    checkout_date TEXT NOT NULL,
                    guests INTEGER DEFAULT 2,
                    rooms INTEGER DEFAULT 1,
                    max_price REAL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Price history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER,
                    price REAL,
                    airline TEXT,
                    currency TEXT DEFAULT 'USD',
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (alert_id) REFERENCES flight_alerts(id)
                )
            ''')
            
            conn.commit()
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        """Get user or create if doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.execute('''
                    INSERT INTO users (user_id, username, first_name, last_interaction)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, first_name, datetime.now()))
                conn.commit()
                
                return {
                    'user_id': user_id,
                    'username': username,
                    'first_name': first_name,
                    'message_count': 0,
                    'last_interaction': datetime.now()
                }
            
            return {
                'user_id': user[0],
                'username': user[1],
                'first_name': user[2],
                'message_count': user[3],
                'last_interaction': user[4]
            }
    
    def update_user_interaction(self, user_id: int):
        """Update user's last interaction timestamp and increment message count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_interaction = ?, message_count = message_count + 1
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            conn.commit()
    
    def reset_daily_message_count(self, user_id: int):
        """Reset message count for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET message_count = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
    
    def get_user_message_count(self, user_id: int) -> int:
        """Get current message count for user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT message_count FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
    
    def create_hotel_alert(self, user_id: int, area: str, checkin_date: str,
                          checkout_date: str, hotel_name: str = None, 
                          max_price: float = None, guests: int = 2, rooms: int = 1) -> int:
        """Create a new hotel price alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hotel_alerts 
                (user_id, hotel_name, area, checkin_date, checkout_date, guests, rooms, max_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, hotel_name, area.lower(), checkin_date, checkout_date, guests, rooms, max_price))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_alerts(self, user_id: int, active_only: bool = True) -> List[Dict]:
        """Get all alerts for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if active_only:
                cursor.execute('''
                    SELECT id, hotel_name, area, checkin_date, checkout_date, guests, max_price, created_at
                    FROM hotel_alerts
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT id, hotel_name, area, checkin_date, checkout_date, guests, max_price, is_active, created_at
                    FROM hotel_alerts
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'id': row[0],
                    'hotel_name': row[1],
                    'area': row[2],
                    'checkin_date': row[3],
                    'checkout_date': row[4],
                    'guests': row[5],
                    'max_price': row[6],
                    'created_at': row[7] if active_only else row[8]
                })
            
            return alerts
    
    def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete/deactivate a hotel alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE hotel_alerts 
                SET is_active = 0 
                WHERE id = ? AND user_id = ?
            ''', (alert_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def save_price_check(self, alert_id: int, price: float, airline: str = None, currency: str = 'USD'):
        """Save a price check result"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO price_history (alert_id, price, airline, currency)
                VALUES (?, ?, ?, ?)
            ''', (alert_id, price, airline, currency))
            
            cursor.execute('''
                UPDATE hotel_alerts 
                SET last_checked = ? 
                WHERE id = ?
            ''', (datetime.now(), alert_id))
            
            conn.commit()
    
    def get_price_history(self, alert_id: int, days: int = 30) -> List[Dict]:
        """Get price history for an alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT price, airline, currency, checked_at
                FROM price_history
                WHERE alert_id = ? AND checked_at >= ?
                ORDER BY checked_at DESC
            ''', (alert_id, since_date))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'price': row[0],
                    'airline': row[1],
                    'currency': row[2],
                    'checked_at': row[3]
                })
            
            return history
