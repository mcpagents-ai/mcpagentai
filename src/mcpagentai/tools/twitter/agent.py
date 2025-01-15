import os
import json
import time
import random
import anthropic
from typing import Sequence, Union, Dict, Any, Optional
from pathlib import Path
import asyncio
from dotenv import load_dotenv

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import TwitterTools, StockTools, WeatherTools
from mcpagentai.tools.stock_agent import StockAgent
from mcpagentai.tools.weather_agent import WeatherAgent
from mcpagentai.tools.time_agent import TimeAgent
from . import agent_client_wrapper

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
load_dotenv(env_path)


class TwitterAgent(MCPAgent):
    """
    AI-powered Twitter agent that uses Claude to generate tweets and replies
    """

    def __init__(self):
        super().__init__()
        self.last_tweet_time = 0
        self.last_reply_time = 0
        self.last_action_time = 0

        # Initialize query handlers
        self.query_handlers = {}
        self._load_query_handlers()

        # Load personality config
        personality_file = os.getenv("PERSONALITY_CONFIG", "tech_expert.json")
        self.personality = self.load_personality(personality_file)

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Setup storage paths - use project root for cookies.json
        self.project_root = Path.cwd()
        self.store_dir = self.project_root / 'store'
        self.store_dir.mkdir(exist_ok=True)
        self.replied_file = self.store_dir / 'replied_tweets.json'
        self.cookies_file = self.project_root / 'cookies.json'  # cookies.json is in root

        # Load replied tweets from file
        self.replied_to = self.load_replied_tweets()

        # Start tweet and reply monitoring loops
        if os.getenv("RUN_AGENT", "false").lower() == "true":
            asyncio.create_task(self._tweet_loop())
            asyncio.create_task(self._reply_loop())

    def _load_query_handlers(self):
        """Load all available query handlers"""
        # Import handlers here to avoid circular imports
        from mcpagentai.tools.twitter.handlers.weather_handler import WeatherQueryHandler
        from mcpagentai.tools.twitter.handlers.stock_handler import StockQueryHandler
        from mcpagentai.tools.twitter.handlers.time_handler import TimeQueryHandler
        from mcpagentai.tools.twitter.handlers.crypto_handler import CryptoQueryHandler
        from mcpagentai.tools.twitter.handlers.currency_handler import CurrencyQueryHandler

        # Initialize handlers
        handlers = [
            WeatherQueryHandler(),
            StockQueryHandler(),
            TimeQueryHandler(),
            CryptoQueryHandler(),
            CurrencyQueryHandler()
        ]

        # Register handlers
        for handler in handlers:
            self.query_handlers[handler.query_type] = handler
            self.logger.info(f"Registered query handler for: {handler.query_type}")

    def _get_available_handlers_info(self) -> str:
        """Get information about available handlers for Claude's prompt"""
        info = []
        for handler in self.query_handlers.values():
            examples_str = "\n".join([f"- {q}" for q in handler.examples.keys()])
            info.append(f"""
            {handler.query_type.upper()}:
            Parameters: {handler.available_params}
            Example queries:
            {examples_str}
            """)
        return "\n".join(info)

    def load_personality(self, personality_file: str) -> dict:
        """Load personality configuration"""
        character_path = os.path.join(
            os.path.dirname(__file__),
            '../eliza/characters',
            personality_file
        )
        with open(character_path, 'r') as f:
            return json.load(f)

    def load_replied_tweets(self) -> set:
        """Load the set of tweets we've replied to"""
        try:
            if self.replied_file.exists():
                # Check if file is empty
                if self.replied_file.stat().st_size == 0:
                    # Initialize with empty array if file is empty
                    with open(self.replied_file, 'w') as f:
                        json.dump([], f)
                    return set()

                # Try to load existing data
                with open(self.replied_file) as f:
                    return set(json.load(f))
            else:
                # Create file with empty array if it doesn't exist
                self.replied_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.replied_file, 'w') as f:
                    json.dump([], f)
                return set()

        except json.JSONDecodeError as e:
            self.logger.warning(f"Invalid JSON in replied tweets file: {e}")
            # Backup the corrupted file and create new empty one
            backup_file = self.replied_file.with_suffix('.json.bak')
            self.replied_file.rename(backup_file)
            with open(self.replied_file, 'w') as f:
                json.dump([], f)
            return set()

        except Exception as e:
            self.logger.warning(f"Could not load replied tweets: {e}")
            # Initialize file with empty array for any other error
            with open(self.replied_file, 'w') as f:
                json.dump([], f)
            return set()  # Return empty set for any failure case

    def save_replied_tweets(self):
        """Save the set of replied tweets to file"""
        with open(self.replied_file, 'w') as f:
            json.dump(list(self.replied_to), f)

    async def generate_tweet(self) -> str:
        """Generate a tweet using the personality config and query handlers"""
        context = {}

        # Randomly decide which data to include (0-2 types of data)
        data_types = ["time", "stock", "crypto", "weather"]
        num_data = random.randint(0, 4)  # Sometimes tweet with no data, max 2 types
        if num_data == 0:
            context["other"] = random.choice([
                "tweet type 1",
            ])
        else:
            selected_data = random.sample(data_types, num_data)

            # Get time if selected (no API, should always work)
            if "time" in selected_data:
                try:
                    if "time" in self.query_handlers:
                        time_data = self.query_handlers["time"].handle_query({"city": "nyc"})
                        if time_data:
                            context["time"] = time_data
                except Exception as e:
                    self.logger.warning(f"Error getting time data: {e}")

            # Get stock info if selected
            if "stock" in selected_data:
                try:
                    if "stock" in self.query_handlers:
                        stock_data = self.query_handlers["stock"].handle_query({"ticker": "IBM"})
                        if stock_data and "API Limit" not in stock_data and "Error" not in stock_data:
                            context["stocks"] = stock_data
                            self.logger.debug(f"Got stock price: {context['stocks']}")
                except Exception as e:
                    self.logger.warning(f"Error getting stock data: {e}")

            # Get crypto info if selected
            if "crypto" in selected_data:
                try:
                    if "crypto" in self.query_handlers:
                        crypto_data = self.query_handlers["crypto"].handle_query({"symbol": "BTC"})
                        if crypto_data and "Error" not in crypto_data:
                            context["crypto"] = crypto_data
                            self.logger.debug(f"Got crypto price: {context['crypto']}")
                except Exception as e:
                    self.logger.warning(f"Error getting crypto data: {e}")

            # Get weather info if selected
            if "weather" in selected_data:
                try:
                    if "weather" in self.query_handlers:
                        weather_data = self.query_handlers["weather"].handle_query({"city": "sf"})
                        if weather_data and "Error" not in weather_data:
                            context["weather"] = weather_data
                            self.logger.debug(f"Got weather: {context['weather']}")
                except Exception as e:
                    self.logger.warning(f"Error getting weather data: {e}")

        # Add context to prompt
        system_prompt = f"""You are {self.personality['name']}, {self.personality['lore']}.
                        Bio: {' '.join(self.personality['bio'])}
                        Style: {' '.join(self.personality['style']['post'])}

                        IMPORTANT: You must respond with valid JSON in exactly this format, nothing else:
                        {{"text": "your tweet here"}}

                        Current context:
                        {f"- Time: {context.get('time')}" if 'time' in context else ""}
                        {f"- Stocks: {context.get('stocks')}" if 'stocks' in context else ""}
                        {f"- Crypto: {context.get('crypto')}" if 'crypto' in context else ""}
                        {f"- Weather: {context.get('weather')}" if 'weather' in context else ""}

                        Keep tweets under 280 characters and match your personality.
                        Only mention data that is available in the context.
                        If no data is available, just tweet something casual and fun that matches your personality.
                        Vary your tweets - don't always focus on the same topics."""

        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": "Generate a tweet incorporating the context. Respond ONLY with the JSON object."
                }]
            )

            # Parse the JSON response
            tweet_data = json.loads(response.content[0].text.strip())
            return tweet_data["text"]

        except Exception as e:
            self.logger.error(f"Error generating tweet: {e}")
            return None

    async def generate_reply(self, tweet_context: Dict[str, Any]) -> Optional[str]:
        try:
            # First try to identify if this is a data query
            analysis_response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                system="""You are a query analyzer. Extract data requirements from tweets.
                         If the tweet is a general question or conversation, respond with {"type": "conversation"}.
                         Otherwise, respond with data queries in this format:
                         {
                           "queries": [
                             {
                               "type": "weather|stock|time|crypto|currency",
                               "params": {
                                 // Parameters specific to the query type
                               }
                             }
                           ]
                         }

                         Query type guidelines:
                         - Use "currency" for fiat currency exchange rates (USD, EUR, CAD, etc.)
                         - Use "crypto" only for cryptocurrency queries (BTC, ETH, etc.)
                         - Use "weather" for weather queries with city in params
                         - Use "stock" for stock market queries with ticker symbol
                         - Use "time" for timezone/time queries with city""",
                messages=[{
                    "role": "user",
                    "content": f"Analyze this tweet for specific data queries or identify if it's conversational: {tweet_context['text']}"
                }]
            )

            try:
                query_data = json.loads(analysis_response.content[0].text)
                context = {}

                # Handle conversational tweets differently
                if query_data.get("type") == "conversation":
                    # Generate a conversational response that directly addresses the tweet
                    reply_response = self.client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=150,
                        system=f"""You are {self.personality['name']}, {self.personality['personality']}.
                                Bio: {' '.join(self.personality['bio'])}
                                Style: {' '.join(self.personality['style']['chat'])}

                                IMPORTANT: You must respond with valid JSON in exactly this format, nothing else:
                                {{"text": "your reply here"}}

                                The user's tweet: "{tweet_context['text']}"

                                Guidelines for conversational replies:
                                1. Always acknowledge or reference what the user said
                                2. If they asked a question, make sure to answer it directly
                                3. Stay in character and maintain your personality
                                4. Keep replies under 280 characters
                                5. Be engaging and friendly
                                6. If you're unsure about something, it's okay to say so""",
                        messages=[{
                            "role": "user",
                            "content": "Generate a conversational reply that directly addresses the tweet. Respond ONLY with the JSON object."
                        }]
                    )
                else:
                    # Handle data-focused queries as before
                    for query in query_data.get("queries", []):
                        if query["type"] in self.query_handlers:
                            handler = self.query_handlers[query["type"]]
                            response = handler.handle_query(query["params"])

                            if isinstance(response, list):
                                response = response[0] if response else None

                            if response and not response.startswith("Error"):
                                context[query["type"]] = response

                    # Generate the reply using the data context
                    reply_response = self.client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=150,
                        system=f"""You are {self.personality['name']}, {self.personality['personality']}.
                                Bio: {' '.join(self.personality['bio'])}
                                Style: {' '.join(self.personality['style']['chat'])}

                                IMPORTANT: You must respond with valid JSON in exactly this format, nothing else:
                                {{"text": "your reply here"}}

                                The user's tweet: "{tweet_context['text']}"
                                Available data: {json.dumps(context)}

                                Guidelines for data-focused replies:
                                1. Always include the specific data they asked for
                                2. If there is currency exchange rate data, include the actual numbers
                                3. Keep replies under 280 characters
                                4. Stay in character while providing the information
                                5. Only mention data that is available in the context""",
                        messages=[{
                            "role": "user",
                            "content": "Generate a reply incorporating the context and directly addressing their query. Respond ONLY with the JSON object."
                        }]
                    )

                if reply_response and reply_response.content:
                    reply_data = json.loads(reply_response.content[0].text.strip())
                    reply_text = reply_data["text"]
                    # Remove any @ mentions from the reply
                    reply_text = ' '.join(word for word in reply_text.split() if not word.startswith('@'))
                    return reply_text

            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing response: {e}")
                return None

            except Exception as e:
                self.logger.error(f"Error processing reply: {e}")
                return None

        except Exception as e:
            self.logger.error(f"Error generating reply: {e}")
            return None

    def list_tools(self) -> list[Tool]:
        """List available Twitter tools"""
        return [
            Tool(
                name=TwitterTools.CREATE_TWEET.value,
                description="Create a new tweet",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name=TwitterTools.REPLY_TWEET.value,
                description="Reply to a tweet",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "tweet_text": {"type": "string"},
                        "tweet_url": {"type": "string"}
                    },
                    "required": ["username", "tweet_text", "tweet_url"]
                }
            )
        ]

    async def call_tool(
            self,
            name: str,
            arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Handle tool calls"""
        if name == TwitterTools.CREATE_TWEET.value:
            return await self._handle_create_tweet(arguments)
        elif name == TwitterTools.REPLY_TWEET.value:
            return await self._handle_reply_tweet(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _handle_create_tweet(self, arguments: dict) -> Sequence[TextContent]:
        """Handle tweet creation"""
        if not self.should_tweet():
            return [TextContent(type="text", text="Too soon to tweet again")]

        tweet_text = await self.generate_tweet()
        if not tweet_text:
            self.logger.error("Failed to generate tweet")
            raise McpError("Failed to generate tweet")

        result = agent_client_wrapper.send_tweet(tweet_text)
        self.last_tweet_time = time.time()

        return [TextContent(
            type="text",
            text=json.dumps({"generated_tweet": tweet_text, "result": result}, indent=2)
        )]

    async def _handle_reply_tweet(self, arguments: dict) -> Sequence[TextContent]:
        now = time.time()
        if now - self.last_reply_time < random.randint(60, 120):  # 1-2 minutes
            return [TextContent(type="text", text="Too soon to reply again")]

        tweet_context = {
            "username": arguments["username"],
            "text": arguments["tweet_text"],
            "url": arguments["tweet_url"]
        }

        reply_text = await self.generate_reply(tweet_context)
        if not reply_text:
            raise McpError("Failed to generate reply")

        result = agent_client_wrapper.reply_tweet(reply_text, tweet_context["url"])
        self.last_reply_time = now

        # Add to replied set and save
        tweet_id = agent_client_wrapper.extract_tweet_id(tweet_context["url"])
        self.replied_to.add(tweet_id)
        self.save_replied_tweets()

        return [TextContent(
            type="text",
            text=json.dumps({"generated_reply": reply_text, "result": result}, indent=2)
        )]

    async def _tweet_loop(self):
        """Periodically generate and post tweets following original bot's schedule"""
        while True:
            try:
                now = time.time()
                # Random interval between 20-40 minutes (1200-2400 seconds)
                if now - self.last_tweet_time > random.randint(1200, 2400):
                    self.logger.info("Generating scheduled tweet...")
                    await self._handle_create_tweet({})
            except Exception as e:
                self.logger.error(f"Error in tweet loop: {e}")

            # Check every 5 minutes
            await asyncio.sleep(300)

    def should_tweet(self) -> bool:
        """Check if enough time has passed since last tweet (20-40 minutes)"""
        now = time.time()
        if now - self.last_tweet_time < 1200:  # 20 minutes minimum
            self.logger.debug('Too soon to tweet again')
            return False
        self.logger.debug('Ready to tweet')
        return True

    def should_reply(self, tweet_id: str) -> bool:
        """Check if we should reply to this tweet"""
        if tweet_id in self.replied_to:
            self.logger.debug(f"Already replied to tweet {tweet_id}")
            return False
        now = time.time()
        if now - self.last_reply_time < 300:  # 5 minutes minimum between replies
            self.logger.debug(f"Too soon to reply to tweet {tweet_id}")
            return False
        self.logger.debug(f"Ready to reply to tweet {tweet_id}")
        return True

    async def can_perform_action(self) -> bool:
        """Global rate limiting check for any tweet action"""
        now = time.time()
        if now - self.last_action_time < 60:  # Global 1 minute minimum between ANY actions
            self.logger.debug("Rate limit cooldown active")
            return False
        self.logger.debug("Ready to perform action")
        return True

    async def _reply_loop(self):
        """Periodically check for mentions and reply to them"""
        retry_count = 0
        max_retries = 3
        base_wait = 60  # Base wait time in seconds

        while True:
            try:
                # Check rate limit first
                if not await self.can_perform_action():
                    self.logger.info("⏳ Rate limit cooldown active, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    continue

                # Calculate wait time between reply checks
                time_since_reply = time.time() - self.last_reply_time
                wait_time = random.randint(60, 120)  # Random 1-2 minute interval

                if time_since_reply < wait_time:
                    remaining_time = int(wait_time - time_since_reply)
                    self.logger.info(f"💤 Next mention check in {remaining_time} seconds...")
                    await asyncio.sleep(remaining_time)
                    continue

                self.logger.info("\n🔍 Checking for new mentions...")

                # Define the Node.js script for checking mentions
                script = """
                const { Scraper } = require('agent-twitter-client');
                const { Cookie } = require('tough-cookie');

                async function checkMentions() {
                    try {
                        const scraper = new Scraper();
                        const cookiesData = require('./cookies.json');

                        const cookies = cookiesData.map(cookieData => {
                            const cookie = new Cookie({
                                key: cookieData.key,
                                value: cookieData.value,
                                domain: cookieData.domain,
                                path: cookieData.path,
                                secure: cookieData.secure,
                                httpOnly: cookieData.httpOnly
                            });
                            return cookie.toString();
                        });

                        await scraper.setCookies(cookies);

                        const mentions = [];
                        for await (const mention of scraper.searchTweets(
                            `@${process.env.TWITTER_USERNAME}`,
                            100,  // Increased to get more historical tweets
                            1  // SearchMode.Latest
                        )) {
                            // Skip if it's our own tweet
                            if (mention.username === process.env.TWITTER_USERNAME) continue;

                            mentions.push({
                                id: mention.id,
                                username: mention.username,
                                text: mention.text
                            });
                        }
                        console.log(JSON.stringify(mentions));
                    } catch (error) {
                        console.log(JSON.stringify({
                            success: false,
                            error: error.message
                        }));
                    }
                }

                checkMentions();
                """

                try:
                    mentions = await self.run_node_script(script)

                    if isinstance(mentions, str):
                        try:
                            mentions = json.loads(mentions)
                        except json.JSONDecodeError:
                            raise Exception(f"Failed to parse mentions response: {mentions}")

                    # Handle scraper error response
                    if isinstance(mentions, dict) and not mentions.get('success'):
                        error_msg = mentions.get('error', 'Unknown error')
                        raise Exception(f"Scraper error: {error_msg}")

                    if not isinstance(mentions, list):
                        raise Exception(f"Invalid mentions format: {mentions}")

                    # Reset retry count on successful request
                    retry_count = 0
                    self.logger.info(f"✨ Found {len(mentions)} total mentions")

                    for mention in mentions:
                        if not await self.can_perform_action():  # Check rate limit for each reply
                            self.logger.info("⏳ Rate limit reached, pausing replies...")
                            break

                        # Skip if we've already replied
                        if mention['id'] in self.replied_to:
                            self.logger.info(f"⏭️ Already replied to tweet {mention['id']}")
                            continue

                        self.logger.info(f"\n📝 Processing mention from @{mention['username']}: {mention['text']}")

                        # Generate AI response without mentioning the user
                        reply = await self.generate_reply({
                            'username': mention['username'],
                            'text': mention['text'],
                            'url': f"https://twitter.com/{mention['username']}/status/{mention['id']}"
                        })

                        if reply:
                            # Remove any @ mentions from the reply
                            reply = ' '.join(word for word in reply.split() if not word.startswith('@'))
                            self.logger.info(f"✍️ Generated reply: {reply}")

                            # Update times BEFORE sending to prevent parallel tweets
                            now = time.time()
                            self.last_reply_time = now
                            self.last_action_time = now

                            self.logger.info(f"🚀 Sending reply to tweet {mention['id']}...")
                            success = await self.send_tweet(reply, mention['id'])
                            if success:
                                self.replied_to.add(mention['id'])
                                self.logger.info(f"✅ Successfully replied to tweet {mention['id']}")
                                self.logger.info(f"Replied to tweet {mention['id']}: {reply}")
                                self.save_replied_tweets()
                            else:
                                self.logger.info(f"❌ Failed to send reply to tweet {mention['id']}")
                                # Reset timers if tweet failed
                                self.last_reply_time = now - 120
                                self.last_action_time = now - 60
                        else:
                            self.logger.info(f"❌ Failed to generate reply for tweet {mention['id']}")

                except Exception as e:
                    retry_count += 1
                    wait_time = min(base_wait * (2 ** retry_count), 3600)  # Max 1 hour wait
                    self.logger.info(f"❌ Error checking mentions (attempt {retry_count}/{max_retries}): {str(e)}")
                    self.logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                    self.logger.error(f"Error checking mentions: {str(e)}")
                    await asyncio.sleep(wait_time)

                    if retry_count >= max_retries:
                        self.logger.info("🔄 Max retries reached, resetting retry count...")
                        retry_count = 0
                        # Wait a longer time before starting fresh
                        await asyncio.sleep(1800)  # 30 minutes
                    continue

            except Exception as e:
                self.logger.info(f"❌ Error in reply loop: {str(e)}")
                self.logger.error(f"Error in reply loop: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on unexpected errors

            self.logger.info("\n💤 Waiting 60 seconds before next mention check...")
            await asyncio.sleep(60)

    async def run_node_script(self, script):
        """Run a Node.js script and return the result"""
        # Create a temporary JS file in the store directory
        temp_script = self.store_dir.parent / 'temp_script.js'
        temp_script.write_text(script)

        process = await asyncio.create_subprocess_exec(
            'node', str(temp_script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ},  # Pass current environment variables to Node
            cwd=str(self.store_dir.parent)  # Run from the project root
        )
        stdout, stderr = await process.communicate()

        # Clean up
        temp_script.unlink()

        if process.returncode != 0:
            raise Exception(f"Node.js error: {stderr.decode()}")

        try:
            return json.loads(stdout.decode())
        except:
            return stdout.decode()

    async def send_tweet(self, text, reply_to=None):
        """Send a tweet with optional reply_to"""
        self.logger.info(f"\n📤 Preparing to send tweet{' as reply' if reply_to else ''}")
        self.logger.info(f"📝 Tweet text: {text}")

        # Properly escape the tweet text for JavaScript
        escaped_text = (
            text.replace('\\', '\\\\')
            .replace("'", "\\'")
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
            .replace('\t', '\\t')
        )

        script = f"""
        const {{ Scraper }} = require('agent-twitter-client');
        const {{ Cookie }} = require('tough-cookie');

        async function tweet() {{
            try {{
                const scraper = new Scraper();
                const cookiesData = require('./cookies.json');

                const cookies = cookiesData.map(cookieData => {{
                    const cookie = new Cookie({{
                        key: cookieData.key,
                        value: cookieData.value,
                        domain: cookieData.domain,
                        path: cookieData.path,
                        secure: cookieData.secure,
                        httpOnly: cookieData.httpOnly
                    }});
                    return cookie.toString();
                }});

                await scraper.setCookies(cookies);

                const response = await scraper.sendTweet('{escaped_text}'{", '" + reply_to + "'" if reply_to else ''});
                console.log(JSON.stringify({{
                    success: true,
                    response: response,
                    text: '{escaped_text}',
                    timestamp: new Date().toISOString()
                }}));
            }} catch (error) {{
                console.log(JSON.stringify({{
                    success: false,
                    error: error.message
                }}));
            }}
        }}

        tweet();
        """

        result = await self.run_node_script(script)
        self.logger.info(f"📨 Tweet API response: {result}")

        if isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                self.logger.info("❌ Failed to parse API response")
                self.logger.error(f"Failed to parse result: {result}")
                return False

        if not result.get('success'):
            self.logger.info(f"❌ Failed to send tweet: {result.get('error')}")
            self.logger.error(f"Failed to send tweet: {result.get('error')}")
            return False

        self.logger.info("✅ Tweet sent successfully!")
        self.logger.info(f"Successfully sent tweet: {text}")
        return True 