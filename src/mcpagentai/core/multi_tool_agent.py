from typing import Sequence, Union
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .agent_base import MCPAgent


class MultiToolAgent(MCPAgent):
    """
    A composite agent that combines multiple MCPAgent subclasses
    under a single interface.
    """

    def __init__(self, agents: list[MCPAgent]):
        super().__init__()
        self._agents = agents
        self.logger.info(f"Initialized MultiToolAgent with {len(self._agents)} sub-agents.")

    def list_tools(self) -> list[Tool]:
        """
        Return the union of all tools from each sub-agent.
        """
        combined_tools = []
        for agent in self._agents:
            combined_tools.extend(agent.list_tools())
        return combined_tools

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Route the tool call to whichever agent implements it.
        """
        for agent in self._agents:
            if agent.has_tool(name):
                return agent.call_tool(name, arguments)
        raise ValueError(f"Unknown tool: {name}")
