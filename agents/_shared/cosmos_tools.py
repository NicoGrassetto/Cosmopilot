"""
Cosmopilot shared agent tools — single source of truth (DRY).

Declare each custom tool's JSON schema and implementation **once** here, then
reuse it across every agent style:

    from _shared import tools

    agent = client.agents.create(
        ...,
        tools=tools("code_interpreter", "query_cosmos_db", "get_change_feed_events"),
    )

Design rules:
- **No top-level third-party imports.** The schema/registry layer is pure stdlib
  so it imports and unit-tests anywhere (no Azure SDK required). The Cosmos
  implementations lazy-import ``azure.cosmos`` only when actually called.
- ``tools(*names)`` returns deep-copied dicts so an agent can never mutate the
  shared schema for the others.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Tool schemas (OpenAI / Foundry function-tool shape) — declared ONCE
# ---------------------------------------------------------------------------

QUERY_COSMOS_DB: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "query_cosmos_db",
        "description": "Execute a SQL query against Cosmos DB and return results",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute against Cosmos DB",
                },
                "container": {
                    "type": "string",
                    "description": "Target container name",
                    "default": "conversations",
                },
            },
            "required": ["query"],
        },
    },
}

GET_CHANGE_FEED_EVENTS: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_change_feed_events",
        "description": "Retrieve recent change feed events from Cosmos DB",
        "parameters": {
            "type": "object",
            "properties": {
                "since_minutes": {
                    "type": "integer",
                    "description": "Number of minutes to look back",
                    "default": 60,
                },
                "container": {
                    "type": "string",
                    "description": "Target container name",
                    "default": "conversations",
                },
            },
        },
    },
}

CODE_INTERPRETER: dict[str, Any] = {"type": "code_interpreter"}

# Custom (client-side) function tools, keyed by tool name.
COSMOS_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "query_cosmos_db": QUERY_COSMOS_DB,
    "get_change_feed_events": GET_CHANGE_FEED_EVENTS,
}

# Every tool the agents can request by name (custom + built-ins).
ALL_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    **COSMOS_TOOL_SCHEMAS,
    "code_interpreter": CODE_INTERPRETER,
}


# ---------------------------------------------------------------------------
# Tool-list builders — use these instead of inlining tool dicts in each agent
# ---------------------------------------------------------------------------

def tools(*names: str) -> list[dict[str, Any]]:
    """Build a Foundry ``tools=[...]`` list from tool names.

    Deduplicates while preserving first-seen order, and deep-copies each schema
    so callers cannot mutate the shared definitions. Unknown names raise
    ``KeyError`` so typos fail fast at construction time.
    """
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        try:
            schema = ALL_TOOL_SCHEMAS[name]
        except KeyError:
            raise KeyError(
                f"Unknown tool {name!r}. Known tools: "
                f"{', '.join(sorted(ALL_TOOL_SCHEMAS))}"
            ) from None
        result.append(copy.deepcopy(schema))
    return result


def all_tools() -> list[dict[str, Any]]:
    """Every declared tool (custom function tools + ``code_interpreter``)."""
    return tools(*ALL_TOOL_SCHEMAS)


def cosmos_tools() -> list[dict[str, Any]]:
    """Only the custom Cosmos DB function tools."""
    return tools(*COSMOS_TOOL_SCHEMAS)


def tool_names() -> list[str]:
    """Names of all declared tools."""
    return list(ALL_TOOL_SCHEMAS)


# ---------------------------------------------------------------------------
# Implementations — declared ONCE, reused by the MCP server and any client-side
# tool-call resolver. Azure SDKs are imported lazily so importing this module
# stays dependency-free.
# ---------------------------------------------------------------------------

def _container_client(container: str):
    """Return a Cosmos DB container client using Entra ID (passwordless) auth."""
    import os

    from azure.cosmos import CosmosClient  # lazy import — optional dependency
    from azure.identity import DefaultAzureCredential

    endpoint = os.environ["COSMOS_DB_ENDPOINT"]
    database = os.environ.get("COSMOS_DB_DATABASE", "cosmopilot")

    client = CosmosClient(endpoint, credential=DefaultAzureCredential())
    return client.get_database_client(database).get_container_client(container)


def query_cosmos_db(query: str, container: str = "conversations") -> list[dict[str, Any]]:
    """Execute a SQL query against Cosmos DB and return the matching items."""
    client = _container_client(container)
    return list(
        client.query_items(query=query, enable_cross_partition_query=True)
    )


def get_change_feed_events(
    since_minutes: int = 60, container: str = "conversations"
) -> list[dict[str, Any]]:
    """Retrieve items changed within the last ``since_minutes`` minutes.

    Uses the Cosmos ``_ts`` system field (epoch seconds) as the change marker so
    it works without an explicit change-feed lease container.
    """
    from datetime import datetime, timedelta, timezone

    start_ts = int(
        (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).timestamp()
    )
    client = _container_client(container)
    return list(
        client.query_items(
            query="SELECT * FROM c WHERE c._ts >= @start ORDER BY c._ts DESC",
            parameters=[{"name": "@start", "value": start_ts}],
            enable_cross_partition_query=True,
        )
    )


# Map tool name -> callable implementation (single source of truth).
TOOL_IMPLEMENTATIONS: dict[str, Callable[..., Any]] = {
    "query_cosmos_db": query_cosmos_db,
    "get_change_feed_events": get_change_feed_events,
}


def call_tool(name: str, **kwargs: Any) -> Any:
    """Invoke a custom tool implementation by name (for tool-call resolvers)."""
    try:
        impl = TOOL_IMPLEMENTATIONS[name]
    except KeyError:
        raise KeyError(
            f"No implementation for tool {name!r}. Implemented: "
            f"{', '.join(sorted(TOOL_IMPLEMENTATIONS))}"
        ) from None
    return impl(**kwargs)


__all__ = [
    "QUERY_COSMOS_DB",
    "GET_CHANGE_FEED_EVENTS",
    "CODE_INTERPRETER",
    "COSMOS_TOOL_SCHEMAS",
    "ALL_TOOL_SCHEMAS",
    "TOOL_IMPLEMENTATIONS",
    "tools",
    "all_tools",
    "cosmos_tools",
    "tool_names",
    "query_cosmos_db",
    "get_change_feed_events",
    "call_tool",
]
