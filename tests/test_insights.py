import json
import sys
from unittest.mock import MagicMock, call

import evaluations.insights as insights


def test_insight_wrappers_delegate_to_beta_insights(monkeypatch):
    endpoint = "https://example.services.ai.azure.com/api/projects/test"
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", endpoint)

    credential_context = MagicMock()
    credential = object()
    credential_context.__enter__.return_value = credential
    credential_factory = MagicMock(return_value=credential_context)

    client = MagicMock()
    client.__enter__.return_value = client
    client_factory = MagicMock(return_value=client)
    sdk_insights = client.beta.insights

    monkeypatch.setattr(insights, "DefaultAzureCredential", credential_factory)
    monkeypatch.setattr(insights, "AIProjectClient", client_factory)

    definition = {
        "displayName": "Release comparison",
        "request": {
            "type": "EvaluationComparison",
            "evalId": "evaluation-1",
            "baselineRunId": "run-1",
            "treatmentRunIds": ["run-2"],
        },
    }
    generated = object()
    sdk_insights.generate.return_value = generated
    assert insights.generate_insight(definition) is generated
    sdk_insights.generate.assert_called_once_with(insight=definition)

    retrieved = object()
    sdk_insights.get.return_value = retrieved
    assert insights.get_insight(
        "insight-1",
        include_coordinates=True,
    ) is retrieved
    sdk_insights.get.assert_called_once_with(
        insight_id="insight-1",
        include_coordinates=True,
    )

    listed = [object(), object()]
    sdk_insights.list.return_value = iter(listed)
    assert insights.list_insights(
        insight_type="EvaluationComparison",
        eval_id="evaluation-1",
        run_id="run-2",
        agent_name="support-agent",
        include_coordinates=False,
    ) == listed
    sdk_insights.list.assert_called_once_with(
        type="EvaluationComparison",
        eval_id="evaluation-1",
        run_id="run-2",
        agent_name="support-agent",
        include_coordinates=False,
    )

    assert credential_factory.call_count == 3
    assert client_factory.call_args_list == [
        call(endpoint=endpoint, credential=credential)
    ] * 3


def test_generate_command_loads_insight_json(monkeypatch, tmp_path, capsys):
    definition = {
        "displayName": "Agent clusters",
        "request": {
            "type": "AgentClusterInsight",
            "agentName": "support-agent",
        },
    }
    definition_path = tmp_path / "insight.json"
    definition_path.write_text(json.dumps(definition), encoding="utf-8")

    result = MagicMock()
    result.as_dict.return_value = {"id": "insight-1"}
    generate_insight = MagicMock(return_value=result)
    monkeypatch.setattr(insights, "generate_insight", generate_insight)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insights", "generate", "--insight", str(definition_path)],
    )

    insights.main()

    generate_insight.assert_called_once_with(definition)
    assert json.loads(capsys.readouterr().out) == {"id": "insight-1"}


def test_get_command_forwards_coordinate_option(monkeypatch, capsys):
    result = MagicMock()
    result.as_dict.return_value = {"id": "insight-1", "state": "Succeeded"}
    get_insight = MagicMock(return_value=result)
    monkeypatch.setattr(insights, "get_insight", get_insight)
    monkeypatch.setattr(
        sys,
        "argv",
        ["insights", "get", "--insight-id", "insight-1", "--include-coordinates"],
    )

    insights.main()

    get_insight.assert_called_once_with(
        "insight-1",
        include_coordinates=True,
    )
    assert json.loads(capsys.readouterr().out) == {
        "id": "insight-1",
        "state": "Succeeded",
    }


def test_list_command_forwards_filters(monkeypatch, capsys):
    result = MagicMock()
    result.as_dict.return_value = {"id": "insight-1"}
    list_insights = MagicMock(return_value=[result])
    monkeypatch.setattr(insights, "list_insights", list_insights)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "insights",
            "list",
            "--type",
            "EvaluationRunClusterInsight",
            "--eval-id",
            "evaluation-1",
            "--run-id",
            "run-1",
            "--agent-name",
            "support-agent",
            "--no-include-coordinates",
        ],
    )

    insights.main()

    list_insights.assert_called_once_with(
        insight_type="EvaluationRunClusterInsight",
        eval_id="evaluation-1",
        run_id="run-1",
        agent_name="support-agent",
        include_coordinates=False,
    )
    assert json.loads(capsys.readouterr().out) == [{"id": "insight-1"}]