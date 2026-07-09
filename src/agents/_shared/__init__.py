"""Cosmopilot shared agent tooling.

Single source of truth for tool schemas and implementations reused across all
agent styles. Import the builders directly:

    from _shared import tools, cosmos_tools, all_tools
"""

from __future__ import annotations

from .cosmos_tools import (
    ALL_TOOL_SCHEMAS,
    CODE_INTERPRETER,
    COSMOS_TOOL_SCHEMAS,
    GET_CHANGE_FEED_EVENTS,
    QUERY_COSMOS_DB,
    TOOL_IMPLEMENTATIONS,
    all_tools,
    call_tool,
    cosmos_tools,
    get_change_feed_events,
    query_cosmos_db,
    tool_names,
    tools,
)

__all__ = [
    "ALL_TOOL_SCHEMAS",
    "CODE_INTERPRETER",
    "COSMOS_TOOL_SCHEMAS",
    "GET_CHANGE_FEED_EVENTS",
    "QUERY_COSMOS_DB",
    "TOOL_IMPLEMENTATIONS",
    "all_tools",
    "call_tool",
    "cosmos_tools",
    "get_change_feed_events",
    "query_cosmos_db",
    "tool_names",
    "tools",
]
