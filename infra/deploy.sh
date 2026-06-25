#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/main.bicep"
PARAMS_FILE="$SCRIPT_DIR/main.parameters.json"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required but was not found in PATH." >&2
  exit 1
fi

prompt_value() {
  local var_name="$1"
  local prompt_text="$2"
  local explanation="$3"
  local default_value="${4:-}"
  local value=""

  echo
  echo "$explanation"
  if [[ -n "$default_value" ]]; then
    read -r -p "$prompt_text [$default_value]: " value
    value="${value:-$default_value}"
  else
    read -r -p "$prompt_text: " value
  fi

  printf -v "$var_name" '%s' "$value"
}

prompt_bool() {
  local var_name="$1"
  local prompt_text="$2"
  local explanation="$3"
  local default_value="${4:-false}"
  local value=""

  echo
  echo "$explanation"
  while true; do
    if [[ "$default_value" == "true" ]]; then
      read -r -p "$prompt_text [Y/n]: " value
      value="${value:-Y}"
    else
      read -r -p "$prompt_text [y/N]: " value
      value="${value:-N}"
    fi
    case "${value,,}" in
      y|yes) value="true"; break ;;
      n|no) value="false"; break ;;
      "") value="$default_value"; break ;;
      *) echo "Please answer yes or no." ;;
    esac
  done

  printf -v "$var_name" '%s' "$value"
}

prompt_value "resourceGroupName" "Resource group name" "This is the Azure container that holds your resources. Think of it like a folder for related cloud stuff." ""
prompt_value "environmentName" "Environment name" "A short name for the environment (e.g., demo, dev, prod). Used for tagging and organization." "demo"
prompt_value "location" "Azure region" "Choose from: eastus, eastus2, westeurope, uksouth, swedencentral. This is where Cosmos DB and Foundry will be created." "eastus"
prompt_value "cosmosAccountName" "Cosmos DB account name" "Must be globally unique. Use lowercase letters, numbers, and hyphens only." "cosmopilot-db"
prompt_value "sqlDatabaseName" "SQL database name" "Logical database inside Cosmos DB that groups containers and items." "cosmopilot"
prompt_value "containerName" "Container name" "Container where your documents/items will be stored (like a table)." "conversations"
prompt_value "partitionKeyPath" "Partition key path" "Field Cosmos DB uses to split data across partitions. Example: /tenantId or /conversationId" "/tenantId"
prompt_value "throughput" "Container throughput (RU/s)" "Performance level for the container. 400 is good for development, scale up for production." "400"
prompt_value "consistencyLevel" "Consistency level" "How strongly reads and writes are synchronized. Options: Eventual, ConsistentPrefix, Session (default), BoundedStaleness, Strong" "Session"
prompt_value "projectName" "Foundry Project name" "Name for the AI Foundry Project. Suffix with unique ID is added automatically." "cosmopilot"
prompt_value "publicNetworkAccess" "Public network access" "Enabled for internet access, Disabled for private-only (requires VNet integration)." "Enabled"
prompt_bool "enableDataIsolation" "Enable data isolation?" "If true, isolates project resources in a private VNet with private endpoints. Recommended for regulated industries, not needed for dev." "false"

cat > "$PARAMS_FILE" <<EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "value": "$environmentName"
    },
    "location": {
      "value": "$location"
    },
    "cosmosAccountName": {
      "value": "$cosmosAccountName"
    },
    "sqlDatabaseName": {
      "value": "$sqlDatabaseName"
    },
    "containerName": {
      "value": "$containerName"
    },
    "partitionKeyPath": {
      "value": "$partitionKeyPath"
    },
    "throughput": {
      "value": $throughput
    },
    "consistencyLevel": {
      "value": "$consistencyLevel"
    },
    "projectName": {
      "value": "$projectName"
    },
    "publicNetworkAccess": {
      "value": "$publicNetworkAccess"
    },
    "enableDataIsolation": {
      "value": $enableDataIsolation
    }
  }
}
EOF

echo
echo "✅ Deployment parameters written to $PARAMS_FILE"
echo
echo "Next step: Create the resource group (if needed), then deploy:"
echo "  az group create --name '$resourceGroupName' --location '$location'"
echo "  az deployment group create --resource-group '$resourceGroupName' --template-file '$TEMPLATE_FILE' --parameters '@$PARAMS_FILE'"
