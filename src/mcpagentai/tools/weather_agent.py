import json
import requests
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import WeatherTools, CurrentWeatherResult, WeatherForecastResult


# A simple mapping from Open-Meteo weathercode to textual description:
WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail"
}


class WeatherAgent(MCPAgent):
    """
    Agent that handles weather functionality (current weather, forecast)
    using the free Open-Meteo API.
    Expects 'location' to be in 'lat,lon' format (e.g., '52.52,13.41').
    """

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=WeatherTools.GET_CURRENT_WEATHER.value,
                description="Get current weather for a specific location (lat,lon).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Coordinates in 'lat,lon' format (e.g. '52.52,13.41')",
                        },
                    },
                    "required": ["location"],
                },
            ),
            Tool(
                name=WeatherTools.FORECAST.value,
                description="Get forecast for a specific location (lat,lon).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Coordinates in 'lat,lon' format (e.g. '52.52,13.41')",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to forecast (1-7 recommended for daily).",
                        },
                    },
                    "required": ["location"],
                },
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == WeatherTools.GET_CURRENT_WEATHER.value:
            return self._handle_get_current_weather(arguments)
        elif name == WeatherTools.FORECAST.value:
            return self._handle_forecast(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_get_current_weather(self, arguments: dict) -> Sequence[TextContent]:
        location = arguments.get("location", "")
        result = self._get_current_weather(location)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _handle_forecast(self, arguments: dict) -> Sequence[TextContent]:
        location = arguments.get("location", "")
        days = arguments.get("days", 3)
        result = self._get_forecast(location, days)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _parse_lat_lon(self, location: str) -> tuple[float, float]:
        """
        Expects a string like '52.52,13.41'.
        Returns (52.52, 13.41) as floats.
        """
        try:
            lat_str, lon_str = location.split(",")
            return float(lat_str.strip()), float(lon_str.strip())
        except Exception:
            raise ValueError(
                "Location must be in 'lat,lon' format (e.g. '52.52,13.41')."
            )

    def _get_current_weather(self, location: str) -> CurrentWeatherResult:
        """
        Calls the Open-Meteo API for current weather.
        """
        lat, lon = self._parse_lat_lon(location)

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "timezone": "auto"  # Let the API pick best timezone
        }

        resp = requests.get(url, params=params)
        data = resp.json()

        # Example structure:
        # {
        #   "latitude": 52.52,
        #   "longitude": 13.419998,
        #   "generationtime_ms": 0.62,
        #   "utc_offset_seconds": 7200,
        #   "timezone": "Europe/Berlin",
        #   "timezone_abbreviation": "CEST",
        #   "elevation": 38.0,
        #   "current_weather": {
        #       "temperature": 16.4,
        #       "windspeed": 2.6,
        #       "winddirection": 316.0,
        #       "weathercode": 0,
        #       "time": "2025-01-07T12:00"
        #   }
        # }
        if "current_weather" not in data:
            raise ValueError("No current weather data found for the given location.")

        cw = data["current_weather"]
        weathercode = cw.get("weathercode", 0)
        description = WEATHER_CODE_MAP.get(weathercode, "Unknown weather conditions")

        return CurrentWeatherResult(
            location=f"{lat},{lon}",
            temperature=cw.get("temperature", 0.0),
            description=description
        )

    def _get_forecast(self, location: str, days: int) -> WeatherForecastResult:
        """
        Calls the Open-Meteo API for daily forecast up to 7 (or more) days.
        """
        lat, lon = self._parse_lat_lon(location)

        # We'll fetch daily weathercode, max temp, min temp
        # Open-Meteo by default can provide up to 7 or 14 days.
        # We'll just request up to 7 days to be safe (or you can request 16).
        if days < 1:
            days = 1
        elif days > 7:
            days = 7  # or 16 if you prefer

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }

        resp = requests.get(url, params=params)
        data = resp.json()

        if "daily" not in data:
            raise ValueError("No daily forecast data found for the given location.")

        daily_data = data["daily"]

        # daily_data example structure:
        # {
        #   "time": ["2025-01-07", "2025-01-08", ...],
        #   "weathercode": [0, 2, ...],
        #   "temperature_2m_max": [17.0, 19.5, ...],
        #   "temperature_2m_min": [8.1, 10.2, ...]
        # }
        time_list = daily_data.get("time", [])
        code_list = daily_data.get("weathercode", [])
        max_list = daily_data.get("temperature_2m_max", [])
        min_list = daily_data.get("temperature_2m_min", [])

        forecast_items = []
        for i in range(min(days, len(time_list))):
            weathercode = code_list[i] if i < len(code_list) else 0
            desc = WEATHER_CODE_MAP.get(weathercode, "Unknown weather conditions")
            high = max_list[i] if i < len(max_list) else 0.0
            low = min_list[i] if i < len(min_list) else 0.0

            forecast_items.append({
                "day": i + 1,
                "date": time_list[i] if i < len(time_list) else "Unknown",
                "description": desc,
                "high": high,
                "low": low
            })

        return WeatherForecastResult(
            location=f"{lat},{lon}",
            forecast=forecast_items
        )
