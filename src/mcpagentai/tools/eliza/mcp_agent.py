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
    Handles local Eliza character JSON files for bios and lore and enables interaction with characters.
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
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name=ElizaParserTools.GET_CHARACTER_BIO.value,
                description="Get bio of a specific Eliza character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_json_file_name": {
                            "type": "string",
                            "description": "Name of character JSON file"
                        }
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
                            "description": "Name of character JSON file"
                        }
                    },
                    "required": ["character_json_file_name"]
                }
            ),
            Tool(
                name="get_full_agent_info",
                description="Get full agent info, including bio and lore, for all characters",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="interact_with_agent",
                description="Interact with an agent by building a prompt based on bio, lore, and previous answers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_json_file_name": {
                            "type": "string",
                            "description": "Name of character JSON file"
                        },
                        "question": {
                            "type": "string",
                            "description": "The question or input for the character"
                        },
                        "previous_answers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of previous answers from the character"
                        }
                    },
                    "required": ["character_json_file_name", "question"]
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
        elif name == "get_full_agent_info":
            return self._handle_get_full_agent_info(arguments)
        elif name == "interact_with_agent":
            return self._handle_interact_with_agent(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}")

    def _handle_get_characters(self, arguments: dict) -> Sequence[TextContent]:
        result = self._get_characters()
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_get_character_bio(self, arguments: dict) -> Sequence[TextContent]:
        filename = arguments.get("character_json_file_name")
        if not filename:
            raise McpError("Character JSON file name not provided")
        result = self._get_character_bio(filename)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_get_character_lore(self, arguments: dict) -> Sequence[TextContent]:
        filename = arguments.get("character_json_file_name")
        if not filename:
            raise McpError("Character JSON file name not provided")
        result = self._get_character_lore(filename)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))]

    def _handle_get_full_agent_info(self, arguments: dict) -> Sequence[TextContent]:
        """
        Combine bio and lore for all characters and return as full info.
        """
        self.logger.info("Getting full agent info for all characters.")
        characters = self._get_characters().characters
        all_info = {}

        for character in characters:
            bio = self._get_character_bio(character).characters
            lore = self._get_character_lore(character).characters
            all_info[character] = {"bio": bio, "lore": lore}

        return [TextContent(type="text", text=json.dumps(all_info, indent=2))]

    def _handle_interact_with_agent(self, arguments: dict) -> Sequence[TextContent]:
        """
        Build a prompt for interaction with an agent.
        """
        filename = arguments.get("character_json_file_name")
        question = arguments.get("question")
        previous_answers = arguments.get("previous_answers", [])

        if not filename:
            raise McpError("Character JSON file name not provided")
        if not question:
            raise McpError("Question not provided")

        bio = self._get_character_bio(filename).characters
        lore = self._get_character_lore(filename).characters

        prompt = f"Character Bio: {bio}\nCharacter Lore: {lore}\nPrevious Answers: {previous_answers}\nQuestion: {question}\nAnswer:"
        self.logger.debug("Generated prompt for interaction: %s", prompt)

        # In this placeholder, we just return the generated prompt.
        # You could integrate an LLM call here to process the prompt and generate a response.
        return [TextContent(type="text", text=prompt)]

    import os
    import json

    import os
    import json

    def _get_characters(self) -> ElizaGetCharacters:
        self.logger.info("Listing character files in %s", self.eliza_character_path)

        # Initialize debug message
        debug_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "debug.log",
            "params": {},
        }

        # Add provided path
        debug_message["params"]["provided_eliza_character_path"] = self.eliza_character_path

        # Check if /app exists
        # app_path = "/app"
        # if os.path.exists(app_path):
        #     debug_message["params"]["app_structure"] = []
        #     for root, dirs, files in os.walk(app_path):
        #         if "node_modules" in dirs:
        #             dirs.remove("node_modules")  # Exclude node_modules
        #         debug_message["params"]["app_structure"].append({
        #             "root": root,
        #             "dirs": dirs,
        #             "files": files,
        #         })
        # else:
        #     debug_message["params"]["app_exists"] = False

        # Path existence and directory checks
        path_exists = os.path.exists(self.eliza_character_path)
        debug_message["params"]["path_exists"] = path_exists

        is_directory = os.path.isdir(self.eliza_character_path)
        debug_message["params"]["is_directory"] = is_directory

        if not is_directory:
            debug_message["error"] = f"Characters directory does not exist: {self.eliza_character_path}"
            print(json.dumps(debug_message))
            raise FileNotFoundError(debug_message["error"])

        # List files in the directory
        try:
            character_files = os.listdir(self.eliza_character_path)
            debug_message["params"]["character_files"] = character_files
        except Exception as e:
            debug_message["error"] = f"Error listing files in directory: {str(e)}"
            print(json.dumps(debug_message))
            raise

        # Print final debug message
        print(json.dumps(debug_message))

        return ElizaGetCharacters(characters=character_files)

    def _get_character_bio(self, filename: str) -> ElizaGetCharacterBio:
        file_path = os.path.join(self.eliza_character_path, filename)
        self.logger.info("Reading character bio from %s", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File doesn't exist: {file_path}")

        with open(file_path, "r") as fp:
            data = json.load(fp)

        # Safely handle bio field as list or string
        bio_data = data.get("bio", "")
        if isinstance(bio_data, list):
            # Convert list of strings into a single string
            bio_data = " ".join(bio_data)

        return ElizaGetCharacterBio(characters=bio_data)

    def _get_character_lore(self, filename: str) -> ElizaGetCharacterLore:
        file_path = os.path.join(self.eliza_character_path, filename)
        self.logger.info("Reading character lore from %s", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File doesn't exist: {file_path}")

        with open(file_path, "r") as fp:
            data = json.load(fp)

        # Safely handle lore field as list or string
        lore_data = data.get("lore", "")
        if isinstance(lore_data, list):
            # Convert list of strings into a single string
            lore_data = " ".join(lore_data)

        return ElizaGetCharacterLore(characters=lore_data)

