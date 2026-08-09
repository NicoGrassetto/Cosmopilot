import json
from io import BytesIO
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from azure.ai.projects import models

from agents import agents


class SerializableResult:
    def __init__(self, **values):
        self.values = values

    def as_dict(self):
        return self.values


def mock_project_client(monkeypatch: pytest.MonkeyPatch):
    credential = MagicMock()
    credential.__enter__.return_value = credential

    client = MagicMock()
    client.__enter__.return_value = client

    client_factory = MagicMock(return_value=client)
    monkeypatch.setattr(agents, "DefaultAzureCredential", MagicMock(return_value=credential))
    monkeypatch.setattr(agents, "AIProjectClient", client_factory)
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://example.test/project")
    return client


def run_cli(monkeypatch, capsys, *arguments):
    monkeypatch.setattr(sys, "argv", ["agents", *arguments])
    agents.main()
    return json.loads(capsys.readouterr().out)


def test_agent_version_wrappers(monkeypatch):
    client = mock_project_client(monkeypatch)
    definition = models.AgentDefinition({"kind": "prompt", "model": "test-model"})
    blueprint_reference = models.AgentBlueprintReference({"id": "blueprint-1"})
    created_version = SimpleNamespace(name="test-agent", version="1")
    client.agents.create_version.return_value = created_version

    assert agents.create_agent_version(
        "test-agent",
        definition=definition,
        metadata={"owner": "test"},
        description="Test agent",
        blueprint_reference=blueprint_reference,
        draft=True,
    ) is created_version
    client.agents.create_version.assert_called_once_with(
        agent_name="test-agent",
        definition=definition,
        content_type="application/json",
        metadata={"owner": "test"},
        description="Test agent",
        blueprint_reference=blueprint_reference,
        draft=True,
    )

    manifest_version = SimpleNamespace(name="test-agent", version="2")
    client.agents.create_version_from_manifest.return_value = manifest_version
    assert agents.create_version_from_manifest(
        "test-agent",
        manifest_id="manifest-1",
        parameter_values={"model": "test-model"},
        metadata={"owner": "test"},
        description="Manifest version",
    ) is manifest_version
    client.agents.create_version_from_manifest.assert_called_once_with(
        agent_name="test-agent",
        manifest_id="manifest-1",
        parameter_values={"model": "test-model"},
        content_type="application/json",
        metadata={"owner": "test"},
        description="Manifest version",
    )

    hosted_definition = models.HostedAgentDefinition(
        {"cpu": "0.5", "memory": "1Gi"}
    )
    code = BytesIO(b"code")
    code_version = SimpleNamespace(name="hosted-agent", version="1")
    client.agents.create_version_from_code.return_value = code_version
    assert agents.create_version_from_code(
        "hosted-agent",
        definition=hosted_definition,
        code=code,
        code_zip_sha256="abc123",
        description="Hosted version",
        metadata={"owner": "test"},
    ) is code_version
    client.agents.create_version_from_code.assert_called_once_with(
        agent_name="hosted-agent",
        definition=hosted_definition,
        code=code,
        code_zip_sha256="abc123",
        description="Hosted version",
        metadata={"owner": "test"},
    )

    client.agents.download_code.return_value = iter((b"zip-", b"content"))
    assert b"".join(
        agents.download_code("hosted-agent", agent_version="1")
    ) == b"zip-content"
    client.agents.download_code.assert_called_once_with(
        agent_name="hosted-agent",
        agent_version="1",
    )


