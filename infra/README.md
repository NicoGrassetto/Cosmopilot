# Cosmopilot Infrastructure

This directory contains the infrastructure-as-code and deployment scripts for Cosmopilot.

## Files

- **`main.bicep`** - Azure Resource Manager (ARM) template defining Cosmos DB and AI Foundry Project resources
- **`main.parameters.json`** - Generated at deployment time; contains your configuration values
- **`deploy.sh`** - Deployment script for macOS and Linux
- **`deploy.ps1`** - Deployment script for Windows (PowerShell)

## Deployment

### macOS / Linux
```bash
bash deploy.sh
```

### Windows (PowerShell)
```powershell
.\deploy.ps1
```

Both scripts will:
1. Check for Azure CLI installation
2. Prompt you for configuration values (or use defaults)
3. Generate `main.parameters.json`
4. Display the Azure CLI commands to create your resource group and deploy resources

## What Gets Deployed

| Resource | Details |
|----------|---------|
| **Cosmos DB Account** | Multi-model database for conversations, vectors, and operational data |
| **SQL Database** | Logical database within Cosmos DB |
| **Container** | "conversations" container with `/tenantId` partition key |
| **AI Foundry Project** | Hub-less Foundry project for AI model deployments |

## Configuration Parameters

See the main [README.md](../README.md#getting-started-deploying-to-azure) for detailed documentation on:
- Configuration options
- Parameter explanations
- Post-deployment steps
- Troubleshooting

## Architecture

```
Resource Group (cosmospilot-rg)
├── Cosmos DB Account (cosmopilot-db)
│   ├── SQL Database (cosmopilot)
│   │   └── Container (conversations)
│   │       └── Partition Key: /tenantId
│   │       └── Throughput: 400 RU/s
│
└── AI Foundry Resource
    └── Foundry Project
        └── Ready for model deployments
```
