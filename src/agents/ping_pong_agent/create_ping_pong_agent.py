import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from azure.ai.projects import AIProjectClient, models
from azure.identity import DefaultAzureCredential

AGENT_DIR = Path(__file__).resolve().parent


def main() -> None:
    with TemporaryDirectory() as directory:
        package_path = Path(directory) / "ping-pong-agent.zip"

        with ZipFile(package_path, "w") as archive:
            for filename in ("main.py", "agent.yaml", "requirements.txt"):
                archive.write(AGENT_DIR / filename, arcname=filename)

        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(
                endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
                credential=credential,
                allow_preview=True,
            ) as client,
            package_path.open("rb") as code,
        ):
            version = client.agents.create_version_from_code(
                agent_name="ping-pong-agent",
                definition=models.HostedAgentDefinition(
                    cpu="0.5",
                    memory="1Gi",
                    code_configuration=models.CodeConfiguration(
                        runtime="python_3_13",
                        entry_point=["python", "main.py"],
                        dependency_resolution="remote_build",
                    ),
                    protocol_versions=[
                        models.ProtocolVersionRecord(
                            protocol="responses",
                            version="1.0.0",
                        )
                    ],
                ),
                code=code,
            )
            print(f"{version.name}: version={version.version}, status={version.status}")


if __name__ == "__main__":
    main()