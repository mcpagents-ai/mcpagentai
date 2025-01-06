import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import TimeTools, TimeResult, TimeConversionResult


class TimeAgent(MCPAgent):
    """
    Agent that handles time-related functionality (current time, time conversions).
    """

    def __init__(self, local_timezone: str | None = None):
        super().__init__()
        self._local_timezone = local_timezone or self._autodetect_local_timezone()

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=TimeTools.GET_CURRENT_TIME.value,
                description="Get current time in a specific timezone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": (
                                f"IANA timezone name (e.g. 'America/New_York'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        }
                    },
                    "required": ["timezone"],
                },
            ),
            Tool(
                name=TimeTools.CONVERT_TIME.value,
                description="Convert time between timezones",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_timezone": {
                            "type": "string",
                            "description": (
                                f"Source IANA timezone name (e.g. 'America/New_York'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        },
                        "time": {
                            "type": "string",
                            "description": "Time to convert in 24-hour format (HH:MM)",
                        },
                        "target_timezone": {
                            "type": "string",
                            "description": (
                                f"Target IANA timezone name (e.g. 'Asia/Tokyo'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        },
                    },
                    "required": ["source_timezone", "time", "target_timezone"],
                },
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == TimeTools.GET_CURRENT_TIME.value:
            return self._handle_get_current_time(arguments)
        elif name == TimeTools.CONVERT_TIME.value:
            return self._handle_convert_time(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_get_current_time(self, arguments: dict) -> Sequence[TextContent]:
        timezone_name = arguments.get("timezone") or self._local_timezone
        result_model = self._get_current_time(timezone_name)
        return [
            TextContent(type="text", text=json.dumps(result_model.model_dump(), indent=2))
        ]

    def _handle_convert_time(self, arguments: dict) -> Sequence[TextContent]:
        source_tz = arguments.get("source_timezone") or self._local_timezone
        time_str = arguments.get("time")
        target_tz = arguments.get("target_timezone") or self._local_timezone

        if not time_str:
            raise ValueError("Time string must be provided.")

        result_model = self._convert_time(source_tz, time_str, target_tz)
        return [
            TextContent(type="text", text=json.dumps(result_model.model_dump(), indent=2))
        ]

    def _autodetect_local_timezone(self) -> str:
        tzinfo = datetime.now().astimezone().tzinfo
        if tzinfo is not None:
            return str(tzinfo)
        raise McpError("Could not determine local timezone - tzinfo is None")

    def _get_current_time(self, timezone_name: str) -> TimeResult:
        timezone = self._get_zoneinfo(timezone_name)
        current_time = datetime.now(timezone)
        return TimeResult(
            timezone=timezone_name,
            datetime=current_time.isoformat(timespec="seconds"),
            is_dst=bool(current_time.dst()),
        )

    def _convert_time(self, source_tz: str, time_str: str, target_tz: str) -> TimeConversionResult:
        source_timezone = self._get_zoneinfo(source_tz)
        target_timezone = self._get_zoneinfo(target_tz)

        # parse HH:MM format
        try:
            hh_mm = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM in 24-hour format.")

        # use today's date for demonstration
        now = datetime.now(source_timezone)
        source_time = datetime(
            now.year, now.month, now.day,
            hh_mm.hour, hh_mm.minute, tzinfo=source_timezone
        )
        target_time = source_time.astimezone(target_timezone)

        source_offset = source_time.utcoffset() or timedelta()
        target_offset = target_time.utcoffset() or timedelta()
        hours_diff = (target_offset - source_offset).total_seconds() / 3600

        if hours_diff.is_integer():
            time_diff_str = f"{hours_diff:+.1f}h"
        else:
            # handle e.g. UTC+5:45 with fractional offsets
            time_diff_str = f"{hours_diff:+.2f}".rstrip("0").rstrip(".") + "h"

        return TimeConversionResult(
            source=TimeResult(
                timezone=source_tz,
                datetime=source_time.isoformat(timespec="seconds"),
                is_dst=bool(source_time.dst()),
            ),
            target=TimeResult(
                timezone=target_tz,
                datetime=target_time.isoformat(timespec="seconds"),
                is_dst=bool(target_time.dst()),
            ),
            time_difference=time_diff_str
        )

    def _get_zoneinfo(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except Exception as e:
            raise McpError(f"Invalid timezone: {str(e)}") from e
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Sequence, Union

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import TimeTools, TimeResult, TimeConversionResult


class TimeAgent(MCPAgent):
    """
    Agent that handles time-related functionality (current time, time conversions).
    """

    def __init__(self, local_timezone: str | None = None):
        super().__init__()
        self._local_timezone = local_timezone or self._autodetect_local_timezone()

    def list_tools(self) -> list[Tool]:
        return [
            Tool(
                name=TimeTools.GET_CURRENT_TIME.value,
                description="Get current time in a specific timezone",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": (
                                f"IANA timezone name (e.g. 'America/New_York'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        }
                    },
                    "required": ["timezone"],
                },
            ),
            Tool(
                name=TimeTools.CONVERT_TIME.value,
                description="Convert time between timezones",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_timezone": {
                            "type": "string",
                            "description": (
                                f"Source IANA timezone name (e.g. 'America/New_York'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        },
                        "time": {
                            "type": "string",
                            "description": "Time to convert in 24-hour format (HH:MM)",
                        },
                        "target_timezone": {
                            "type": "string",
                            "description": (
                                f"Target IANA timezone name (e.g. 'Asia/Tokyo'). "
                                f"Use '{self._local_timezone}' if not provided."
                            ),
                        },
                    },
                    "required": ["source_timezone", "time", "target_timezone"],
                },
            ),
        ]

    def call_tool(
        self,
        name: str,
        arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == TimeTools.GET_CURRENT_TIME.value:
            return self._handle_get_current_time(arguments)
        elif name == TimeTools.CONVERT_TIME.value:
            return self._handle_convert_time(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    def _handle_get_current_time(self, arguments: dict) -> Sequence[TextContent]:
        timezone_name = arguments.get("timezone") or self._local_timezone
        result_model = self._get_current_time(timezone_name)
        return [
            TextContent(type="text", text=json.dumps(result_model.model_dump(), indent=2))
        ]

    def _handle_convert_time(self, arguments: dict) -> Sequence[TextContent]:
        source_tz = arguments.get("source_timezone") or self._local_timezone
        time_str = arguments.get("time")
        target_tz = arguments.get("target_timezone") or self._local_timezone

        if not time_str:
            raise ValueError("Time string must be provided.")

        result_model = self._convert_time(source_tz, time_str, target_tz)
        return [
            TextContent(type="text", text=json.dumps(result_model.model_dump(), indent=2))
        ]

    def _autodetect_local_timezone(self) -> str:
        tzinfo = datetime.now().astimezone().tzinfo
        if tzinfo is not None:
            return str(tzinfo)
        raise McpError("Could not determine local timezone - tzinfo is None")

    def _get_current_time(self, timezone_name: str) -> TimeResult:
        timezone = self._get_zoneinfo(timezone_name)
        current_time = datetime.now(timezone)
        return TimeResult(
            timezone=timezone_name,
            datetime=current_time.isoformat(timespec="seconds"),
            is_dst=bool(current_time.dst()),
        )

    def _convert_time(self, source_tz: str, time_str: str, target_tz: str) -> TimeConversionResult:
        source_timezone = self._get_zoneinfo(source_tz)
        target_timezone = self._get_zoneinfo(target_tz)

        # parse HH:MM format
        try:
            hh_mm = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError("Invalid time format. Expected HH:MM in 24-hour format.")

        # use today's date for demonstration
        now = datetime.now(source_timezone)
        source_time = datetime(
            now.year, now.month, now.day,
            hh_mm.hour, hh_mm.minute, tzinfo=source_timezone
        )
        target_time = source_time.astimezone(target_timezone)

        source_offset = source_time.utcoffset() or timedelta()
        target_offset = target_time.utcoffset() or timedelta()
        hours_diff = (target_offset - source_offset).total_seconds() / 3600

        if hours_diff.is_integer():
            time_diff_str = f"{hours_diff:+.1f}h"
        else:
            # handle e.g. UTC+5:45 with fractional offsets
            time_diff_str = f"{hours_diff:+.2f}".rstrip("0").rstrip(".") + "h"

        return TimeConversionResult(
            source=TimeResult(
                timezone=source_tz,
                datetime=source_time.isoformat(timespec="seconds"),
                is_dst=bool(source_time.dst()),
            ),
            target=TimeResult(
                timezone=target_tz,
                datetime=target_time.isoformat(timespec="seconds"),
                is_dst=bool(target_time.dst()),
            ),
            time_difference=time_diff_str
        )

    def _get_zoneinfo(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except Exception as e:
            raise McpError(f"Invalid timezone: {str(e)}") from e
