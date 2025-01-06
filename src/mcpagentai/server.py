import json
from typing import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, ImageContent, EmbeddedResource

from .core.logging import get_logger
from .core.multi_tool_agent import MultiToolAgent

# Import the specific tool agents
from .tools.time_agent import TimeAgent
from .tools.weather_agent import WeatherAgent
from .tools.dictionary_agent import DictionaryAgent
from .tools.calculator_agent import CalculatorAgent


async def start_server(local_timezone: str | None = None) -> None:
    logger = get_logger("mcpagentai.server")
    logger.info("Starting MCPAgentAI server...")

    # Instantiate sub-agents
    time_agent = TimeAgent(local_timezone=local_timezone)
    weather_agent = WeatherAgent()
    dictionary_agent = DictionaryAgent()
    calculator_agent = CalculatorAgent()

    # Combine them into one aggregator
    multi_tool_agent = MultiToolAgent([
        time_agent,
        weather_agent,
        dictionary_agent,
        calculator_agent,
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
            logger.error(f"Error in call_tool: {str(e)}")
            raise ValueError(f"Error processing request: {str(e)}") from e

    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Running server on stdio_server...")
        await server.run(read_stream, write_stream, options)
