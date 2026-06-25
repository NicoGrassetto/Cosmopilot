# Cosmopilot Infrastructure Deployment Script for Windows
# This script prompts for configuration and generates deployment parameters

param(
    [switch]$NonInteractive = $false
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"

# Check if Azure CLI is installed
Write-Host "Checking for Azure CLI..." -ForegroundColor $InfoColor
$azCliExists = $null
try {
    $azCliVersion = az --version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Azure CLI found: $azCliVersion" -ForegroundColor $SuccessColor
    } else {
        throw "Azure CLI not found"
    }
} catch {
    Write-Host "✗ Azure CLI is required but was not found." -ForegroundColor $ErrorColor
    Write-Host "Download from: https://aka.ms/azure-cli" -ForegroundColor $InfoColor
    exit 1
}

# Function to prompt for values
function Prompt-Value {
    param(
        [string]$PromptText,
        [string]$Explanation,
        [string]$DefaultValue = ""
    )
    
    Write-Host ""
    Write-Host $Explanation -ForegroundColor $InfoColor
    
    if ($DefaultValue) {
        $userInput = Read-Host "$PromptText [$DefaultValue]"
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            return $DefaultValue
        }
        return $userInput
    } else {
        $userInput = Read-Host $PromptText
        while ([string]::IsNullOrWhiteSpace($userInput)) {
            Write-Host "This field is required." -ForegroundColor $ErrorColor
            $userInput = Read-Host $PromptText
        }
        return $userInput
    }
}

# Function to prompt for boolean values
function Prompt-Boolean {
    param(
        [string]$PromptText,
        [string]$Explanation,
        [bool]$DefaultValue = $false
    )
    
    Write-Host ""
    Write-Host $Explanation -ForegroundColor $InfoColor
    
    $defaultStr = if ($DefaultValue) { "Y/n" } else { "y/N" }
    
    while ($true) {
        $userInput = Read-Host "$PromptText [$defaultStr]"
        
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            return $DefaultValue
        }
        
        $lower = $userInput.ToLower()
        if ($lower -eq "y" -or $lower -eq "yes") {
            return $true
        } elseif ($lower -eq "n" -or $lower -eq "no") {
            return $false
        } else {
            Write-Host "Please answer yes or no." -ForegroundColor $ErrorColor
        }
    }
}

# Prompt for configuration values
$resourceGroupName = Prompt-Value `
    -PromptText "Resource group name" `
    -Explanation "This is the Azure container that holds your resources. Think of it like a folder for related cloud stuff."

$environmentName = Prompt-Value `
    -PromptText "Environment name" `
    -Explanation "A short name for the environment (e.g., demo, dev, prod). Used for tagging and organization." `
    -DefaultValue "demo"

$location = Prompt-Value `
    -PromptText "Azure region" `
    -Explanation "Choose from: eastus, eastus2, westeurope, uksouth, swedencentral. This is where Cosmos DB and Foundry will be created." `
    -DefaultValue "swedencentral"

$cosmosAccountName = Prompt-Value `
    -PromptText "Cosmos DB account name" `
    -Explanation "Must be globally unique. Use lowercase letters, numbers, and hyphens only." `
    -DefaultValue "cosmopilot-db"

$sqlDatabaseName = Prompt-Value `
    -PromptText "SQL database name" `
    -Explanation "Logical database inside Cosmos DB that groups containers and items." `
    -DefaultValue "cosmopilot"

$containerName = Prompt-Value `
    -PromptText "Container name" `
    -Explanation "Container where your documents/items will be stored (like a table)." `
    -DefaultValue "conversations"

$partitionKeyPath = Prompt-Value `
    -PromptText "Partition key path" `
    -Explanation "Field Cosmos DB uses to split data across partitions. Example: /tenantId or /conversationId" `
    -DefaultValue "/tenantId"

$throughput = Prompt-Value `
    -PromptText "Container throughput (RU/s)" `
    -Explanation "Performance level for the container. 400 is good for development, scale up for production." `
    -DefaultValue "400"

$consistencyLevel = Prompt-Value `
    -PromptText "Consistency level" `
    -Explanation "How strongly reads and writes are synchronized. Options: Eventual, ConsistentPrefix, Session (default), BoundedStaleness, Strong" `
    -DefaultValue "Session"

$projectName = Prompt-Value `
    -PromptText "Foundry Project name" `
    -Explanation "Name for the AI Foundry Project. Suffix with unique ID is added automatically." `
    -DefaultValue "cosmopilot"

$publicNetworkAccess = Prompt-Value `
    -PromptText "Public network access" `
    -Explanation "Enabled for internet access, Disabled for private-only (requires VNet integration)." `
    -DefaultValue "Enabled"

$enableDataIsolation = Prompt-Boolean `
    -PromptText "Enable data isolation?" `
    -Explanation "If true, isolates project resources in a private VNet with private endpoints. Recommended for regulated industries, not needed for dev." `
    -DefaultValue $false

# Convert boolean to lowercase string for JSON
$enableDataIsolationJson = if ($enableDataIsolation) { "true" } else { "false" }

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$paramsFile = Join-Path $scriptDir "main.parameters.json"
$templateFile = Join-Path $scriptDir "main.bicep"

# Create parameters JSON
$parametersJson = @{
    "`$schema" = "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#"
    "contentVersion" = "1.0.0.0"
    "parameters" = @{
        "environmentName" = @{ "value" = $environmentName }
        "location" = @{ "value" = $location }
        "cosmosAccountName" = @{ "value" = $cosmosAccountName }
        "sqlDatabaseName" = @{ "value" = $sqlDatabaseName }
        "containerName" = @{ "value" = $containerName }
        "partitionKeyPath" = @{ "value" = $partitionKeyPath }
        "throughput" = @{ "value" = [int]$throughput }
        "consistencyLevel" = @{ "value" = $consistencyLevel }
        "projectName" = @{ "value" = $projectName }
        "publicNetworkAccess" = @{ "value" = $publicNetworkAccess }
        "enableDataIsolation" = @{ "value" = [bool]$enableDataIsolation }
    }
} | ConvertTo-Json -Depth 10

# Write parameters to file
Set-Content -Path $paramsFile -Value $parametersJson -Encoding UTF8

Write-Host ""
Write-Host "✅ Deployment parameters written to $paramsFile" -ForegroundColor $SuccessColor
Write-Host ""
Write-Host "Next step: Create the resource group (if needed), then deploy:" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "  az group create --name '$resourceGroupName' --location '$location'"
Write-Host "  az deployment group create --resource-group '$resourceGroupName' --template-file '$templateFile' --parameters '@$paramsFile'"
Write-Host ""
