#!/usr/bin/env bash
# Post-provision hook for the research-assistant agent.
#
# Reads outputs from the main deployment, creates a demo vector store (via
# provision_vector_store.py), and prints the env vars needed to register the agent:
#   AZURE_AI_PROJECT_ENDPOINT, BING_CONNECTION_ID, FILE_SEARCH_VECTOR_STORE_ID
#
# Usage:
#   ./infra/postprovision.sh <resourceGroupName> [deploymentName]
#
# Requires: az CLI (logged in) and python3 with the repo requirements installed.
set -euo pipefail

RESOURCE_GROUP="${1:?resource group name is required}"
DEPLOYMENT_NAME="${2:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROVISION_PY="$REPO_ROOT/src/agents/research-assistant/provision_vector_store.py"

echo "Reading outputs from deployment '$DEPLOYMENT_NAME' in resource group '$RESOURCE_GROUP'..."
OUTPUTS_JSON="$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --query properties.outputs -o json)"

get_output() {
  echo "$OUTPUTS_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['$1']['value'])"
}

AZURE_AI_PROJECT_ENDPOINT="$(get_output foundryProjectEndpoint)"
BING_CONNECTION_ID="$(get_output bingConnectionId)"

export AZURE_AI_PROJECT_ENDPOINT
echo "Project endpoint: $AZURE_AI_PROJECT_ENDPOINT"
echo "Bing connection id: $BING_CONNECTION_ID"

echo "Creating demo vector store and uploading fake documents..."
VECTOR_STORE_LINE="$(python3 "$PROVISION_PY" | tail -n 1)"
FILE_SEARCH_VECTOR_STORE_ID="${VECTOR_STORE_LINE#FILE_SEARCH_VECTOR_STORE_ID=}"

echo
echo "✅ Post-provision complete. Export these before registering the agent:"
echo "  export AZURE_AI_PROJECT_ENDPOINT='$AZURE_AI_PROJECT_ENDPOINT'"
echo "  export BING_CONNECTION_ID='$BING_CONNECTION_ID'"
echo "  export FILE_SEARCH_VECTOR_STORE_ID='$FILE_SEARCH_VECTOR_STORE_ID'"
echo "  export AZURE_DEPLOYMENT_NAME='gpt-4-1-nano'"
