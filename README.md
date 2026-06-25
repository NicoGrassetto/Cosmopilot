<h1 align="center">🤖 Cosmopilot</h1>

<p align="center">
  <img src="assets/banner.png" alt="Cosmopilot Banner" width="60%" />
</p>

<p align="center">AI-powered chatbot with real-time operational data and voice capabilities.</p>

<p align="center">
  <a href="LICENSE"><img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-2ea44f" /></a>
  <a href="LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-2ea44f" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot/codespaces"><img alt="Open in Codespaces" src="https://img.shields.io/badge/Open%20in-Codespaces-fb8c00?logo=github" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NicoGrassetto/Cosmopilot" /></a>
</p>

Cosmopilot is a demo showcasing Microsoft Foundry as an AI platform, combined with a unified database using Cosmos DB to store both vectors and operational data. It's optimized for speed and real-time data feed/refresh, featuring a lightweight frontend built with Svelte and real-time message synchronization via Cosmos DB change feeds.

---

## 🚀 Getting Started: Deploying to Azure

This guide walks you through deploying Cosmopilot to Azure. The deployment creates two main components:
- **Azure Cosmos DB**: Multi-model database for storing conversations, vectors, and operational data
- **Azure AI Foundry Project**: Managed AI infrastructure for running language models and embeddings

### Prerequisites

Before you begin, ensure you have the following installed and configured:

#### 1. **Azure CLI**
The Azure Command Line Interface is required to deploy resources to Azure.

