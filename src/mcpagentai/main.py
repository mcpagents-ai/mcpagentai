import argparse
import asyncio

from .server import start_server


def main():
    """
    MCP Agent AI - A multi-tool server (time, weather, dictionary, calculator).
    """
    parser = argparse.ArgumentParser(
        description="Run the MCPAgentAI server (time, weather, dictionary, calculator, etc.)."
    )
    parser.add_argument("--local-timezone", type=str, help="Override local timezone for the TimeAgent.")
    args = parser.parse_args()

    asyncio.run(start_server(local_timezone=args.local_timezone))
