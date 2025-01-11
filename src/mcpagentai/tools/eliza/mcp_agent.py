import os
import json
import logging

from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from mcpagentai.defs import (
    ElizaParserTools,
    ElizaGetCharacters,
    ElizaGetCharacterLore,
    ElizaGetCharacterBio,
)
from mcpagentai.core.agent_base import MCPAgent

logger = logging.getLogger(__name__)

class ElizaMCPAgent(MCPAgent):
    """
    Handles local Eliza character JSON files for bios and lore.
    Previously called ElizaParserAgent.
    """

    def __init__(self, eliza_path: str = None):
        super().__init__()
        self.eliza_path = eliza_path or os.getenv("ELIZA_PATH")
        self.eliza_character_path = os.path.join(self.eliza_path, "characters")

        logger.info("ElizaMCPAgent initialized with character path: %s", self.eliza_character_path)

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=ElizaParserTools.GET_CHARACTERS.value,
                description="Get list of Eliza character JSON files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to list all character JSON files"
                        },
                    }
                }
            ),
            Tool(
                name=ElizaParserTools.GET_CHARACTER_BIO.value,
                description="Get bio of a specific Eliza character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_json_file_name": {
                            "type": "string",
                            "description": "Name of character json file"
                        },
                    },
                    "required": ["character_json_file_name"]
                }
            ),
            Tool(
                name=ElizaParserTools.GET_CHARACTER_LORE.value,
                description="Get lore of a specific Eliza character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_json_file_name": {
                            "type": "string",
                            "description": "Name of character json file"
                        },
                    },
                    "required": ["character_json_file_name"]
                }
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        self.logger.debug("ElizaMCPAgent call_tool => name=%s, arguments=%s", name, arguments)

        if name == ElizaParserTools.GET_CHARACTERS.value:
            return self._handle_get_characters(arguments)
        elif name == ElizaParserTools.GET_CHARACTER_BIO.value:
            return self._handle_get_character_bio(arguments)
        elif name == ElizaParserTools.GET_CHARACTER_LORE.value:
            return self._handle_get_character_lore(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}")

    def _handle_get_characters(self, arguments: dict) -> Sequence[TextContent]:
        question = arguments.get("question", "")
        self.logger.debug("Handling GET_CHARACTERS with question=%s", question)

        result = self._get_characters(question)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_get_character_bio(self, arguments: dict) -> Sequence[TextContent]:
        filename = arguments.get("character_json_file_name")
        if not filename:
            raise McpError("Character JSON file name not provided")

        self.logger.debug("Handling GET_CHARACTER_BIO with file=%s", filename)
        result = self._get_character_bio(filename)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_get_character_lore(self, arguments: dict) -> Sequence[TextContent]:
        filename = arguments.get("character_json_file_name")
        if not filename:
            raise McpError("Character JSON file name not provided")

        self.logger.debug("Handling GET_CHARACTER_LORE with file=%s", filename)
        result = self._get_character_lore(filename)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _get_characters(self, question: str) -> ElizaGetCharacters:
        """
        Return a list of character files as a pydantic model.
        """
        self.logger.info("Listing character files in %s", self.eliza_character_path)

        if not os.path.isdir(self.eliza_character_path):
            raise FileNotFoundError(f"Characters directory does not exist: {self.eliza_character_path}")

        character_files = os.listdir(self.eliza_character_path)
        return ElizaGetCharacters(characters=character_files)

    def _get_character_bio(self, filename: str) -> ElizaGetCharacterBio:
        """
        Return the 'bio' field from a specified JSON.
        """
        file_path = os.path.join(self.eliza_character_path, filename)
        self.logger.info("Reading character bio from %s", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File doesnt exist: {file_path}")

        with open(file_path, "r") as fp:
            data = json.load(fp)

        bio = data.get('bio', "")
        return ElizaGetCharacterBio(characters=bio)

    def _get_character_lore(self, filename: str) -> ElizaGetCharacterLore:
        """
        Return the 'lore' field from a specified JSON.
        """
        file_path = os.path.join(self.eliza_character_path, filename)
        self.logger.info("Reading character lore from %s", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File doesnt exist: {file_path}")

        with open(file_path, "r") as fp:
            data = json.load(fp)

        lore = data.get('lore', "")
        return ElizaGetCharacterLore(characters=lore)