**Installation:**
- **macOS**: `brew install azure-cli`
- **Windows**: Download from [Azure CLI releases](https://github.com/Azure/azure-cli/releases) or use `winget install Microsoft.AzureCLI`
- **Linux**: See [official installation guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux)

**Verify installation:**
```bash
az --version
```

#### 2. **Platform-Specific Requirements**

**macOS/Linux:**
- Bash 3.2 or higher (usually pre-installed)
- Run deployment with `bash deploy.sh`

**Windows:**
- PowerShell 5.1 or higher (included with Windows 10+)
- If using older PowerShell, you may need to enable script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Run deployment with `.\deploy.ps1` from PowerShell

#### 3. **Azure Account & Subscription**
- Create a free Azure account at [azure.microsoft.com](https://azure.microsoft.com)
- You'll receive $200 free credits for 30 days
- Note your subscription ID for the deployment

**Verify access:**
```bash
az login
az account show
```

#### 3. **Required Permissions**
You need permissions to create the following resources:
- Cosmos DB account and containers
- AI Foundry project and resources
- Resource groups

**Most Azure accounts have sufficient permissions by default.** If you encounter permission errors during deployment, contact your Azure administrator.

#### 4. **Required Information**
Gather the following before running the deployment:
- **Azure Region**: Where your resources will be deployed (examples: `eastus`, `westeurope`, `swedencentral`)
- **Resource Group Name**: A container name for all your resources (example: `cosmopilot-rg`)
- **Cosmos DB Account Name**: Must be globally unique (example: `cosmopilot-db-123`)

### Deployment Steps

#### Step 1: Authenticate with Azure
```bash
az login
```
This opens your browser to sign in. Ensure you're logged into the correct Azure account.

#### Step 2: Navigate to Infrastructure Directory
```bash
cd infra
```

#### Step 3: Run the Deployment Script

**On macOS/Linux:**
```bash
bash deploy.sh
```

**On Windows (PowerShell):**
```powershell
.\deploy.ps1
```

The script will prompt you for configuration values. **Use the defaults** for a quick demo, or customize:

| Prompt | Default | Description |
|--------|---------|-------------|
| **Resource group name** | *(required)* | Container for your Azure resources (e.g., `cosmopilot-rg`) |
| **Environment name** | `demo` | Tag for environment organization (e.g., `dev`, `test`, `prod`) |
| **Azure region** | `eastus` | Region where resources are deployed; options: `eastus`, `eastus2`, `westeurope`, `uksouth`, `swedencentral` |
| **Cosmos DB account name** | `cosmopilot-db` | ⚠️ **Must be globally unique** across all Azure; use lowercase + numbers + hyphens |
| **SQL database name** | `cosmopilot` | Logical database within Cosmos DB |
| **Container name** | `conversations` | Where documents will be stored (like a table) |
| **Partition key path** | `/tenantId` | Field used to partition data; don't change unless you know what you're doing |
| **Throughput (RU/s)** | `400` | Performance level; 400 is good for development, increase for production |
| **Consistency level** | `Session` | Read-write consistency; `Session` is recommended for most use cases |
| **Foundry Project name** | `cosmopilot` | Name for your AI Foundry project |
| **Public network access** | `Enabled` | Allow internet access; set to `Disabled` for private networks only |
| **Enable data isolation** | `false` | Advanced security feature; not needed for development |

#### Step 4: Create Resource Group (if needed)
If you haven't created the resource group, the script will display a command:
```bash
az group create --name '<your-resource-group-name>' --location '<your-location>'
```

#### Step 5: Deploy Resources
The script displays the deployment command. Run it:
```bash
az deployment group create \
  --resource-group '<your-resource-group-name>' \
  --template-file 'main.bicep' \
  --parameters '@main.parameters.json'
```

**Deployment typically takes 5-10 minutes.** You'll see progress updates in your terminal.

#### Step 6: Capture Output Values
Once deployment completes, save the output values displayed by Azure CLI. These include:
- **Cosmos DB Endpoint**: Connection URL for your database
- **Cosmos DB Account Name**: Identifier for your database
- **Foundry Project Name**: Your AI project identifier
- **Model Deployment Name**: `gpt-4o-nano`
- **Embedding Deployment Name**: `text-embedding-3-nano`

### Configuration Details

#### Cosmos DB Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| **cosmosAccountName** | Globally unique identifier for your Cosmos DB account | `cosmopilot-db-001` |
| **sqlDatabaseName** | Logical database within Cosmos DB | `cosmopilot` |
| **containerName** | Container where documents are stored | `conversations` |
| **partitionKeyPath** | Field used by Cosmos DB to distribute data across partitions | `/tenantId` |
| **throughput** | Request units per second (RU/s) for performance; higher = faster/more expensive | `400` (dev) to `10000` (production) |
| **consistencyLevel** | How strictly reads and writes are synchronized | `Session` (default, balanced), `Strong` (strict), `Eventual` (fast) |

#### Foundry Project Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| **projectName** | Name of your AI Foundry project | `cosmopilot` |
| **publicNetworkAccess** | Whether the project is accessible from the internet | `Enabled` (default), `Disabled` (private network only) |
| **enableDataIsolation** | Advanced security: isolate project in private virtual network | `false` (default), `true` (enterprise security) |

### Post-Deployment: Next Steps

After successful deployment:

1. **Access Cosmos DB**
   - Go to [Azure Portal](https://portal.azure.com)
   - Find your Cosmos DB account
   - Use Data Explorer to view/manage your data

2. **Access Foundry Project**
   - Visit your Foundry project in Azure Portal
   - Deploy language models (gpt-4o-nano) and embeddings (text-embedding-3-nano)
   - Configure API keys for frontend integration

3. **Connect Frontend**
   - Retrieve Cosmos DB connection string
   - Update frontend configuration with connection details
   - Deploy or run locally

4. **Scale Up (Production)**
   - Increase throughput if needed (`az cosmosdb sql container throughput update`)
   - Enable data isolation for security
   - Configure backup and recovery policies
   - Set up monitoring and alerts

### Troubleshooting

#### Issue: "Cosmos DB account name already exists"
**Cause**: The account name must be globally unique across all Azure. Someone else may have used it.

**Solution**: Modify the name with a suffix (e.g., `cosmopilot-db-yourname-123`).

#### Issue: "Service limit exceeded" or quota errors
**Cause**: Your subscription has resource limits (e.g., max Cosmos DB accounts, cores).

**Solution**:
- Check current quotas: `az provider show --namespace Microsoft.DocumentDB --query resourceTypes[?resourceType=='databaseAccounts'].limits`
- Request quota increase in Azure Portal > Subscriptions > Usage + quotas

#### Issue: "User does not have permission to perform action"
**Cause**: Your Azure account lacks required permissions.

**Solution**:
- Ensure you're logged into the correct account: `az account show`
- Contact your Azure subscription administrator to grant necessary roles
- Required role: **Contributor** or **Owner** for the resource group

#### Issue: "InvalidParameter" or validation errors
**Cause**: Invalid values provided (e.g., unsupported region, special characters in names).

**Solution**:
- Re-run `bash deploy.sh` and use valid values
- Region must be one of: `eastus`, `eastus2`, `westeurope`, `uksouth`, `swedencentral`
- Names must use only lowercase letters, numbers, and hyphens

#### Issue: Deployment hangs or takes too long
**Cause**: Network issues or resource creation delays.

**Solution**:
- Wait 15-20 minutes for deployment to complete
- If still hung, check Azure Portal for deployment status
- Cancel and retry: `az deployment group cancel --resource-group '<name>' --name '<deployment-name>'`

#### Issue: "The template is invalid"
**Cause**: `main.bicep` or `main.parameters.json` is corrupted or has syntax errors.

**Solution**:
- Verify files are not modified: `git diff infra/`
- Re-download from repository if needed
- Ensure JSON syntax in `main.parameters.json` is correct

### Getting Help

- **Azure Documentation**: [learn.microsoft.com](https://learn.microsoft.com)
- **Cosmos DB Guide**: [docs.microsoft.com/cosmos-db](https://docs.microsoft.com/azure/cosmos-db)
- **Azure CLI Reference**: [learn.microsoft.com/cli/azure](https://learn.microsoft.com/cli/azure)
- **Report Issues**: Open a GitHub issue on this repository

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <img src="assets/overlay.png" alt="Cosmopilot Overlay" width="50%" />
</p>

<!-- COMMENTED OUT - Original notes:
# Cosmopilot

- Conversation history and sessions stored in Cosmos DB
- Operational data in Cosmos DB
- Vectors in Cosmos DB

- Microsoft Foundry + fast model + fast embedding
- Feed in realtime changes
- Use change feed

Use Helix + Zellij + opencode and a lightweight and fast model

/infra (Cosmos DB + make sure the IP bs is disabled, etc etc)

front-end in /frontend

Use-case operational data

/src

/tests

/docs

/.github


No backend except for indexing 

frontend connects direclty to backend( TS)

indexing is handled by a function in the change feed. python or js or whatever

https://github.com/copilotkit/copilotkit

Add voice to it 

(Speech to text and text to speech)
In the agent add a way to vibe code operational data for cosmos db (via a script to bootstrap it) similarly should change the script that creates realtime operational data.
Repo should be empty (no opeorational data)

Nano or mini model

diskANN for faster ops

Add evals set

Complete demo of "Operate" + "Discover"
-->
