import logging
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError
from mcpagentai.core.agent_base import MCPAgent

# import the enum and model definitions for Twitter:
from mcpagentai.defs import TwitterTools, TwitterResult

# import the Node-based logic:
from . import twitter_api  # or wherever your `twitter_api.py` lives

logger = logging.getLogger(__name__)

class TwitterAgent(MCPAgent):
    """
    Agent that handles creating or replying to tweets using
    a Node.js (agent-twitter-client) bridge, instead of Tweepy.
    """

    def __init__(self):
        super().__init__()
        logger.info("TwitterAgent initialized (Node-based).")

    def list_tools(self) -> list[Tool]:
        """
        Return the two basic operations: CREATE_TWEET and REPLY_TWEET.
        Adjust as needed for your use cases.
        """
        return [
            Tool(
                name=TwitterTools.CREATE_TWEET.value,
                description="Create a new tweet with some text content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tweet_text": {
                            "type": "string",
                            "description": "Text to include in the new tweet"
                        }
                    },
                    "required": ["tweet_text"]
                }
            ),
            Tool(
                name=TwitterTools.REPLY_TWEET.value,
                description="Reply to an existing tweet (URL or ID) with some text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reply_text": {
                            "type": "string",
                            "description": "Text to post as a reply."
                        },
                        "tweet_url": {
                            "type": "string",
                            "description": "Full tweet URL or ID to reply to (e.g., https://twitter.com/user/status/123)."
                        }
                    },
                    "required": ["reply_text", "tweet_url"]
                }
            )
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Dispatch to the appropriate _handle method based on the tool name.
        Return a list of MCP Content (TextContent in these examples).
        """
        self.logger.debug("TwitterAgent.call_tool => name=%s, arguments=%s", name, arguments)

        if name == TwitterTools.CREATE_TWEET.value:
            return self._handle_create_tweet(arguments)
        elif name == TwitterTools.REPLY_TWEET.value:
            return self._handle_reply_tweet(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_create_tweet(self, arguments: dict) -> Sequence[TextContent]:
        tweet_text = arguments.get("tweet_text", "").strip()
        if not tweet_text:
            raise McpError("Missing 'tweet_text' in the request.")

        result_data = twitter_api.send_tweet(tweet_text)
        # We can parse result_data into a Pydantic model for consistency
        result_model = TwitterResult(**result_data)

        if not result_model.success:
            raise McpError(f"Failed to create tweet: {result_model.error}")

        message = (
            f"Tweet created successfully!\n\n"
            f"Message: {result_model.message}\n"
            f"URL: {result_model.tweet_url or 'N/A'}\n"
        )
        return [TextContent(type="text", text=message)]

    def _handle_reply_tweet(self, arguments: dict) -> Sequence[TextContent]:
        reply_text = arguments.get("reply_text", "").strip()
        tweet_url = arguments.get("tweet_url", "").strip()
        if not reply_text or not tweet_url:
            raise McpError("Missing 'reply_text' or 'tweet_url' in request.")

        result_data = twitter_api.reply_tweet(reply_text, tweet_url)
        result_model = TwitterResult(**result_data)

        if not result_model.success:
            raise McpError(f"Failed to reply to tweet: {result_model.error}")

        message = (
            f"Reply posted successfully!\n\n"
            f"Message: {result_model.message}\n"
            f"URL: {result_model.tweet_url or 'N/A'}\n"
        )
        return [TextContent(type="text", text=message)]
