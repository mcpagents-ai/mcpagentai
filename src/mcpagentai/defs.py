"""
Shared data models used across multiple tools (pydantic BaseModels, Enums, etc.).
"""

from enum import Enum
from pydantic import BaseModel
from typing import List, Dict


# -- TIME MODELS ---------------------------------------------------- #
class TimeTools(str, Enum):
    GET_CURRENT_TIME = "get_current_time"
    CONVERT_TIME = "convert_time"

class TimeResult(BaseModel):
    timezone: str
    datetime: str
    is_dst: bool

class TimeConversionResult(BaseModel):
    source: TimeResult
    target: TimeResult
    time_difference: str


# -- WEATHER MODELS ------------------------------------------------- #
class WeatherTools(str, Enum):
    GET_CURRENT_WEATHER = "get_current_weather"
    FORECAST = "get_weather_forecast"

class CurrentWeatherResult(BaseModel):
    location: str
    temperature: float
    description: str

class WeatherForecastResult(BaseModel):
    location: str
    forecast: List[Dict]


# -- DICTIONARY MODELS --------------------------------------------- #
# (No specific pydantic model needed for dictionary, but we could define one if desired)

# -- CALCULATOR MODELS --------------------------------------------- #
# (No specific pydantic model needed for calculator, but we could define one if desired)
