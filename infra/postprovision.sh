#!/usr/bin/env bash
# Post-provision hook for the research-assistant and knowledge-assistant agents.
#
# Reads outputs from the main deployment, then:
#   * creates a demo vector store (research-assistant file_search),
#   * creates the Azure AI Search index and loads data/documents (knowledge-assistant),
#   * creates the Foundry memory store (knowledge-assistant memory_search),
# and prints the env vars needed to register the agents.
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
SEARCH_INDEX_PY="$REPO_ROOT/src/agents/knowledge-assistant/provision_search_index.py"
MEMORY_STORE_PY="$REPO_ROOT/src/agents/knowledge-assistant/provision_memory_store.py"

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
SEARCH_SERVICE_NAME="$(get_output searchServiceName)"
SEARCH_SERVICE_ENDPOINT="$(get_output searchServiceEndpoint)"
SEARCH_CONNECTION_ID="$(get_output searchConnectionId)"
SEARCH_INDEX_NAME="$(get_output searchIndexName)"

export AZURE_AI_PROJECT_ENDPOINT
echo "Project endpoint: $AZURE_AI_PROJECT_ENDPOINT"
echo "Bing connection id: $BING_CONNECTION_ID"
echo "Search service: $SEARCH_SERVICE_NAME ($SEARCH_SERVICE_ENDPOINT)"
echo "Search connection id: $SEARCH_CONNECTION_ID"

echo "Creating demo vector store and uploading fake documents..."
VECTOR_STORE_LINE="$(python3 "$PROVISION_PY" | tail -n 1)"
FILE_SEARCH_VECTOR_STORE_ID="${VECTOR_STORE_LINE#FILE_SEARCH_VECTOR_STORE_ID=}"

echo "Creating Azure AI Search index and loading data/documents..."
SEARCH_ADMIN_KEY="$(az search admin-key show \
  --resource-group "$RESOURCE_GROUP" \
  --service-name "$SEARCH_SERVICE_NAME" \
  --query primaryKey -o tsv)"
SEARCH_INDEX_LINE="$(SEARCH_SERVICE_ENDPOINT="$SEARCH_SERVICE_ENDPOINT" \
  SEARCH_INDEX_NAME="$SEARCH_INDEX_NAME" \
  SEARCH_ADMIN_KEY="$SEARCH_ADMIN_KEY" \
  python3 "$SEARCH_INDEX_PY" | tail -n 1)"
SEARCH_INDEX_NAME="${SEARCH_INDEX_LINE#SEARCH_INDEX_NAME=}"

echo "Creating Foundry memory store..."
MEMORY_STORE_LINE="$(python3 "$MEMORY_STORE_PY" | tail -n 1)"
MEMORY_STORE_NAME="${MEMORY_STORE_LINE#MEMORY_STORE_NAME=}"

echo
echo "✅ Post-provision complete. Export these before registering the agents:"
echo "  export AZURE_AI_PROJECT_ENDPOINT='$AZURE_AI_PROJECT_ENDPOINT'"
echo "  export AZURE_DEPLOYMENT_NAME='gpt-4-1-nano'"
echo "  # research-assistant"
echo "  export BING_CONNECTION_ID='$BING_CONNECTION_ID'"
echo "  export FILE_SEARCH_VECTOR_STORE_ID='$FILE_SEARCH_VECTOR_STORE_ID'"
echo "  # knowledge-assistant"
echo "  export SEARCH_CONNECTION_ID='$SEARCH_CONNECTION_ID'"
echo "  export SEARCH_INDEX_NAME='$SEARCH_INDEX_NAME'"
echo "  export MEMORY_STORE_NAME='$MEMORY_STORE_NAME'"
