import json
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.agent_base import MCPAgent


class CalculatorAgent(MCPAgent):
    """
    Agent that performs arbitrary math expressions using Python's eval (cautiously).
    For real usage, consider a safe parser or sandbox for security.
    """

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name="calculate_expression",
                description="Calculate a math expression (dangerous: uses eval).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "A mathematical expression in Python syntax",
                        },
                    },
                    "required": ["expression"],
                },
            )
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == "calculate_expression":
            return self._handle_calculate_expression(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_calculate_expression(self, arguments: dict) -> Sequence[TextContent]:
        expr = arguments["expression"]
        try:
            result = eval(expr)  # For demonstration only, not recommended for production
        except Exception as e:
            result = f"Error evaluating expression: {e}"
        return [
            TextContent(
                type="text",
                text=json.dumps({"expression": expr, "result": result}, indent=2)
            )
        ]