def test_session_wrappers(monkeypatch):
    client = mock_project_client(monkeypatch)
    version_indicator = models.VersionIndicator({"agent_version": "1"})
    created_session = SimpleNamespace(
        agent_session_id="session-1",
        status="running",
    )
    client.agents.create_session.return_value = created_session

    assert agents.create_session(
        "hosted-agent",
        version_indicator=version_indicator,
        agent_session_id="session-1",
    ) is created_session
    client.agents.create_session.assert_called_once_with(
        agent_name="hosted-agent",
        version_indicator=version_indicator,
        content_type="application/json",
        agent_session_id="session-1",
    )

    retrieved_session = SimpleNamespace(
        agent_session_id="session-1",
        status="running",
    )
    client.agents.get_session.return_value = retrieved_session
    assert agents.get_session("hosted-agent", "session-1") is retrieved_session
    client.agents.get_session.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
    )

    listed_sessions = [retrieved_session]
    client.agents.list_sessions.return_value = listed_sessions
    assert agents.list_sessions(
        "hosted-agent",
        limit=10,
        order="desc",
        before="session-2",
    ) == listed_sessions
    client.agents.list_sessions.assert_called_once_with(
        agent_name="hosted-agent",
        limit=10,
        order="desc",
        before="session-2",
    )

    assert agents.stop_session("hosted-agent", "session-1") is None
    client.agents.stop_session.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
    )

    assert agents.delete_session("hosted-agent", "session-1") is None
    client.agents.delete_session.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
    )

    client.agents.get_session_log_stream.return_value = iter((b"event: ", b"log"))
    assert b"".join(
        agents.get_session_log_stream(
            "hosted-agent",
            "1",
            "session-1",
        )
    ) == b"event: log"
    client.agents.get_session_log_stream.assert_called_once_with(
        agent_name="hosted-agent",
        agent_version="1",
        session_id="session-1",
    )


def test_session_file_wrappers(monkeypatch):
    client = mock_project_client(monkeypatch)
    listed_entries = [SimpleNamespace(name="input.txt")]
    client.agents.list_session_files.return_value = listed_entries

    assert agents.list_session_files(
        "hosted-agent",
        "session-1",
        path="/data",
        limit=10,
        order="asc",
        before="entry-2",
    ) == listed_entries
    client.agents.list_session_files.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data",
        limit=10,
        order="asc",
        before="entry-2",
    )

    upload_result = SimpleNamespace(path="/data/input.txt")
    client.agents.upload_session_file.return_value = upload_result
    assert agents.upload_session_file(
        "hosted-agent",
        "session-1",
        b"input",
        path="/data/input.txt",
    ) is upload_result
    client.agents.upload_session_file.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        content=b"input",
        path="/data/input.txt",
    )

    client.agents.download_session_file.return_value = iter((b"out", b"put"))
    assert b"".join(
        agents.download_session_file(
            "hosted-agent",
            "session-1",
            path="/data/output.txt",
        )
    ) == b"output"
    client.agents.download_session_file.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data/output.txt",
    )

    assert agents.delete_session_file(
        "hosted-agent",
        "session-1",
        path="/data",
        recursive=True,
    ) is None
    client.agents.delete_session_file.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data",
        recursive=True,
    )


