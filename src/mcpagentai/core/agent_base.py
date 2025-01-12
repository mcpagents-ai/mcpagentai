import abc
from typing import Sequence, Union
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .logging import get_logger

class MCPAgent(abc.ABC):
    """
    Master abstract base class for MCP Agents of any type.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Initializing agent: {self.__class__.__name__}")

    @abc.abstractmethod
    def list_tools(self) -> list[Tool]:
        """
        Return a list of the tools provided by this agent.
        """
        pass

    @abc.abstractmethod
    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Call the specified tool by name with the given arguments,
        and return a sequence of textual/image/embedded resources (MCP content).
        """
        pass

    def has_tool(self, tool_name: str) -> bool:
        """
        Determine if this agent implements a tool by the given name.
        """
        return any(tool.name == tool_name for tool in self.list_tools())
