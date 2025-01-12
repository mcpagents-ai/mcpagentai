import asyncio
import os

from mcpagentai.server import start_server

def main():
    """
    CLI entry point for the 'mcpagentai' command.
    """
    local_timezone = os.getenv("LOCAL_TIMEZONE", None)
    asyncio.run(start_server(local_timezone=local_timezone))
