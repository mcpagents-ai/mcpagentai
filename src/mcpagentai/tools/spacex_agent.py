from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, ErrorData
from mcp.shared.exceptions import McpError


from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import SpaceXTools, SpaceXGetLatestLaunches

from typing import Sequence, Union
import requests
import json



class SpaceXAgent(MCPAgent):
    __base_url = "https://api.spacexdata.com/v5/launches"
    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=SpaceXTools.GET_LATEST_LAUNCHES.value,
                 description="Get latest launches of SpaceX rocket",
                 inputSchema={"type": "object",
                              "properties": {
                                  "question": {
                                      "type": "string",
                                      "description": "Get latest spacex launches data"
                                  }
                              }
                              }
                 )
        ]
    
    def call_tool(self, 
                  name: str, 
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == SpaceXTools.GET_LATEST_LAUNCHES.value:
            return self._handler_get_latest_launches(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}") 

    
    def _handler_get_latest_launches(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question")
        self.logger.debug(f"Received question about: {question}")
        result = self._get_latest_launches()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]
    
    def _get_latest_launches(self) -> SpaceXGetLatestLaunches:
        url = f"{self.__base_url}/latest"
        response = requests.get(url)
        data = response.json()
        return SpaceXGetLatestLaunches(launches_data=data)