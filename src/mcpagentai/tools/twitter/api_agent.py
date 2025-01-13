import os
import logging
import json  # Ensure json is imported
import tweepy

from typing import Sequence, Union
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError
from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import TwitterTools, TwitterResult


class TwitterAgent(MCPAgent):
    """
    Agent that handles creating tweets and replying to tweets using the Twitter API v2 via Tweepy.
    """

    def __init__(self):
        super().__init__()
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_key_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_SECRET")

        if not self.bearer_token:
            self.logger.warning(
                "Bearer token is missing. Please set your TWITTER_BEARER_TOKEN environment variable."
            )

        # Initialize Tweepy Client for API v2
        self._authenticate()

    def _authenticate(self) -> tweepy.Client:
        """
        Authenticates with Twitter API using Tweepy's Client for API v2.

        Returns:
            tweepy.Client: Authenticated Tweepy Client instance.
        """
        try:
            # Initialize Tweepy Client with OAuth 2.0 Bearer Token
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_key_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            # Verify credentials
            user = self.client.get_user(username=self._get_username())
            if user.data:
                self.logger.info("Successfully authenticated with Twitter API v2.")
            else:
                raise McpError("Authentication failed: Unable to fetch user data.")
            return
        except Exception as e:
            self.logger.error(f"Error during Twitter authentication: {e}")
            raise McpError(f"Twitter authentication failed: {e}") from e

    def _get_username(self) -> str:
        """
        Retrieves the authenticated user's username.

        Returns:
            str: Twitter username.

        Raises:
            McpError: If unable to retrieve username.
        """
        try:
            # Fetch the authenticated user
            response = self.client.get_me()
            if response.data and response.data.username:
                return response.data.username
            else:
                raise McpError("Unable to retrieve authenticated user's username.")
        except Exception as e:
            self.logger.error(f"Error fetching authenticated user's username: {e}")
            raise McpError(f"Failed to get username: {e}") from e

    def list_tools(self) -> list[Tool]:
        """
        Return the list of tools for tweeting and replying.
        """
        return [
            Tool(
                name=TwitterTools.CREATE_TWEET.value,
                description="Create a new tweet on the authenticated account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The text content of the new tweet"
                        },
                    },
                    "required": ["message"]
                },
            ),
            Tool(
                name=TwitterTools.REPLY_TWEET.value,
                description="Reply to an existing tweet given the tweet ID and reply text.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tweet_id": {
                            "type": "string",
                            "description": "The ID of the tweet to reply to"
                        },
                        "message": {
                            "type": "string",
                            "description": "The text content of the reply"
                        },
                    },
                    "required": ["tweet_id", "message"]
                },
            ),
        ]

    def call_tool(
            self,
            name: str,
            arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """
        Dispatch calls to create a new Tweet or reply to an existing Tweet.
        """
        self.logger.debug("TwitterAgent call_tool => name=%s, arguments=%s", name, arguments)
        if name == TwitterTools.CREATE_TWEET.value:
            return self._handle_create_tweet(arguments)
        elif name == TwitterTools.REPLY_TWEET.value:
            return self._handle_reply_tweet(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_create_tweet(self, arguments: dict) -> Sequence[TextContent]:
        """
        Creates a new Tweet on the user's timeline.
        """
        message = arguments.get("message", "").strip()
        if not message:
            raise McpError("No tweet message provided")

        if not hasattr(self, 'client') or not self.client:
            raise McpError("Twitter client not initialized. Check your credentials.")

        try:
            # Create a new tweet using API v2
            response = self.client.create_tweet(text=message)
            if response.data:
                tweet_id = response.data['id']
                tweet_url = f"https://twitter.com/{self._get_username()}/status/{tweet_id}"
                result = TwitterResult(
                    success=True,
                    message="Tweet posted successfully",
                    tweet_url=tweet_url
                )
                self.logger.info(f"Tweet created successfully: {tweet_url}")
                return [TextContent(type="text", text=result.model_dump_json(indent=2))]
            else:
                raise McpError("Failed to create tweet: No data returned.")
        except tweepy.TweepyException as e:
            error_msg = f"Error posting tweet: {e}"
            self.logger.error(error_msg)
            raise McpError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error posting tweet: {e}"
            self.logger.error(error_msg)
            raise McpError(error_msg) from e

    def _handle_reply_tweet(self, arguments: dict) -> Sequence[TextContent]:
        """
        Replies to an existing Tweet by ID.
        """
        tweet_id = arguments.get("tweet_id", "").strip()
        message = arguments.get("message", "").strip()
        if not tweet_id:
            raise McpError("No tweet_id provided")
        if not message:
            raise McpError("No reply message provided")

        if not hasattr(self, 'client') or not self.client:
            raise McpError("Twitter client not initialized. Check your credentials.")

        try:
            # Reply to a tweet using API v2
            response = self.client.create_tweet(
                text=message,
                in_reply_to_tweet_id=tweet_id
            )
            self.logger.debug(f"Reply Tweet Response: {response}")

            if response.data:
                reply_id = response.data['id']
                reply_url = f"https://twitter.com/{self._get_username()}/status/{reply_id}"
                result = TwitterResult(
                    success=True,
                    message="Replied to tweet successfully",
                    tweet_url=reply_url
                )
                self.logger.info(f"Replied to tweet successfully: {reply_url}")
                return [TextContent(type="text", text=result.model_dump_json(indent=2))]
            else:
                raise McpError("Failed to reply to tweet: No data returned.")
        except tweepy.TweepyException as e:
            error_msg = f"Error replying to tweet: {e}"
            self.logger.error(error_msg)
            raise McpError(error_msg) from e
        except KeyError as e:
            error_msg = f"Missing expected key in response data: {e}"
            self.logger.error(error_msg)
            raise McpError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error replying to tweet: {e}"
            self.logger.error(error_msg)
            raise McpError(error_msg) from e
