from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, ErrorData
from mcp.shared.exceptions import McpError


from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import NBATools, NBAGetSchedulesData, NBAGetAllTeamsData, NBAGetAllActivePlayersData
from mcpagentai.defs import XXLMagTools, XXLMagGetLatestArticle

from bs4 import BeautifulSoup

from typing import Sequence, Union
import requests
import json
import os



class XXLMagAgent(MCPAgent):
    __base_url = "https://www.xxlmag.com"
    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=XXLMagTools.GET_LATEST_ARTICLE.value,
                 description="Get latest article url from xxl mag",
                 inputSchema={"type": "object",
                              "properties": {
                                  "question": {
                                      "type": "string",
                                      "description": "Get latest article from xxl mag"
                                  }
                              }
                              }
                 )
        ]
    
    def call_tool(self, 
                  name: str, 
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == NBATools.GET_ALL_TEAMS_DATA.value:
            return self._handler_get_latest_article(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}") 

    
    def _handler_get_latest_article(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question")
        self.logger.debug(f"Received question about: {question}")
        result = self._get_latest_article()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]
    
    def _get_latest_article(self) -> XXLMagGetLatestArticle:
        response = requests.get(self.__base_url)
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.find_all("a")
        
        latest_article_url = f"{self.__base_url}{elements[2].get("href")}"
        return XXLMagGetLatestArticle(article_url=latest_article_url)