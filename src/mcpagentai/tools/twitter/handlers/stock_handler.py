import json
import os
from typing import Dict, Any, Optional

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.defs import StockTools
from mcpagentai.tools.stock_agent import StockAgent

class StockQueryHandler(QueryHandler):
    def __init__(self):
        self.stock_agent = StockAgent()
        
        # Common stock tickers and their names
        self.tickers = {
            "apple": "AAPL",
            "google": "GOOGL",
            "microsoft": "MSFT",
            "nvidia": "NVDA",
            "amd": "AMD",
            "tesla": "TSLA",
            "amazon": "AMZN",
            "meta": "META",
            "spy": "SPY",  # S&P 500 ETF
            "qqq": "QQQ",  # NASDAQ ETF
            "dia": "DIA",  # Dow Jones ETF
            "iwm": "IWM"   # Russell 2000 ETF
        }
    
    @property
    def query_type(self) -> str:
        return "stock"
    
    @property
    def available_params(self) -> Dict[str, str]:
        return {
            "ticker": "Stock ticker symbol (e.g., AAPL, GOOGL)",
            "company": "Company name (e.g., Apple, Google)"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            if not os.getenv("ALPHA_VANTAGE_API_KEY"):
                return "API Limit Reached - Stock Data Unavailable"
                
            # Get ticker from params
            ticker = params.get("ticker", "").upper()
            company = params.get("company", "").lower()
            
            # If company name provided, try to get ticker
            if company and company in self.tickers:
                ticker = self.tickers[company]
            
            # Default to AAPL if no ticker provided
            ticker = ticker or "AAPL"
            
            # Get stock data
            try:
                stock_data = self.stock_agent.call_tool(StockTools.GET_STOCK_PRICE_TODAY.value, {"ticker": ticker})
                if stock_data and stock_data[0].text:
                    stock_json = json.loads(stock_data[0].text)
                    if "price" in stock_json:
                        formatted_price = "{:.2f}".format(float(stock_json["price"]))
                        return f"{ticker}: ${formatted_price}"
            except ValueError as e:
                print(f"Alpha Vantage API error: {e}")
                return "API Limit Reached - Stock Data Unavailable"
            
            return "API Limit Reached - Stock Data Unavailable"
            
        except Exception as e:
            print(f"Error in stock handler: {e}")
            return "API Limit Reached - Stock Data Unavailable"
    
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "What's the Apple stock price?": {"company": "apple"},
            "GOOGL price?": {"ticker": "GOOGL"},
            "How's NVIDIA doing?": {"company": "nvidia"},
            "What's the S&P 500 at?": {"ticker": "SPY"},
            "Price of TSLA?": {"ticker": "TSLA"}
        } 