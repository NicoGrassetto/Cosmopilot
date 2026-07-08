"""
Verification tests for the shared Cosmopilot tool definitions.

Pure stdlib (``unittest``) so they run without the Azure SDKs. Run with:

    python -m unittest discover -s agents/_shared/tests

The key guard is ``test_hosted_agent_tools_unchanged``: it pins the refactored
tool list to the ORIGINAL inline definitions so the DRY refactor cannot silently
change agent behavior.
"""

import copy
import pathlib
import sys
import unittest

# Put agents/_shared on the path so we can import the module standalone.
_SHARED_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SHARED_DIR))

import cosmos_tools as ct  # noqa: E402


# The exact tool list originally inlined in agents/hosted-agent/agent.py.
# If a refactor changes these, this constant must be updated deliberately.
ORIGINAL_HOSTED_AGENT_TOOLS = [
    {"type": "code_interpreter"},
    {
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
    },
    {
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
    },
]


class ToolBuilderTests(unittest.TestCase):
    def test_hosted_agent_tools_unchanged(self):
        """Refactored builder must reproduce the original inline list exactly."""
        built = ct.tools(
            "code_interpreter", "query_cosmos_db", "get_change_feed_events"
        )
        self.assertEqual(built, ORIGINAL_HOSTED_AGENT_TOOLS)

    def test_code_interpreter_shape(self):
        self.assertEqual(ct.tools("code_interpreter"), [{"type": "code_interpreter"}])

    def test_dedup_preserves_first_seen_order(self):
        built = ct.tools(
            "code_interpreter", "query_cosmos_db", "code_interpreter"
        )
        names = [t.get("function", {}).get("name", t["type"]) for t in built]
        self.assertEqual(names, ["code_interpreter", "query_cosmos_db"])

    def test_unknown_tool_raises_keyerror(self):
        with self.assertRaises(KeyError):
            ct.tools("does_not_exist")

    def test_returns_deep_copies(self):
        a = ct.tools("query_cosmos_db")[0]
        a["function"]["description"] = "MUTATED"
        # Shared schema and a fresh build must be untouched.
        self.assertNotEqual(
            ct.QUERY_COSMOS_DB["function"]["description"], "MUTATED"
        )
        self.assertNotEqual(
            ct.tools("query_cosmos_db")[0]["function"]["description"], "MUTATED"
        )

    def test_empty_call_returns_empty_list(self):
        self.assertEqual(ct.tools(), [])


class RegistryTests(unittest.TestCase):
    def test_all_schemas_include_custom_and_builtins(self):
        self.assertEqual(
            set(ct.ALL_TOOL_SCHEMAS),
            {"query_cosmos_db", "get_change_feed_events", "code_interpreter"},
        )

    def test_schema_names_match_registry_keys(self):
        for name, schema in ct.COSMOS_TOOL_SCHEMAS.items():
            self.assertEqual(schema["function"]["name"], name)

    def test_every_cosmos_schema_has_an_implementation(self):
        self.assertEqual(
            set(ct.COSMOS_TOOL_SCHEMAS), set(ct.TOOL_IMPLEMENTATIONS)
        )

    def test_all_tools_and_cosmos_tools_helpers(self):
        self.assertEqual(len(ct.all_tools()), 3)
        self.assertEqual(len(ct.cosmos_tools()), 2)
        self.assertEqual(set(ct.tool_names()), set(ct.ALL_TOOL_SCHEMAS))

    def test_call_tool_unknown_raises(self):
        with self.assertRaises(KeyError):
            ct.call_tool("nope")

    def test_required_fields_present(self):
        self.assertEqual(
            ct.QUERY_COSMOS_DB["function"]["parameters"]["required"], ["query"]
        )


class ImportSafetyTests(unittest.TestCase):
    def test_module_imports_without_azure_sdk(self):
        """Importing the definitions must not require azure.* to be installed."""
        self.assertNotIn("azure.cosmos", sys.modules)


if __name__ == "__main__":
    unittest.main()
