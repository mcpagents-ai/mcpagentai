from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import StockTools, StockGetPrice, StockGetTickerByNameAgent

from typing import Sequence, Union

import requests

import json


class StockAgent(MCPAgent):
    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=StockTools.GET_TICKER_BY_NAME.value,
                 description="Get list of stock tickers by keyword",
                 inputSchema={"type": "object",
                              "properties": {
                                  "keyword": {
                                      "type": "string",
                                      "description": "Keyword of stock name"
                                  },
                                  "required": ["keyword"]
                              }
                              }
                 ),
            Tool(name=StockTools.GET_STOCK_PRICE_TODAY.value,
                 description="Get bio of specific eliza character",
                 inputSchema={
                     "type": "object",
                     "properties":
                         {
                             "ticker":
                                 {
                                     "type": "string",
                                     "description": "Ticker of stock"
                                 },
                             "required": ["ticker"]
                         }
                 })
        ]

    def call_tool(self,
                  name: str,
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == StockTools.GET_TICKER_BY_NAME.value:
            return self._handle_get_ticker_by_name(arguments)
        elif name == StockTools.GET_STOCK_PRICE_TODAY.value:
            return self._handle_get_stock_price_today(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}")

    def _handle_get_ticker_by_name(self, arguments: dict) -> Sequence[TextContent]:
        keyword = arguments.get("keyword")
        result = self._get_ticker_by_name(keyword)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _handle_get_stock_price_today(self, arguments: dict) -> Sequence[TextContent]:
        ticker = arguments.get("ticker")
        result = self._get_stock_price_today(ticker)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _get_ticker_by_name(self, ticker: str) -> StockGetTickerByNameAgent:
        # todo add request success error handling
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={ticker}&apikey=demo%27)"
        response = requests.get(url)
        data = response.json()
        return StockGetTickerByNameAgent(tickers=data['bestMatches'])

    def _get_stock_price_today(self, ticker: str) -> StockGetPrice:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey=demo"
        response = requests.get(url)
        data = response.json()
        price_series = data['Time Series (Daily)']
        last_day = next(iter(price_series))
        return StockGetPrice(price=price_series[last_day]['4. close'])