import json
import sys

import pytest

import connections


@pytest.mark.integration
def testget_connection():
    connection = connections.get_connection("aisearch")

    assert connection.name == "aisearch"


@pytest.mark.integration
def testget_default_connection():
    connection = connections.get_default_connection("CognitiveSearch")

    assert connection.name == "aisearch"


@pytest.mark.integration
def testlist_connections():
    project_connections = connections.list_connections(
        connection_type="CognitiveSearch",
    )

    assert any(connection.name == "aisearch" for connection in project_connections)