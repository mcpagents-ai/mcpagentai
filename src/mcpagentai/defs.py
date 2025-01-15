"""
Shared data models used across multiple tools (pydantic BaseModels, Enums, etc.).
"""

from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Optional


# -------------------------------------------------------------------------
# TIME MODELS (example if you have them)
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# WEATHER MODELS (example if you have them)
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# CURRENCY MODELS (example if you have them)
# -------------------------------------------------------------------------
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


# -------------------------------------------------------------------------
# ELIZA MODELS & ENUMS (Remote HTTP-based)
# -------------------------------------------------------------------------
class ElizaTools(str, Enum):
    GET_AGENTS = "get_eliza_agents"
    MESSAGE_AGENT = "message_eliza_agent"

class ElizaGetAgents(BaseModel):
    """Returns a list of agent names from a remote Eliza server."""
    agents: List[str]

class ElisaMessageAgent(BaseModel):
    """Returns a single message from a specific Eliza agent."""
    agent_message: str


# -------------------------------------------------------------------------
# ELIZA PARSER (Local file-based) MODELS & ENUMS
# -------------------------------------------------------------------------
class ElizaParserTools(str, Enum):
    GET_CHARACTERS = "get_characters"
    GET_CHARACTER_BIO = "get_character_bio"
    GET_CHARACTER_LORE = "get_character_lore"
    GET_FULL_AGENT_INFO = "get_full_agent_info"
    INTERACT_WITH_AGENT = "interact_with_agent"

class ElizaGetCharacters(BaseModel):
    """List of local character JSON files."""
    characters: List[str]

class ElizaGetCharacterBio(BaseModel):
    """Bio content for a single character."""
    characters: str

class ElizaGetCharacterLore(BaseModel):
    """Lore content for a single character."""
    characters: str


# -- STOCK MODELS ------------------------------------------ #

class StockTools(str, Enum):
    GET_TICKER_BY_NAME = "get_ticker_by_name"
    GET_STOCK_PRICE_TODAY = "get_stock_price"
    GET_STOCK_PRICE_HISTORY = "get_stock_price_history"

class StockGetTickerByNameAgent(BaseModel):
    tickers: List[str]

class StockGetPrice(BaseModel):
    price: float

class StockGetPriceHistory(BaseModel):
    prices: Dict

# -- TWITTER MODELS ------------------------------------------ #

class TwitterTools(str, Enum):
    CREATE_TWEET = "create_tweet"
    REPLY_TWEET = "reply_tweet"

class TwitterResult(BaseModel):
    """
    Minimal response model for tweet creation or reply.
    """
    success: bool
    message: Optional[str] = None
    tweet_url: Optional[str] = None
    error: Optional[str] = None


# -------------------------------------------------------------------------
# CRYPTO MODELS
# -------------------------------------------------------------------------
class CryptoTools(str, Enum):
    GET_CRYPTO_PRICE = "get_crypto_price"
    GET_CRYPTO_INFO = "get_crypto_info"

class CryptoPriceResult(BaseModel):
    symbol: str
    price_usd: float
    price_btc: Optional[float]
    market_cap: Optional[float]
    volume_24h: Optional[float]
    change_24h: Optional[float]
    last_updated: str

class CryptoInfoResult(BaseModel):
    symbol: str
    name: str
    description: Optional[str]
    website: Optional[str]
    explorer: Optional[str]
    rank: Optional[int]
    total_supply: Optional[float]
    circulating_supply: Optional[float]