def test_agent_version_commands(monkeypatch, tmp_path, capsys):
    definition_file = tmp_path / "definition.json"
    definition_file.write_text(
        '{"kind": "prompt", "model": "test-model"}',
        encoding="utf-8",
    )
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text('{"owner": "test"}', encoding="utf-8")
    blueprint_file = tmp_path / "blueprint.json"
    blueprint_file.write_text('{"id": "blueprint-1"}', encoding="utf-8")

    create_command = MagicMock(
        return_value=SerializableResult(name="test-agent", version="1")
    )
    monkeypatch.setattr(agents, "create_agent_version", create_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "--allow-preview",
        "create-agent-version",
        "--agent-name",
        "test-agent",
        "--definition-file",
        str(definition_file),
        "--metadata-file",
        str(metadata_file),
        "--description",
        "Test agent",
        "--blueprint-reference-file",
        str(blueprint_file),
        "--draft",
    )
    create_arguments = create_command.call_args.kwargs
    assert create_arguments["definition"].as_dict() == {
        "kind": "prompt",
        "model": "test-model",
    }
    assert create_arguments["metadata"] == {"owner": "test"}
    assert create_arguments["blueprint_reference"].as_dict() == {
        "id": "blueprint-1"
    }
    assert create_arguments["draft"] is True
    assert create_arguments["allow_preview"] is True
    assert output == {"name": "test-agent", "version": "1"}

    parameter_values_file = tmp_path / "parameter-values.json"
    parameter_values_file.write_text(
        '{"model": "test-model"}',
        encoding="utf-8",
    )
    manifest_command = MagicMock(
        return_value=SerializableResult(name="test-agent", version="2")
    )
    monkeypatch.setattr(agents, "create_version_from_manifest", manifest_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "create-version-from-manifest",
        "--agent-name",
        "test-agent",
        "--manifest-id",
        "manifest-1",
        "--parameter-values-file",
        str(parameter_values_file),
        "--metadata-file",
        str(metadata_file),
        "--description",
        "Manifest version",
    )
    manifest_command.assert_called_once_with(
        agent_name="test-agent",
        manifest_id="manifest-1",
        parameter_values={"model": "test-model"},
        metadata={"owner": "test"},
        description="Manifest version",
        allow_preview=False,
    )
    assert output == {"name": "test-agent", "version": "2"}

    hosted_definition_file = tmp_path / "hosted-definition.json"
    hosted_definition_file.write_text(
        '{"cpu": "0.5", "memory": "1Gi"}',
        encoding="utf-8",
    )
    code_file = tmp_path / "hosted-agent.zip"
    code_file.write_bytes(b"code")
    code_command = MagicMock(
        return_value=SerializableResult(name="hosted-agent", version="1")
    )
    monkeypatch.setattr(agents, "create_version_from_code", code_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "create-version-from-code",
        "--agent-name",
        "hosted-agent",
        "--definition-file",
        str(hosted_definition_file),
        "--code-file",
        str(code_file),
        "--code-zip-sha256",
        "abc123",
        "--metadata-file",
        str(metadata_file),
        "--description",
        "Hosted version",
    )
    code_arguments = code_command.call_args.kwargs
    assert code_arguments["definition"].as_dict() == {
        "cpu": "0.5",
        "memory": "1Gi",
        "kind": "hosted",
    }
    assert code_arguments["code"].name == str(code_file)
    assert code_arguments["code"].closed
    assert code_arguments["code_zip_sha256"] == "abc123"
    assert code_arguments["metadata"] == {"owner": "test"}
    assert output == {"name": "hosted-agent", "version": "1"}

    downloaded_code = tmp_path / "downloaded-agent.zip"
    download_command = MagicMock(return_value=iter((b"zip-", b"content")))
    monkeypatch.setattr(agents, "download_code", download_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "download-code",
        "--agent-name",
        "hosted-agent",
        "--agent-version",
        "1",
        "--output",
        str(downloaded_code),
    )
    download_command.assert_called_once_with(
        agent_name="hosted-agent",
        agent_version="1",
        allow_preview=False,
    )
    assert downloaded_code.read_bytes() == b"zip-content"
    assert output["bytes"] == len(b"zip-content")


def test_session_commands(monkeypatch, tmp_path, capsys):
    version_indicator_file = tmp_path / "version-indicator.json"
    version_indicator_file.write_text(
        '{"agent_version": "1"}',
        encoding="utf-8",
    )
    create_command = MagicMock(
        return_value=SerializableResult(
            agent_session_id="session-1",
            status="running",
        )
    )
    monkeypatch.setattr(agents, "create_session", create_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "create-session",
        "--agent-name",
        "hosted-agent",
        "--version-indicator-file",
        str(version_indicator_file),
        "--session-id",
        "session-1",
    )
    create_arguments = create_command.call_args.kwargs
    assert create_arguments["version_indicator"].as_dict() == {
        "agent_version": "1"
    }
    assert create_arguments["agent_session_id"] == "session-1"
    assert output["agent_session_id"] == "session-1"

    get_command = MagicMock(
        return_value=SerializableResult(
            agent_session_id="session-1",
            status="running",
        )
    )
    monkeypatch.setattr(agents, "get_session", get_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "get-session",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
    )
    get_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        allow_preview=False,
    )
    assert output["status"] == "running"

    list_command = MagicMock(
        return_value=[SerializableResult(agent_session_id="session-1")]
    )
    monkeypatch.setattr(agents, "list_sessions", list_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "list-sessions",
        "--agent-name",
        "hosted-agent",
        "--limit",
        "10",
        "--order",
        "desc",
        "--before",
        "session-2",
    )
    list_command.assert_called_once_with(
        agent_name="hosted-agent",
        limit=10,
        order="desc",
        before="session-2",
        allow_preview=False,
    )
    assert output == [{"agent_session_id": "session-1"}]

    stop_command = MagicMock(return_value=None)
    monkeypatch.setattr(agents, "stop_session", stop_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "stop-session",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
    )
    stop_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        allow_preview=False,
    )
    assert output == {"session_id": "session-1", "stopped": True}

    delete_command = MagicMock(return_value=None)
    monkeypatch.setattr(agents, "delete_session", delete_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "delete-session",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
    )
    delete_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        allow_preview=False,
    )
    assert output == {"session_id": "session-1", "deleted": True}

    log_file = tmp_path / "session.log"
    log_command = MagicMock(return_value=iter((b"event: ", b"log")))
    monkeypatch.setattr(agents, "get_session_log_stream", log_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "get-session-log-stream",
        "--agent-name",
        "hosted-agent",
        "--agent-version",
        "1",
        "--session-id",
        "session-1",
        "--output",
        str(log_file),
    )
    log_command.assert_called_once_with(
        agent_name="hosted-agent",
        agent_version="1",
        session_id="session-1",
        allow_preview=False,
    )
    assert log_file.read_bytes() == b"event: log"
    assert output["bytes"] == len(b"event: log")


