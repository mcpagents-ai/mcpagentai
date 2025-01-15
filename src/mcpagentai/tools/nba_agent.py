from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource, ErrorData
from mcp.shared.exceptions import McpError


from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import NBATools, NBAGetSchedulesData, NBAGetAllTeamsData, NBAGetAllActivePlayersData

from typing import Sequence, Union
import requests
import json
import os



class NBAAgent(MCPAgent):
    __base_url = "https://api.sportsdata.io/v3/nba/scores/json/"
    def __init__(self, sportsdataio_nba_key: str | None = None):
        super().__init__()
        self.api_key = sportsdataio_nba_key
        if self.api_key is None:
            self.api_key = os.getenv("SPORTS_DATA_NBA_IO_KEY")
            if self.api_key is None:
                raise ValueError(f"Api key not provided. Cant fidn in env and ")

    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=NBATools.GET_ALL_TEAMS_DATA.value,
                 description="Get list of all NBA teams",
                 inputSchema={"type": "object",
                              "properties": {
                                  "question": {
                                      "type": "string",
                                      "description": "Question for list all NBA teams"
                                  }
                              }
                              }
                 ),
            Tool(name=NBATools.GET_ALL_ACTIVE_PLAYERS_DATA.value,
                 description="Get all active NBA players data",
                 inputSchema={
                     "type": "object",
                     "properties":
                         {
                             "question":
                                 {
                                     "type": "string",
                                     "description": "Question for list all active players data"
                                 },
                         }
                 }),
            Tool(name=NBATools.GET_SCHEDULES_DATA.value,
                 description="Get schedules and results from selected NBA season",
                 inputSchema={
                     "type": "object",
                     "properties":
                         {
                             "season":
                                 {
                                     "type": "string",
                                     "description": "Year of season. F.e 2020, 2018PRE, 2020STAR, 2020POST"
                                 },
                             "required": ["season"]
                         }
                 })
        ]
    
    def call_tool(self, 
                  name: str, 
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == NBATools.GET_ALL_TEAMS_DATA.value:
            return self._handler_get_all_teams_data(arguments)
        elif name == NBATools.GET_ALL_ACTIVE_PLAYERS_DATA.value:
            return self._handler_get_all_active_players_data(arguments)
        elif name == NBATools.GET_SCHEDULES_DATA:
            return self._handler_get_all_teams_data(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}") 

    
    def _handler_get_all_teams_data(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question")
        self.logger.debug(f"Received question about: {question}")
        result = self._get_all_teams_data()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]
    
    def _handler_get_all_active_players_data(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question")
        self.logger.debug(f"Received question about: {question}")
        result = self._get_all_active_players_data()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]
    
    def _handler_get_schedules_data(self, arguments: dict) -> Sequence[TextContent]:
        season = arguments.get("season")
        if season is None:
            raise McpError(ErrorData(message="Season not provided", code=-1))
        result = self._get_schedules_data()
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ] 
    
    def _get_all_teams_data(self) -> NBAGetAllTeamsData:
        request_url = f"{self.__base_url}teams?key={self.api_key}"
        response = requests.get(request_url)
        response_json = response.json()
        return NBAGetAllTeamsData(teams_data=response_json)
    
    def _get_all_active_players_data(self) -> NBAGetAllActivePlayersData:
        request_url = f"{self.__base_url}PlayersActiveBasic?key={self.api_key}"
        response = requests.get(request_url)
        response_json = response.json()
        return NBAGetAllActivePlayersData(teams_data=response_json)

    def _get_schedules_data(self, season) -> NBAGetSchedulesData:
        request_url = f"{self.__base_url}SchedulesBasic/{season}?key={self.api_key}"
        response = requests.get(request_url)
        response_json = response.json()
        return NBAGetSchedulesData(teams_data=response_json)