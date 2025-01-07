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


# -- CURRENCY MODELS ------------------------------------------------- #
class CurrencyTools(str, Enum):
    GET_EXCHANGE_RATE = "get_exchange_rate"
    CONVERT_CURRENCY = "convert_currency"

class ExchangeRateResult(BaseModel):
    base: str
    rates: Dict[str, float]
    date: str

class ConversionResult(BaseModel):
    base: str
    target: str
    amount: float
    converted_amount: float
    date: str