def test_session_file_commands(monkeypatch, tmp_path, capsys):
    list_command = MagicMock(
        return_value=[SerializableResult(name="input.txt")]
    )
    monkeypatch.setattr(agents, "list_session_files", list_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "list-session-files",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
        "--path",
        "/data",
        "--limit",
        "10",
        "--order",
        "asc",
        "--before",
        "entry-2",
    )
    list_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data",
        limit=10,
        order="asc",
        before="entry-2",
        allow_preview=False,
    )
    assert output == [{"name": "input.txt"}]

    source = tmp_path / "input.txt"
    source.write_bytes(b"input")
    upload_command = MagicMock(
        return_value=SerializableResult(path="/data/input.txt")
    )
    monkeypatch.setattr(agents, "upload_session_file", upload_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "upload-session-file",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
        "--source",
        str(source),
        "--path",
        "/data/input.txt",
    )
    upload_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        content=b"input",
        path="/data/input.txt",
        allow_preview=False,
    )
    assert output == {"path": "/data/input.txt"}

    destination = tmp_path / "output.txt"
    download_command = MagicMock(return_value=iter((b"out", b"put")))
    monkeypatch.setattr(agents, "download_session_file", download_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "download-session-file",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
        "--path",
        "/data/output.txt",
        "--output",
        str(destination),
    )
    download_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data/output.txt",
        allow_preview=False,
    )
    assert destination.read_bytes() == b"output"
    assert output["bytes"] == len(b"output")

    delete_command = MagicMock(return_value=None)
    monkeypatch.setattr(agents, "delete_session_file", delete_command)
    output = run_cli(
        monkeypatch,
        capsys,
        "delete-session-file",
        "--agent-name",
        "hosted-agent",
        "--session-id",
        "session-1",
        "--path",
        "/data",
        "--recursive",
    )
    delete_command.assert_called_once_with(
        agent_name="hosted-agent",
        session_id="session-1",
        path="/data",
        recursive=True,
        allow_preview=False,
    )
    assert output == {
        "session_id": "session-1",
        "path": "/data",
        "deleted": True,
    }


def test_optimization_job_wrappers(monkeypatch):
    client = mock_project_client(monkeypatch)
    job = models.OptimizationJob({"inputs": {}})

    optimization_result = SimpleNamespace(best="candidate-1", candidates=[])
    poller = MagicMock()
    poller.result.return_value = optimization_result
    client.beta.agents.begin_create_optimization_job.return_value = poller

    created = agents.begin_create_optimization_job(
        job,
        operation_id="operation-1",
        polling_interval=5,
    )

    assert created is optimization_result
    client.beta.agents.begin_create_optimization_job.assert_called_once_with(
        job=job,
        operation_id="operation-1",
        content_type="application/json",
        polling_interval=5,
    )
    poller.result.assert_called_once_with()

    retrieved_job = SimpleNamespace(id="job-1", status="in_progress")
    client.beta.agents.get_optimization_job.return_value = retrieved_job
    assert agents.get_optimization_job("job-1") is retrieved_job
    client.beta.agents.get_optimization_job.assert_called_once_with(job_id="job-1")

    listed_jobs = [SimpleNamespace(id="job-1", status="succeeded")]
    client.beta.agents.list_optimization_jobs.return_value = listed_jobs
    assert agents.list_optimization_jobs(
        limit=10,
        order="desc",
        before="job-2",
        status="succeeded",
        agent_name="weather-agent",
    ) == listed_jobs
    client.beta.agents.list_optimization_jobs.assert_called_once_with(
        limit=10,
        order="desc",
        before="job-2",
        status="succeeded",
        agent_name="weather-agent",
    )

    cancelled_job = SimpleNamespace(id="job-1", status="cancelled")
    client.beta.agents.cancel_optimization_job.return_value = cancelled_job
    assert agents.cancel_optimization_job("job-1") is cancelled_job
    client.beta.agents.cancel_optimization_job.assert_called_once_with(job_id="job-1")

    assert agents.delete_optimization_job("job-1") is None
    client.beta.agents.delete_optimization_job.assert_called_once_with(job_id="job-1")


