import aiohttp
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from amadeus import Client, ResponseError

logger = logging.getLogger(__name__)

# Popular London areas with coordinates
LONDON_AREAS = {
    "westminster": {"lat": 51.5014, "lon": -0.1419, "name": "Westminster", "iata": "LON"},
    "kensington": {"lat": 51.4991, "lon": -0.1938, "name": "South Kensington", "iata": "LON"},
    "camden": {"lat": 51.5390, "lon": -0.1426, "name": "Camden", "iata": "LON"},
    "shoreditch": {"lat": 51.5255, "lon": -0.0780, "name": "Shoreditch", "iata": "LON"},
    "covent garden": {"lat": 51.5117, "lon": -0.1234, "name": "Covent Garden", "iata": "LON"},
    "city": {"lat": 51.5155, "lon": -0.0922, "name": "City of London", "iata": "LON"},
    "notting hill": {"lat": 51.5099, "lon": -0.1959, "name": "Notting Hill", "iata": "LON"},
    "greenwich": {"lat": 51.4826, "lon": -0.0077, "name": "Greenwich", "iata": "LON"},
    "paddington": {"lat": 51.5154, "lon": -0.1755, "name": "Paddington", "iata": "LON"},
    "soho": {"lat": 51.5136, "lon": -0.1357, "name": "Soho", "iata": "LON"},
}

class HotelPriceService:
    """Service for fetching hotel prices using Amadeus API"""
    
    def __init__(self, amadeus_key: str = None, amadeus_secret: str = None):
        self.amadeus_key = amadeus_key
        self.amadeus_secret = amadeus_secret
        self.cache = {}
        self.cache_duration = 3600  # 1 hour
        
        # Initialize Amadeus client if credentials provided
        if self.amadeus_key and self.amadeus_secret:
            try:
                self.amadeus = Client(
                    client_id=self.amadeus_key,
                    client_secret=self.amadeus_secret
                )
                logger.info("Amadeus API client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Amadeus client: {e}")
                self.amadeus = None
        else:
            self.amadeus = None
            logger.warning("Amadeus API credentials not provided, using mock data")
    
    def get_london_areas(self) -> Dict[str, Dict]:
        """Get list of supported London areas"""
        return LONDON_AREAS
    
    async def search_hotels_rapidapi(
        self, 
        area: str,
        checkin_date: str,
        checkout_date: str,
        adults: int = 2,
        rooms: int = 1
    ) -> List[Dict]:
        """
        Search hotels using Amadeus Hotel API
        
        Returns:
            List of hotel dictionaries, or empty list if API not configured
        """
        if not self.amadeus:
            logger.error("Amadeus API not configured - cannot search hotels")
            return []
        
        # Check cache
        cache_key = f"{area}_{checkin_date}_{checkout_date}_{adults}_{rooms}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now().timestamp() - cached_time < self.cache_duration:
                logger.info("Returning cached hotel data")
                return cached_data
        
        area_data = LONDON_AREAS.get(area.lower())
        if not area_data:
            logger.error(f"Unknown area: {area}")
            return []
        
        try:
            # Search hotels by city code
            response = self.amadeus.reference_data.locations.hotels.by_city.get(
                cityCode='LON'
            )
            
            if not response.data:
                logger.warning("No hotels found in Amadeus response")
                return []
            
            # Get hotel IDs near the area
            hotel_ids = []
            for hotel in response.data[:20]:
                if hotel.get('geoCode'):
                    lat = hotel['geoCode'].get('latitude', 0)
                    lon = hotel['geoCode'].get('longitude', 0)
                    
                    # Calculate distance
                    lat_diff = abs(lat - area_data['lat'])
                    lon_diff = abs(lon - area_data['lon'])
                    distance = ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5
                    
                    # Include hotels within ~3km
                    if distance < 0.03:
                        hotel_ids.append(hotel.get('hotelId'))
            
            if not hotel_ids:
                logger.warning(f"No hotels found near {area}")
                return []
            
            # Get hotel offers
            hotels = []
            for hotel_id in hotel_ids[:5]:
                try:
                    offers_response = self.amadeus.shopping.hotel_offers_search.get(
                        hotelIds=hotel_id,
                        checkInDate=checkin_date,
                        checkOutDate=checkout_date,
                        adults=adults,
                        roomQuantity=rooms,
                        currency='GBP'
                    )
                    
                    if offers_response.data:
                        for offer_data in offers_response.data:
                            hotel_info = self._parse_amadeus_hotel(offer_data, area_data)
                            if hotel_info:
                                hotels.append(hotel_info)
                                
                except ResponseError as e:
                    logger.warning(f"Error getting offers for hotel {hotel_id}: {e}")
                    continue
            
            # Cache and return results
            if hotels:
                hotels.sort(key=lambda x: x['price'])
                self.cache[cache_key] = (hotels[:5], datetime.now().timestamp())
                return hotels[:5]
            else:
                logger.warning(f"No available hotels found for {area} on {checkin_date}")
                return []
                
        except ResponseError as e:
            logger.error(f"Amadeus API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching hotels: {e}")
            return []
    
    def _parse_amadeus_hotel(self, data: Dict, area_data: Dict) -> Optional[Dict]:
        """Parse Amadeus hotel offer response"""
        try:
            hotel = data.get('hotel', {})
            offers = data.get('offers', [])
            
            if not offers:
                return None
            
            # Get the cheapest offer
            offer = min(offers, key=lambda x: float(x.get('price', {}).get('total', 999999)))
            price_info = offer.get('price', {})
            
            hotel_info = {
                'name': hotel.get('name', 'Unknown Hotel'),
                'price': float(price_info.get('total', 0)),
                'currency': price_info.get('currency', 'GBP'),
                'rating': float(hotel.get('rating', 0)) * 2,  # Convert 0-5 to 0-10
                'stars': int(hotel.get('hotelId', '').count('STAR') if 'STAR' in hotel.get('hotelId', '') else 3),
                'address': f"{hotel.get('name', area_data['name'])}, London",
                'distance_to_center': f"{hotel.get('cityCode', 'Central London')}",
                'review_count': 0,
                'amenities': offer.get('room', {}).get('typeEstimated', {}).get('category', ''),
            }
            
            return hotel_info if hotel_info['price'] > 0 else None
            
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error parsing Amadeus hotel: {e}")
            return None
