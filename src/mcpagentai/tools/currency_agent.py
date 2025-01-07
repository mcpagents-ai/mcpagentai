import os
import json
import requests
from typing import Sequence, Union, Optional

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcpagentai.core.agent_base import MCPAgent

# Import your currency definitions from defs.py
from mcpagentai.defs import (
    CurrencyTools,
    ExchangeRateResult,
    ConversionResult
)


class CurrencyAgent(MCPAgent):
    """
    Agent that handles currency functionality:
    - retrieving latest exchange rates
    - converting an amount from one currency to another
    """

    BASE_URL = "https://api.freecurrencyapi.com/v1/latest"

    def __init__(self, api_key: str | None = None):
        """
        Initializes the CurrencyAgent with an API key.
        The API key can be passed directly or retrieved from the ACCESS_KEY environment variable.
        """
        super().__init__()
        self.api_key = api_key or os.getenv("FREECURRENCY_API_KEY", "<your_key>")
        if not self.api_key:
            raise ValueError("API key is missing! Set FREECURRENCY_API_KEY environment variable or pass it as an argument.")

    def list_tools(self) -> list[Tool]:
        """
        Returns a list of Tools that this agent can handle,
        matching the patterns from defs.py
        """
        return [
            Tool(
                name=CurrencyTools.GET_EXCHANGE_RATE.value,
                description="Get latest exchange rates from a base currency to one or more target currencies",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_currency": {
                            "type": "string",
                            "description": "The ISO currency code to use as the base (e.g., 'USD')",
                        },
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of target currency codes (e.g., ['EUR','GBP'])",
                        },
                    },
                    "required": ["base_currency", "symbols"],
                },
            ),
            Tool(
                name=CurrencyTools.CONVERT_CURRENCY.value,
                description="Convert an amount from one currency to another",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base_currency": {
                            "type": "string",
                            "description": "The ISO currency code to convert FROM (e.g., 'USD')",
                        },
                        "target_currency": {
                            "type": "string",
                            "description": "The ISO currency code to convert INTO (e.g., 'EUR')",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount of money to convert",
                        },
                    },
                    "required": ["base_currency", "target_currency", "amount"],
                },
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Routes the tool call to the appropriate handler method.
        """
        if name == CurrencyTools.GET_EXCHANGE_RATE.value:
            return self._handle_get_exchange_rate(arguments)
        elif name == CurrencyTools.CONVERT_CURRENCY.value:
            return self._handle_convert_currency(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    # -------------------------------------------------------------------
    # Tool Handlers
    # -------------------------------------------------------------------

    def _handle_get_exchange_rate(self, arguments: dict) -> Sequence[TextContent]:
        """
        Retrieves the latest exchange rates from a base currency to one or more targets.
        """
        base_currency = arguments.get("base_currency", "").upper()
        symbols = arguments.get("symbols", [])

        result = self._get_exchange_rate(base_currency, symbols)

        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]

    def _handle_convert_currency(self, arguments: dict) -> Sequence[TextContent]:
        """
        Converts a specific amount from a base currency to a target currency.
        """
        base_currency = arguments.get("base_currency", "").upper()
        target_currency = arguments.get("target_currency", "").upper()
        amount = arguments.get("amount", 1)

        # Ensure amount is a float
        amount = float(amount)

        result = self._convert_currency(base_currency, target_currency, amount)

        return [
            TextContent(
                type="text",
                text=json.dumps(result.model_dump(), indent=2)
            )
        ]

    # -------------------------------------------------------------------
    # Internal Methods (API calls, data processing, etc.)
    # -------------------------------------------------------------------

    def _get_exchange_rate(self, base_currency: str, symbols: list[str]) -> dict:
        """
        Calls FreeCurrencyAPI to retrieve exchange rates.
        """
        symbols_str = ",".join(symbols)
        params = {
            "apikey": self.api_key,
            "base_currency": base_currency,
            "currencies": symbols_str
        }

        try:
            resp = requests.get(self.BASE_URL, params=params)
            data = resp.json()

            if "error" in data:
                raise ValueError(f"API error: {data['error']}")

            rates = data.get("data", {})
            return {
                "base": base_currency,
                "rates": rates,
                "timestamp": data.get("timestamp")
            }
        except Exception as e:
            raise RuntimeError(f"Error calling exchange rate API: {e}")

    def _convert_currency(self, base_currency: str, target_currency: str, amount: float) -> ConversionResult:
        """
        Uses FreeCurrencyAPI rates to calculate currency conversion.
        """
        exchange_rates = self._get_exchange_rate(base_currency, [target_currency])
        rates = exchange_rates.get("rates", {})
        rate = rates.get(target_currency)

        if not rate:
            raise ValueError(f"Conversion rate for {target_currency} not found.")

        converted_amount = amount * rate
        timestamp = exchange_rates.get("timestamp")

        # Ensure the date is a valid string
        if timestamp:
            try:
                from datetime import datetime
                date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                date = "unknown"
        else:
            date = "unknown"

        return ConversionResult(
            base=base_currency,
            target=target_currency,
            amount=amount,
            converted_amount=converted_amount,
            date=date
        )

