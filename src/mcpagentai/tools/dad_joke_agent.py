from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, ErrorData
from mcp.shared.exceptions import McpError


from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import DadJokeTools, DadJokeGetDadJoke

from typing import Sequence, Union
import requests
import json



class DadJokeAgent(MCPAgent):
    __base_url = "https://icanhazdadjoke.com"
    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=DadJokeTools.GET_DAD_JOKE.value,
                 description="Get some random dad joke",
                 inputSchema={"type": "object",
                              "properties": {
                                  "question": {
                                      "type": "string",
                                      "description": "Get dad joke"
                                  }
                              }
                              }
                 )
        ]
    
    def call_tool(self, 
                  name: str, 
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == DadJokeTools.GET_DAD_JOKE.value:
            return self._handler_get_dad_joke(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}") 

    
    def _handler_get_dad_joke(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question")
        self.logger.debug(f"Received question about: {question}")
        result = self._get_dad_joke()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]
    
    def _get_dad_joke(self) -> DadJokeGetDadJoke:
        response = requests.get(self.__base_url, headers={"Accept": "application/json"})
        data = response.json()
        return DadJokeGetDadJoke(joke=data["joke"])