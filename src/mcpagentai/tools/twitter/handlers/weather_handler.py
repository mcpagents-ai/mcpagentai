import json
from typing import Dict, Any, Optional, List

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.defs import WeatherTools
from mcpagentai.tools.weather_agent import WeatherAgent
from mcpagentai.core.logging import get_logger

class WeatherQueryHandler(QueryHandler):
    def __init__(self):
        super().__init__()
        self.weather_agent = WeatherAgent()
        self.logger = get_logger("mcpagentai.weather_handler")
        
        # Common city coordinates
        self.city_coords = {
            'sf': '37.7749,-122.4194',
            'nyc': '40.7128,-74.0060',
            'london': '51.5074,-0.1278',
            'tokyo': '35.6762,139.6503',
            'paris': '48.8566,2.3522',
            'berlin': '52.5200,13.4050',
            'osaka': '34.6937,135.5023',  # Added Osaka
            'singapore': '1.3521,103.8198',
            'sydney': '-33.8688,151.2093',
            'dubai': '25.2048,55.2708',
            'mumbai': '19.0760,72.8777',
            'seoul': '37.5665,126.9780',
            'hong kong': '22.3193,114.1694'  # Added Hong Kong
        }
    
    @property
    def query_type(self) -> str:
        return "weather"
    
    @property
    def available_params(self) -> Dict[str, Any]:
        return {
            "city": "City name (e.g. 'sf', 'nyc', 'london', 'tokyo', etc.)",
            "location": "Coordinates in 'lat,lon' format (e.g. '52.52,13.41')"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            location = None
            
            # Check for city parameter first
            if "city" in params:
                city = params["city"].lower()
                # Try to find city in our predefined coordinates
                if city in self.city_coords:
                    location = self.city_coords[city]
                else:
                    # If city not found, default to San Francisco
                    self.logger.warning(f"City '{city}' not found in coordinates list, defaulting to San Francisco")
                    location = self.city_coords['sf']
            
            # If no city provided, check for direct coordinates
            elif "location" in params:
                location = params["location"]
            
            # Default to San Francisco if no location specified
            else:
                location = self.city_coords['sf']

            # Get weather data
            weather_data = self.weather_agent.call_tool(
                WeatherTools.GET_CURRENT_WEATHER.value,
                {"location": location}
            )
            
            if isinstance(weather_data, list) and len(weather_data) > 0:
                try:
                    # Parse the JSON response
                    data = json.loads(weather_data[0].text)
                    
                    # Extract temperature and description
                    temp = data.get("temperature", 0.0)
                    desc = data.get("description", "unknown conditions")
                    
                    # Format temperature to one decimal place
                    temp_formatted = "{:.1f}".format(float(temp))
                    
                    # Return formatted weather string
                    return f"{temp_formatted}°F, {desc}"
                    
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.error(f"Error parsing weather data: {str(e)}")
                    return "Error: Could not parse weather data"
                    
            return "Error: No weather data available"

        except Exception as e:
            self.logger.error(f"Error in weather handler: {str(e)}")
            return f"Error in weather handler: {str(e)}"
    
    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "query": "What's the weather in Tokyo?",
                "params": {"city": "tokyo"}
            },
            {
                "query": "How's the weather in San Francisco?",
                "params": {"city": "sf"}
            },
            {
                "query": "Weather at coordinates 52.52,13.41",
                "params": {"location": "52.52,13.41"}
            }
        ] 