// Cosmopilot — subscription-scoped entry point for `azd up`.
// Creates the resource group and deploys the Cosmos DB + Azure AI Foundry demo
// infrastructure (see resources.bicep) into it.
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the azd environment. Used to name the resource group (rg-<name>) and to derive a unique resource token.')
param environmentName string

@allowed([
  'eastus2'
])
@description('Primary location for all resources except Azure AI Search. Locked to East US 2 — the only region with every required model deployment and the full Foundry evaluation suite.')
param location string

@minLength(1)
@description('Region for the Azure AI Search service only. Prompted during `azd up`; can differ from the primary region since Search is reached over a global *.search.windows.net endpoint. Pick another region if East US 2 is out of Search capacity.')
@metadata({
  azd: {
    type: 'location'
  }
})
param searchLocation string

// Deterministic, globally-unique token derived from the subscription + env + region.
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  scope: rg
  name: 'cosmopilot-resources'
  params: {
    environmentName: environmentName
    location: location
    searchLocation: searchLocation
    resourceToken: resourceToken
  }
}

// ===== azd-standard outputs =====
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name

// ===== Application environment outputs (captured into .azure/<env>/.env) =====
// Azure AI Foundry
output AZURE_AI_PROJECT_ENDPOINT string = resources.outputs.foundryProjectEndpoint
output AZURE_AI_PROJECT_NAME string = resources.outputs.foundryProjectName
output AZURE_AI_FOUNDRY_RESOURCE_NAME string = resources.outputs.foundryResourceName
output AZURE_DEPLOYMENT_NAME string = resources.outputs.modelDeploymentName
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT string = resources.outputs.embeddingDeploymentName

// Azure Cosmos DB
output COSMOS_DB_ENDPOINT string = resources.outputs.cosmosAccountEndpoint
output COSMOS_DB_DATABASE string = resources.outputs.sqlDatabaseName
output COSMOS_DB_CONTAINER string = resources.outputs.containerName

// Azure AI Search
output AZURE_AI_SEARCH_ENDPOINT string = resources.outputs.searchServiceEndpoint
output AZURE_AI_SEARCH_CONNECTION_ID string = resources.outputs.searchConnectionId
output AZURE_AI_SEARCH_INDEX_NAME string = resources.outputs.searchIndexName

// Grounding with Bing Search
output AZURE_BING_CONNECTION_ID string = resources.outputs.bingConnectionId

// Observability
output AZURE_APPLICATION_INSIGHTS_NAME string = resources.outputs.appInsightsName
