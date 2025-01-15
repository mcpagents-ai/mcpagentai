import json
from typing import Dict, Any, Optional

from mcpagentai.tools.twitter.query_handler import QueryHandler
from mcpagentai.defs import CurrencyTools
from mcpagentai.tools.currency_agent import CurrencyAgent
from mcpagentai.core.logging import get_logger

class CurrencyQueryHandler(QueryHandler):
    def __init__(self):
        self.currency_agent = CurrencyAgent()
        self.logger = get_logger("mcpagentai.currency_handler")
        
        # Common currency aliases
        self.currency_aliases = {
            "dollar": "USD",
            "usd": "USD",
            "euro": "EUR",
            "eur": "EUR",
            "pound": "GBP",
            "gbp": "GBP",
            "yen": "JPY",
            "jpy": "JPY",
            "yuan": "CNY",
            "cny": "CNY",
            "cad": "CAD",
            "canadian dollar": "CAD",
            "canadian": "CAD",
            "bitcoin": "BTC",
            "btc": "BTC",
            "eth": "ETH"
        }
    
    @property
    def query_type(self) -> str:
        return "currency"
    
    @property
    def available_params(self) -> Dict[str, str]:
        return {
            "base_currency": "Source currency code or common name (e.g., 'USD', 'euro')",
            "target_currency": "Target currency code or common name (e.g., 'EUR', 'yen')",
            "amount": "Amount to convert (optional, defaults to 1)"
        }
    
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        try:
            # Get currency codes from params
            base = params.get("base_currency", "").lower()
            target = params.get("target_currency", "").lower()
            amount = float(params.get("amount", 1))
            
            # Convert aliases to codes
            base_code = self.currency_aliases.get(base, base.upper())
            target_code = self.currency_aliases.get(target, target.upper())
            
            # Default to USD->EUR if no currencies provided
            base_code = base_code or "USD"
            target_code = target_code or "EUR"
            
            # Get conversion data
            conversion = self.currency_agent.call_tool(
                CurrencyTools.CONVERT_CURRENCY.value, 
                {
                    "base_currency": base_code,
                    "target_currency": target_code,
                    "amount": amount
                }
            )
            
            if conversion and conversion[0].text:
                result = json.loads(conversion[0].text)
                if "converted_amount" in result:
                    formatted_amount = "{:.2f}".format(float(result["converted_amount"]))
                    rate = float(result["converted_amount"]) / amount
                    formatted_rate = "{:.4f}".format(rate)
                    
                    # Build a more informative response
                    response = [
                        f"💱 Exchange Rate: 1 {base_code} = {formatted_rate} {target_code}",
                        f"🔄 Conversion: {amount:,.2f} {base_code} = {formatted_amount} {target_code}"
                    ]
                    
                    # Add date if available
                    if "date" in result and result["date"] != "unknown":
                        response.append(f"📅 As of: {result['date']}")
                        
                    return "\n".join(response)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in currency handler: {e}")
            return None
    
    @property
    def examples(self) -> Dict[str, str]:
        return {
            "Convert 100 USD to EUR": {"base_currency": "usd", "target_currency": "eur", "amount": 100},
            "How much is 50 euro in yen?": {"base_currency": "euro", "target_currency": "yen", "amount": 50},
            "Bitcoin price in USD": {"base_currency": "btc", "target_currency": "usd", "amount": 1},
            "Convert 1000 yuan to dollars": {"base_currency": "cny", "target_currency": "usd", "amount": 1000}
        } 