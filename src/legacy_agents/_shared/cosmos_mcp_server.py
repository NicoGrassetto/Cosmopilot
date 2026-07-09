"""
Cosmos DB MCP server for Cosmopilot (Foundry Toolbox layer).

Exposes the SAME custom tools defined in ``cosmos_tools.py`` over the Model
Context Protocol so they can be registered in a Foundry **Toolbox** and reused
by *every* agent style — including prompt agents and YAML workflows that cannot
import Python — through a single ``TOOLBOX_ENDPOINT``.

There is no second copy of the tool logic here: each MCP tool delegates to the
shared implementation, keeping one source of truth.

Run locally (stdio):

    pip install -r requirements.txt
    python cosmos_mcp_server.py

Then wire it into a Foundry Toolbox (see ``toolbox.yaml`` and the README).
"""

from __future__ import annotations

from typing import Any

# When run as a script, this file's directory is on sys.path, so the shared
# module imports directly. (Consumers that import the package use ``_shared``.)
from cosmos_tools import get_change_feed_events as _get_change_feed_events
from cosmos_tools import query_cosmos_db as _query_cosmos_db

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on optional 'mcp' extra
    raise SystemExit(
        "The 'mcp' package is required to run the Cosmos MCP server.\n"
        "Install it with: pip install -r requirements.txt"
    ) from exc

mcp = FastMCP("cosmos-mcp")


@mcp.tool()
def query_cosmos_db(query: str, container: str = "conversations") -> list[dict[str, Any]]:
    """Execute a SQL query against Cosmos DB and return results."""
    return _query_cosmos_db(query, container)


@mcp.tool()
def get_change_feed_events(
    since_minutes: int = 60, container: str = "conversations"
) -> list[dict[str, Any]]:
    """Retrieve recent change feed events from Cosmos DB."""
    return _get_change_feed_events(since_minutes, container)


if __name__ == "__main__":
    mcp.run()
