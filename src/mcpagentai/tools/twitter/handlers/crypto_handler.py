import json
from typing import Dict, Any, Optional

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.tools.crypto_agent import CryptoAgent
from mcpagentai.defs import CryptoTools
from mcpagentai.core.logging import get_logger

class CryptoQueryHandler(QueryHandler):
    def __init__(self):
        self.crypto_agent = CryptoAgent()
        self.logger = get_logger("mcpagentai.crypto_handler")
        
        # Common crypto aliases
        self.crypto_aliases = {
            "bitcoin": "BTC",
            "btc": "BTC",
            "ethereum": "ETH",
            "eth": "ETH",
            "dogecoin": "DOGE",
            "doge": "DOGE",
            "cardano": "ADA",
            "ada": "ADA",
            "solana": "SOL",
            "sol": "SOL",
            "ripple": "XRP",
            "xrp": "XRP",
            "polkadot": "DOT",
            "dot": "DOT"
        }
    
    @property
    def query_type(self) -> str:
        return "crypto"
    
    @property
    def available_params(self) -> Dict[str, str]:
        return {
            "symbol": "Cryptocurrency symbol or common name (e.g., 'BTC', 'ethereum')",
            "quote_currency": "Quote currency (e.g., 'USD', 'USDT'). Defaults to USDT.",
            "detailed": "Whether to fetch detailed ticker info (optional, defaults to False)"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            # Accept either 'symbol' or 'coin' parameter
            symbol = params.get("symbol") or params.get("coin")
            if not symbol:
                self.logger.warning("No symbol/coin provided in params")
                return None
                
            # Convert to lowercase for alias lookup
            symbol = symbol.lower()
            
            # Convert alias to symbol
            symbol = self.crypto_aliases.get(symbol, symbol.upper())
            self.logger.info(f"Looking up price for {symbol}")
            
            # Get crypto data
            crypto_data = self.crypto_agent.call_tool(
                CryptoTools.GET_CRYPTO_PRICE.value,
                {"symbol": symbol}
            )
            
            if crypto_data and crypto_data[0].text:
                result = json.loads(crypto_data[0].text)
                self.logger.debug(f"Got crypto data: {result}")
                
                if "price_usd" in result:
                    price = float(result["price_usd"])
                    formatted_price = "${:,.2f}".format(price)
                    change = result.get("change_24h", 0)
                    change_emoji = "📈" if change and change > 0 else "📉" if change and change < 0 else "➡️"
                    
                    response = [
                        f"{symbol} Price: {formatted_price} USD {change_emoji}"
                    ]
                    
                    if change:
                        formatted_change = "{:+.2f}%".format(change)
                        response.append(f"24h Change: {formatted_change}")
                    
                    response_text = "\n".join(response)
                    self.logger.info(f"Generated response: {response_text}")
                    return response_text
                else:
                    self.logger.warning(f"No price data in response for {symbol}")
            else:
                self.logger.warning(f"No response from crypto agent for {symbol}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in crypto handler: {e}")
            return None
    
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "What's the Bitcoin price?": {"symbol": "btc", "quote_currency": "USDT"},
            "Show me ETH details": {"symbol": "eth", "quote_currency": "USDT", "detailed": True},
            "Price of Dogecoin in USD": {"symbol": "doge", "quote_currency": "USD"},
            "How much is Solana?": {"symbol": "sol", "quote_currency": "USDT"}
        } 