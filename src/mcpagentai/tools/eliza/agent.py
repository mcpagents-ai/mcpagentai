import os
import json
import logging
import requests

from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import ElizaTools, ElizaGetAgents, ElisaMessageAgent


logger = logging.getLogger(__name__)

class ElizaAgent(MCPAgent):
    """
    Communicates with a remote Eliza server over HTTP.
    """

    def __init__(self, eliza_api_url: str = None):
        super().__init__()
        # Use .env or fallback default if not provided
        self.eliza_api_url = eliza_api_url or os.getenv("ELIZA_API_URL")
        logger.info("ElizaAgent initialized with API URL: %s", self.eliza_api_url)

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=ElizaTools.GET_AGENTS.value,
                description="Get list of Eliza agents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to Eliza to list all agents"
                        },
                    }
                }
            ),
            Tool(
                name=ElizaTools.MESSAGE_AGENT.value,
                description="Message specific Eliza agent and get response from it",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {
                            "type": "string",
                            "description": "Name of agent from Eliza"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to specific Eliza agent"
                        },
                    },
                    "required": ["agent", "message"]
                }
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        self.logger.debug("ElizaAgent call_tool => name=%s, arguments=%s", name, arguments)
        if name == ElizaTools.GET_AGENTS.value:
            return self._handle_get_agents(arguments)
        elif name == ElizaTools.MESSAGE_AGENT.value:
            return self._handle_message_agent(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}")

    def _handle_get_agents(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question") or "list eliza agents"
        self.logger.debug("Handling GET_AGENTS with question=%s", question)
        result = self._get_agents(question)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_message_agent(self, arguments: dict) -> Sequence[TextContent]:
        agent = arguments.get("agent")
        message = arguments.get("message")
        self.logger.debug("Handling MESSAGE_AGENT with agent=%s, message=%s", agent, message)

        if agent is None:
            raise McpError("Agent name not provided")
        if message is None:
            raise McpError("Message to agent not provided")

        result = self._message_agent(agent, message)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _get_agents_all_data(self) -> dict:
        agents_url = f"{self.eliza_api_url}/api/agents"
        self.logger.info("Fetching Eliza agents from: %s", agents_url)

        try:
            response = requests.get(agents_url)
            if response.status_code != 200:
                raise McpError("Cant connect to Eliza server")
        except requests.RequestException as e:
            error_msg = f"Request error connecting to Eliza server: {str(e)}"
            logger.error(error_msg)
            raise McpError(error_msg) from e

        return response.json()

    def _get_agents(self, question: str) -> ElizaGetAgents:
        """
        Return a pydantic model with the agent names from the Eliza server.
        """
        agents_data = self._get_agents_all_data()
        agent_names = [agent['name'] for agent in agents_data.get('agents', [])]
        return ElizaGetAgents(agents=agent_names)

    def _message_agent(self, agent_name: str, message: str) -> ElisaMessageAgent:
        """
        Send a message to a specific agent and return a pydantic model with the agent's response.
        """
        agents_data = self._get_agents_all_data()
        agent_id = None
        for ag in agents_data.get("agents", []):
            if ag['name'] == agent_name:
                agent_id = ag['id']
                break

        if agent_id is None:
            raise McpError(f"Couldnt find agent of name: {agent_name}")

        message_url = f"{self.eliza_api_url}/api/{agent_id}/message"
        if self.eliza_api_url.startswith("http://"):
            host_url = self.eliza_api_url[len("http://"):]
        elif self.eliza_api_url.startswith("https://"):
            host_url = self.eliza_api_url[len("https://"):]
        else:
            host_url = self.eliza_api_url

        headers = {
            "Accept": "*/*",
            "Sec-Fetch-Site": "same-origin",
            "Accept-Language": "pl-PL,pl;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Sec-Fetch-Mode": "cors",
            "Host": host_url,
            "Origin": self.eliza_api_url,
            "User-Agent": "MCP-ElizaAgent",
            "Referer": f"{self.eliza_api_url}/{agent_id}/chat",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
        }

        # form data => multipart/form-data
        files = {
            "text": (None, message),
            "userId": (None, "user"),
            "roomId": (None, f"default-room-{agent_id}"),
        }

        try:
            response = requests.post(message_url, headers=headers, files=files)
            if response.status_code != 200:
                raise McpError(f"Cant connect to Eliza server or invalid agent id parameter: {agent_id}")
        except requests.RequestException as e:
            error_msg = f"Request error posting to Eliza server: {str(e)}"
            logger.error(error_msg)
            raise McpError(error_msg) from e

        resp_json = response.json()
        agent_message = resp_json[0]["text"] if resp_json else ""
        return ElisaMessageAgent(agent_message=agent_message)
