import os
import json
import requests
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import CryptoTools

class CryptoAgent(MCPAgent):
    """
    Agent that handles cryptocurrency functionality using CoinGecko API
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        super().__init__()
        
        # Common ID mappings (symbol -> coingecko_id)
        self.coin_ids = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "ADA": "cardano",
            "XRP": "ripple",
            "DOT": "polkadot",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network",
            "LINK": "chainlink"
        }

    def list_tools(self) -> list[Tool]:
        """List available crypto tools"""
        return [
            Tool(
                name=CryptoTools.GET_CRYPTO_PRICE.value,
                description="Get current price and 24h change for a cryptocurrency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH)"
                        }
                    },
                    "required": ["symbol"]
                }
            ),
            Tool(
                name=CryptoTools.GET_CRYPTO_INFO.value,
                description="Get detailed information about a cryptocurrency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Cryptocurrency symbol (e.g., BTC, ETH)"
                        }
                    },
                    "required": ["symbol"]
                }
            )
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Route tool calls to appropriate handlers"""
        if name == CryptoTools.GET_CRYPTO_PRICE.value:
            return self._handle_get_price(arguments)
        elif name == CryptoTools.GET_CRYPTO_INFO.value:
            return self._handle_get_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_get_price(self, arguments: dict) -> Sequence[TextContent]:
        """Get current price and 24h change for a cryptocurrency"""
        symbol = arguments.get("symbol", "").upper()
        
        # Get coin ID from symbol
        coin_id = self.coin_ids.get(symbol)
        if not coin_id:
            self.logger.error(f"Unknown cryptocurrency symbol: {symbol}")
            return [TextContent(type="text", text=json.dumps({"error": "Unknown cryptocurrency"}))]
            
        try:
            # Call CoinGecko API
            url = f"{self.BASE_URL}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            
            self.logger.info(f"Fetching price data for {symbol} ({coin_id})")
            response = requests.get(url, params=params)
            data = response.json()
            
            if coin_id in data:
                result = {
                    "symbol": symbol,
                    "price_usd": data[coin_id]["usd"],
                    "change_24h": data[coin_id].get("usd_24h_change")
                }
                return [TextContent(type="text", text=json.dumps(result))]
            else:
                self.logger.error(f"No price data found for {symbol}")
                return [TextContent(type="text", text=json.dumps({"error": "No price data found"}))]
                
        except Exception as e:
            self.logger.error(f"Error fetching price: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    def _handle_get_info(self, arguments: dict) -> Sequence[TextContent]:
        """Get detailed information about a cryptocurrency"""
        symbol = arguments.get("symbol", "").upper()
        
        # Get coin ID from symbol
        coin_id = self.coin_ids.get(symbol)
        if not coin_id:
            self.logger.error(f"Unknown cryptocurrency symbol: {symbol}")
            return [TextContent(type="text", text=json.dumps({"error": "Unknown cryptocurrency"}))]
            
        try:
            # Call CoinGecko API
            url = f"{self.BASE_URL}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false"
            }
            
            self.logger.info(f"Fetching info for {symbol} ({coin_id})")
            response = requests.get(url, params=params)
            data = response.json()
            
            result = {
                "symbol": symbol,
                "name": data["name"],
                "description": data["description"]["en"],
                "website": data["links"]["homepage"][0],
                "explorer": data["links"]["blockchain_site"][0],
                "rank": data["market_cap_rank"],
                "total_supply": data["market_data"]["total_supply"],
                "circulating_supply": data["market_data"]["circulating_supply"]
            }
            return [TextContent(type="text", text=json.dumps(result))]
                
        except Exception as e:
            self.logger.error(f"Error fetching info: {e}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))] 