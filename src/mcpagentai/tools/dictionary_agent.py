import json
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.agent_base import MCPAgent


class DictionaryAgent(MCPAgent):
    """
    Agent that looks up word definitions (stubbed example).
    """

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name="define_word",
                description="Look up the definition of a word",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "word": {
                            "type": "string",
                            "description": "The word to define",
                        },
                    },
                    "required": ["word"],
                },
            )
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == "define_word":
            return self._handle_define_word(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_define_word(self, arguments: dict) -> Sequence[TextContent]:
        word = arguments["word"]
        # Stubbed. In reality, you'd call an external dictionary API, e.g. Merriam-Webster.
        mock_definition = (
            f"{word.capitalize()}: [Mock definition for demonstration purposes]"
        )
        return [
            TextContent(
                type="text",
                text=json.dumps({"word": word, "definition": mock_definition}, indent=2)
            )
        ]
