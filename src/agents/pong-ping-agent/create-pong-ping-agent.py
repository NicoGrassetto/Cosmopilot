import os
import time
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

from memory_storage import ensure_agent_memory_store

name = "pong-ping-hosted-agent"
endpoint = os.environ["AZURE_AI_PROJECT_ENDPOINT"]

# ------- Memory store--------
memory_scope = os.environ["AGENT_MEMORY_SCOPE"]
if not memory_scope.strip():
    raise ValueError("AGENT_MEMORY_SCOPE must be a non-empty trusted scope.")
memory_store = ensure_agent_memory_store(name)
# --------

with DefaultAzureCredential() as credential, AIProjectClient(endpoint, credential, allow_preview=True) as client:
    definition = models.HostedAgentDefinition(
        cpu="0.5", memory="1Gi",
        code_configuration=models.CodeConfiguration(
            runtime="python_3_14", entry_point=["python", "main.py"],
            dependency_resolution=models.CodeDependencyResolution.REMOTE_BUILD),
        environment_variables={
            "AZURE_AI_PROJECT_ENDPOINT": endpoint,
            "AZURE_DEPLOYMENT_NAME": os.environ["AZURE_DEPLOYMENT_NAME"],
            "AGENT_MEMORY_STORE_NAME": memory_store.name,
            "AGENT_MEMORY_SCOPE": memory_scope},
        protocol_versions=[models.ProtocolVersionRecord(protocol="responses", version="2.0.0")])

    agent_dir = Path(__file__).resolve().parent
    with BytesIO() as code:
        with ZipFile(code, "w") as archive:
            archive.write(agent_dir / "main.py", "main.py")
            archive.write(agent_dir.parents[2] / "requirements.txt", "requirements.txt")
        code.seek(0)
        created = client.agents.create_version_from_code(agent_name=name, definition=definition, code=code)

    for attempt in range(60):
        status = client.agents.get_version(agent_name=name, agent_version=created.version)["status"]
        if status == "active":
            break
        if status == "failed":
            raise RuntimeError("Hosted-agent provisioning failed")
        time.sleep(10)
    else:
        raise TimeoutError("Agent did not become active")
    client.agents.update_details(name, agent_endpoint=models.AgentEndpointConfig(
        version_selector=models.VersionSelector(version_selection_rules=[
            models.FixedRatioVersionSelectionRule(agent_version=created.version, traffic_percentage=100)]),
        protocol_configuration=models.ProtocolConfiguration(responses=models.ResponsesProtocolConfiguration())))

    with client.get_openai_client(agent_name=name) as openai:
        print(openai.responses.create(input="ping").output_text)