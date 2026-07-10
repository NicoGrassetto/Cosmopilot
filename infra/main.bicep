// Cosmopilot Infrastructure: Cosmos DB + Azure AI Foundry Project

// ===== Cosmos DB Parameters =====
@description('A short name for the environment, such as dev, test, or prod. This helps you keep deployments organized.')
param environmentName string

@description('The Azure region where resources will be deployed. Locked to East US 2: it is the only region where every deployed model (model-router 2025-11-18, gpt-4.1, Phi-4-mini-reasoning) AND every Foundry feature the project uses is available — including the full evaluation suite (risk & safety evaluators, Groundedness Pro, and Protected Material, which is East US 2-only).')
@allowed([
  'eastus2'
])
param location string

@description('The Cosmos DB account name. It must be globally unique across Azure and use only lowercase letters, numbers, and hyphens.')
param cosmosAccountName string

@description('The SQL database name inside the Cosmos DB account. This is like a logical database for your app data.')
param sqlDatabaseName string

@description('The container name inside the SQL database. This is where your items will be stored.')
param containerName string

@description('The partition key path for the container. This is the field Cosmos DB uses to spread data across partitions. Example: /tenantId')
param partitionKeyPath string = '/tenantId'

@description('The throughput for the container in request units per second (RU/s). A small value like 400 is fine for development.')
param throughput int = 400

@description('The consistency level for the account. Session is a good default for most apps.')
@allowed([
  'BoundedStaleness'
  'ConsistentPrefix'
  'Session'
  'Strong'
  'Eventual'
])
param consistencyLevel string = 'Session'

// ===== Foundry Project Parameters =====
@description('Foundry Project name - must be globally unique')
param projectName string

@description('Project public network access')
param publicNetworkAccess string = 'Enabled'

@description('Enable data isolation for the project')
param enableDataIsolation bool = false

// ===== Bing Grounding Parameters =====
@description('Name for the Grounding with Bing Search account. Must be unique within the resource group.')
param bingAccountName string = 'bing-grounding'

// ===== Azure AI Search Parameters =====
@description('Name for the Azure AI Search service. Must be globally unique, 2-60 chars, lowercase letters, digits, and hyphens (no leading/trailing hyphen).')
param searchServiceName string = 'cosmopilot-search'

@description('Azure AI Search SKU. Basic is a good default for a demo; free allows only one per subscription.')
@allowed([
  'free'
  'basic'
  'standard'
])
param searchServiceSku string = 'basic'

@description('Name of the search index that the knowledge-assistant queries.')
param searchIndexName string = 'knowledge-docs'

@description('Region for the Azure AI Search service. Defaults to the main location; override if that region is out of Search capacity.')
param searchLocation string = location

// ===== Variables =====
var uniqueSuffix = uniqueString(resourceGroup().id)
var projectFullName = '${projectName}-${uniqueSuffix}'
var demoEnvironment = 'demo'
var modelDeploymentName = 'gpt-4-1-nano'
var modelType = 'gpt-4.1-nano'
var embeddingDeploymentName = 'text-embedding-ada-002'
var embeddingModelType = 'text-embedding-ada-002'
// Azure AI Search service name must be globally unique; append the suffix.
var searchFullName = '${searchServiceName}-${uniqueSuffix}'

// Additional Foundry model deployments (see docs/tools-roadmap.md).
// model-router: single OpenAI deployment that routes to the best underlying model.
var modelRouterDeploymentName = 'model-router'
var modelRouterModelType = 'model-router'
var modelRouterModelVersion = '2025-11-18'
// gpt-4.1: full GPT-4.1 chat model.
var gpt41DeploymentName = 'gpt-4.1'
var gpt41ModelType = 'gpt-4.1'
var gpt41ModelVersion = '2025-04-14'
// Phi-4-mini-reasoning: small Microsoft reasoning model (Microsoft format).
var phiMiniReasoningDeploymentName = 'Phi-4-mini-reasoning'
var phiMiniReasoningModelType = 'Phi-4-mini-reasoning'
var phiMiniReasoningModelVersion = '1'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  tags: {
    environment: environmentName
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: false
    consistencyPolicy: {
      defaultConsistencyLevel: consistencyLevel
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    publicNetworkAccess: 'enabled'
    enableAutomaticFailover: false
  }
}

resource sqlDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: sqlDatabaseName
  properties: {
    resource: {
      id: sqlDatabaseName
    }
  }
}

resource containerResource 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: sqlDatabase
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: [
          partitionKeyPath
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent' // you can also have lazy for analytics and lower latency but index updates after write completes
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
      }
    }
    options: {
      throughput: throughput
    }
  }
}

// ===== Foundry Resource (AI Services account) =====
resource foundryResource 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: projectFullName
  location: location
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: projectFullName
    publicNetworkAccess: publicNetworkAccess
  }
  tags: {
    environment: demoEnvironment
  }
}

// ===== Foundry Project (hub-less, new experience) =====
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundryResource
  name: projectFullName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

