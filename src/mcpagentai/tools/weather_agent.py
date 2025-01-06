import json
from typing import Sequence, Union
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import WeatherTools, CurrentWeatherResult, WeatherForecastResult


class WeatherAgent(MCPAgent):
    """
    Agent that handles weather functionality (current weather, forecast).
    """

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=WeatherTools.GET_CURRENT_WEATHER.value,
                description="Get current weather for a specific location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or lat/long for weather query",
                        },
                    },
                    "required": ["location"],
                },
            ),
            Tool(
                name=WeatherTools.FORECAST.value,
                description="Get forecast for a specific location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or lat/long for weather forecast",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to forecast",
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

    def _get_current_weather(self, location: str) -> CurrentWeatherResult:
        """
        Stubbed/mocked. In reality, you'd call an external weather API (OpenWeatherMap, etc.).
        """
        return CurrentWeatherResult(
            location=location,
            temperature=23.4,
            description="Partly cloudy"
        )

    def _get_forecast(self, location: str, days: int) -> WeatherForecastResult:
        """
        Stubbed/mocked. In reality, you'd retrieve from a weather API.
        """
        mock_forecast_data = [
            {
                "day": i+1,
                "description": "Mostly sunny",
                "high": 22 + i,
                "low": 15 - i
            }
            for i in range(days)
        ]
        return WeatherForecastResult(
            location=location,
            forecast=mock_forecast_data
        )
