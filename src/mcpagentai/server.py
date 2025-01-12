import json
import logging
from typing import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.logging import get_logger
from mcpagentai.core.multi_tool_agent import MultiToolAgent

# Sub-agents
from mcpagentai.tools.calculator_agent import CalculatorAgent
from mcpagentai.tools.currency_agent import CurrencyAgent
from mcpagentai.tools.dictionary_agent import DictionaryAgent
from mcpagentai.tools.eliza.agent import ElizaAgent
from mcpagentai.tools.eliza.mcp_agent import ElizaMCPAgent
from mcpagentai.tools.stock_agent import StockAgent
from mcpagentai.tools.time_agent import TimeAgent
from mcpagentai.tools.twitter.agent import TwitterAgent
from mcpagentai.tools.weather_agent import WeatherAgent

async def start_server(local_timezone: str | None = None) -> None:
    logger = get_logger("mcpagentai.server")
    logger.info("Starting MCPAgentAI server...")

    time_agent = TimeAgent(local_timezone=local_timezone)
    weather_agent = WeatherAgent()
    dictionary_agent = DictionaryAgent()
    calculator_agent = CalculatorAgent()
    currency_agent = CurrencyAgent()
    eliza_agent = ElizaAgent()
    eliza_mcp_agent = ElizaMCPAgent()
    stock_agent = StockAgent()
    twitter_agent = TwitterAgent()

    # Combine them into one aggregator
    multi_tool_agent = MultiToolAgent([
        # time_agent,
        # weather_agent,
        # dictionary_agent,
        # calculator_agent,
        # currency_agent,
        # eliza_agent,
        eliza_mcp_agent,
        stock_agent,
        twitter_agent,
    ])

    server = Server("mcpagentai")

    @server.list_tools()
    async def list_tools():
        """
        List all available tools.
        """
        logger.debug("server.list_tools called")
        return multi_tool_agent.list_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """
        Dispatch calls to the aggregator agent, which routes to the correct sub-agent.
        """
        try:
            return multi_tool_agent.call_tool(name, arguments)
        except Exception as e:
            logger.exception("Error in call_tool")
            # Avoid using e.message. Use str(e) instead
            raise ValueError(f"Error processing request: {str(e)}") from e

    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Running server on stdio_server...")
        await server.run(read_stream, write_stream, options)