// ===== Model Deployments =====
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryResource
  name: modelDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelType
    }
  }
  dependsOn: [
    foundryProject
  ]
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryResource
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelType
    }
  }
  // Serialize model deployments: a Cognitive Services account only allows one
  // deployment operation at a time, so wait for the chat model deployment.
  dependsOn: [
    modelDeployment
  ]
}

// model-router — one OpenAI deployment that dynamically routes each prompt to
// the best underlying model. No need to deploy the routed models separately.
resource modelRouterDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryResource
  name: modelRouterDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelRouterModelType
      version: modelRouterModelVersion
    }
  }
  dependsOn: [
    embeddingDeployment
  ]
}

// gpt-4.1 — full GPT-4.1 chat model.
resource gpt41Deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryResource
  name: gpt41DeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: gpt41ModelType
      version: gpt41ModelVersion
    }
  }
  dependsOn: [
    modelRouterDeployment
  ]
}

// Phi-4-mini-reasoning — small Microsoft reasoning model.
resource phiMiniReasoningDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundryResource
  name: phiMiniReasoningDeploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: 1
  }
  properties: {
    model: {
      format: 'Microsoft'
      name: phiMiniReasoningModelType
      version: phiMiniReasoningModelVersion
    }
  }
  dependsOn: [
    gpt41Deployment
  ]
}

// ===== Grounding with Bing Search =====
// Bing account (global) that backs the research-assistant's bing_grounding tool.
// SKU G1 / kind Bing.Grounding is the required combination for Foundry grounding.
resource bingAccount 'Microsoft.Bing/accounts@2025-05-01-preview' = {
  name: bingAccountName
  location: 'global'
  kind: 'Bing.Grounding'
  sku: {
    name: 'G1'
  }
  tags: {
    environment: demoEnvironment
  }
  properties: {}
}

// Foundry connection exposing the Bing account to the project. The agent references
// this connection's id via the BING_CONNECTION_ID env var when registering. It must
// be a project-scoped connection so the grounding tool can resolve it.
resource bingConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: foundryProject
  name: 'binggrounding'
  properties: {
    category: 'GroundingWithBingSearch'
    target: 'https://api.bing.microsoft.com/'
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: listKeys(bingAccount.id, '2025-05-01-preview').key1
    }
    metadata: {
      Type: 'bing_grounding'
      ApiType: 'Azure'
      ResourceId: bingAccount.id
    }
  }
}

// ===== Azure AI Search =====
// Search service that backs the knowledge-assistant's azure_ai_search tool.
resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchFullName
  location: searchLocation
  sku: {
    name: searchServiceSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    // Allow both API-key and Azure AD auth so the Foundry connection (key-based)
    // and local provisioning (AAD) both work.
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
  tags: {
    environment: demoEnvironment
  }
}

// Project-scoped connection exposing the search service to the Foundry project.
// The knowledge-assistant references this connection id (SEARCH_CONNECTION_ID)
// when attaching its azure_ai_search tool to an index.
resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: foundryProject
  name: 'aisearch'
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchService.name}.search.windows.net'
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: listAdminKeys(searchService.id, '2024-06-01-preview').primaryKey
    }
    metadata: {
      Type: 'azure_ai_search'
      ApiType: 'Azure'
      ResourceId: searchService.id
      ApiVersion: '2024-07-01'
    }
  }
}

// ===== Outputs =====
// Cosmos DB outputs
output cosmosAccountName string = cosmosAccount.name
output cosmosAccountEndpoint string = cosmosAccount.properties.documentEndpoint
output sqlDatabaseName string = sqlDatabase.name
output containerName string = containerResource.name

// Foundry Project outputs
output foundryResourceName string = foundryResource.name
output foundryResourceId string = foundryResource.id
output foundryProjectName string = foundryProject.name
output foundryProjectId string = foundryProject.id
output foundryProjectEndpoint string = 'https://${projectFullName}.services.ai.azure.com/api/projects/${projectFullName}'
output modelDeploymentName string = modelDeploymentName
output modelDeploymentId string = modelDeployment.id
output modelType string = modelType
output embeddingDeploymentName string = embeddingDeploymentName
output embeddingDeploymentId string = embeddingDeployment.id
output embeddingModelType string = embeddingModelType

// Additional model deployments
output modelRouterDeploymentName string = modelRouterDeployment.name
output modelRouterDeploymentId string = modelRouterDeployment.id
output modelRouterModelType string = modelRouterModelType
output gpt41DeploymentName string = gpt41Deployment.name
output gpt41DeploymentId string = gpt41Deployment.id
output gpt41ModelType string = gpt41ModelType
output phiMiniReasoningDeploymentName string = phiMiniReasoningDeployment.name
output phiMiniReasoningDeploymentId string = phiMiniReasoningDeployment.id
output phiMiniReasoningModelType string = phiMiniReasoningModelType

// Bing Grounding outputs (used to register the research-assistant agent)
output bingAccountName string = bingAccount.name
output bingConnectionName string = bingConnection.name
output bingConnectionId string = bingConnection.id

// Azure AI Search outputs (used to provision the index and register the knowledge-assistant)
output searchServiceName string = searchService.name
output searchServiceEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchConnectionName string = searchConnection.name
output searchConnectionId string = searchConnection.id
output searchIndexName string = searchIndexName