def test_begin_create_optimization_job_command(monkeypatch, tmp_path, capsys):
    job_file = tmp_path / "optimization-job.json"
    job_file.write_text('{"inputs": {}}', encoding="utf-8")
    captured = {}

    def begin_create(**kwargs):
        captured.update(kwargs)
        return SerializableResult(best="candidate-1")

    monkeypatch.setattr(agents, "begin_create_optimization_job", begin_create)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agents",
            "--allow-preview",
            "begin-create-optimization-job",
            "--job-file",
            str(job_file),
            "--operation-id",
            "operation-1",
            "--polling-interval",
            "5",
        ],
    )

    agents.main()

    assert captured["job"].as_dict() == {"inputs": {}}
    assert captured["operation_id"] == "operation-1"
    assert captured["polling_interval"] == 5
    assert captured["allow_preview"] is True
    assert json.loads(capsys.readouterr().out) == {"best": "candidate-1"}


def test_get_optimization_job_command(monkeypatch, capsys):
    command = MagicMock(return_value=SerializableResult(id="job-1"))
    monkeypatch.setattr(agents, "get_optimization_job", command)
    monkeypatch.setattr(
        sys,
        "argv",
        ["agents", "get-optimization-job", "--job-id", "job-1"],
    )

    agents.main()

    command.assert_called_once_with(job_id="job-1", allow_preview=False)
    assert json.loads(capsys.readouterr().out) == {"id": "job-1"}


def test_list_optimization_jobs_command(monkeypatch, capsys):
    command = MagicMock(return_value=[SerializableResult(id="job-1")])
    monkeypatch.setattr(agents, "list_optimization_jobs", command)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agents",
            "list-optimization-jobs",
            "--limit",
            "10",
            "--order",
            "desc",
            "--before",
            "job-2",
            "--status",
            "succeeded",
            "--agent-name",
            "weather-agent",
        ],
    )

    agents.main()

    command.assert_called_once_with(
        limit=10,
        order="desc",
        before="job-2",
        status="succeeded",
        agent_name="weather-agent",
        allow_preview=False,
    )
    assert json.loads(capsys.readouterr().out) == [{"id": "job-1"}]


def test_cancel_optimization_job_command(monkeypatch, capsys):
    command = MagicMock(
        return_value=SerializableResult(id="job-1", status="cancelled")
    )
    monkeypatch.setattr(agents, "cancel_optimization_job", command)
    monkeypatch.setattr(
        sys,
        "argv",
        ["agents", "cancel-optimization-job", "--job-id", "job-1"],
    )

    agents.main()

    command.assert_called_once_with(job_id="job-1", allow_preview=False)
    assert json.loads(capsys.readouterr().out) == {
        "id": "job-1",
        "status": "cancelled",
    }


def test_delete_optimization_job_command(monkeypatch, capsys):
    command = MagicMock(return_value=None)
    monkeypatch.setattr(agents, "delete_optimization_job", command)
    monkeypatch.setattr(
        sys,
        "argv",
        ["agents", "delete-optimization-job", "--job-id", "job-1"],
    )

    agents.main()

    command.assert_called_once_with(job_id="job-1", allow_preview=False)
    assert json.loads(capsys.readouterr().out) == {
        "job_id": "job-1",
        "deleted": True,
    }