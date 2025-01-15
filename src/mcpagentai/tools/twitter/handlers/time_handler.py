from typing import Dict, Any, Optional

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.tools.time_agent import TimeAgent

class TimeQueryHandler(QueryHandler):
    def __init__(self):
        self.time_agent = TimeAgent()
        
        # Common timezone aliases
        self.timezone_aliases = {
            "ny": "America/New_York",
            "nyc": "America/New_York",
            "est": "America/New_York",
            "la": "America/Los_Angeles",
            "sf": "America/Los_Angeles",
            "pst": "America/Los_Angeles",
            "london": "Europe/London",
            "uk": "Europe/London",
            "tokyo": "Asia/Tokyo",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin"
        }
    
    @property
    def query_type(self) -> str:
        return "time"
    
    @property
    def available_params(self) -> Dict[str, str]:
        return {
            "timezone": "Timezone name (e.g., America/New_York)",
            "city": "Common city name (e.g., 'nyc', 'sf', 'london')"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            # Get timezone from params
            timezone = params.get("timezone")
            city = params.get("city", "").lower()
            
            # If city is provided and in our list, use its timezone
            if city and city in self.timezone_aliases:
                timezone = self.timezone_aliases[city]
            
            # Default to NY if no timezone provided
            timezone = timezone or "America/New_York"
            
            # Get time data
            time_data = self.time_agent.call_tool("get_current_time", {"timezone": timezone})
            if time_data and time_data[0].text:
                return time_data[0].text
            
            return None
            
        except Exception as e:
            print(f"Error in time handler: {e}")
            return None
    
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "What time is it in NYC?": {"city": "nyc"},
            "Time in London?": {"city": "london"},
            "What's the time in Tokyo?": {"city": "tokyo"},
            "Current time in America/Los_Angeles?": {"timezone": "America/Los_Angeles"}
        } 