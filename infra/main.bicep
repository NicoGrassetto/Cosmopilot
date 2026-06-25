// Cosmopilot Infrastructure: Cosmos DB + Azure AI Foundry Project

// ===== Cosmos DB Parameters =====
@description('A short name for the environment, such as dev, test, or prod. This helps you keep deployments organized.')
param environmentName string

@description('The Azure region where resources will be deployed.')
@allowed([
  'eastus'
  'eastus2'
  'westeurope'
  'uksouth'
  'swedencentral'
])
param location string = resourceGroup().location

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

// ===== Variables =====
var uniqueSuffix = uniqueString(resourceGroup().id)
var projectFullName = '${projectName}-${uniqueSuffix}'
var demoEnvironment = 'demo'
var modelDeploymentName = 'gpt-4o-nano'
var modelType = 'gpt-4o-nano'
var embeddingDeploymentName = 'text-embedding-3-nano'
var embeddingModelType = 'text-embedding-3-nano'

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

// ===== Foundry Project (standalone, auto-manages infrastructure) =====
resource foundryProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01-preview' = {
  name: projectFullName
  location: location
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: projectFullName
    description: 'Cosmopilot AI Foundry Project'
    publicNetworkAccess: publicNetworkAccess
    enableDataIsolation: enableDataIsolation
  }
  tags: {
    environment: demoEnvironment
  }
}

// ===== Outputs =====
// Cosmos DB outputs
output cosmosAccountName string = cosmosAccount.name
output cosmosAccountEndpoint string = cosmosAccount.properties.documentEndpoint
output sqlDatabaseName string = sqlDatabase.name
output containerName string = containerResource.name

// Foundry Project outputs
output projectName string = foundryProject.name
output projectId string = foundryProject.id
output projectWorkspaceId string = foundryProject.properties.workspaceId
output modelDeploymentName string = modelDeploymentName
output modelType string = modelType
output embeddingDeploymentName string = embeddingDeploymentName
output embeddingModelType string = embeddingModelType
