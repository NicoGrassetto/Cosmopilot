# Frequently Asked Questions (FAQ)

## General Questions

### What is Cosmopilot?

Cosmopilot is a demo showcasing Microsoft Foundry as an AI platform combined with Cosmos DB for unified storage of both vectors and operational data. It's optimized for speed and real-time data refresh.

### Who should use Cosmopilot?

- Developers exploring Microsoft Foundry and Cosmos DB
- Teams building AI-powered chat applications
- Researchers prototyping real-time AI systems
- Anyone interested in vector databases + operational data patterns

### Is Cosmopilot production-ready?

Cosmopilot is a demo and learning project. While built with best practices, thoroughly test and customize for your production use case.

## Deployment & Setup

### How do I deploy Cosmopilot?

```bash
cd infra
./deploy.sh
```

The script will prompt for configuration values. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### What are the prerequisites?

- Azure subscription with available quotas
- Azure CLI installed and authenticated
- Node.js 18+ for frontend
- Helix editor (optional, for development)

### What regions does Cosmopilot support?

- East US
- East US 2
- West Europe
- UK South
- Sweden Central

### How much does it cost?

Cosmos DB (400 RU/s): ~$25-30/month with free tier
AI Foundry: Pay-per-use for model inference and embeddings

See Azure Pricing Calculator for exact estimates.

### Can I use it in other regions?

Not by default, but you can modify `main.bicep` to add regions. See the `@allowed` decorator on the `location` parameter.

## Architecture & Design

### Why Cosmos DB instead of traditional databases?

- Real-time change feed for streaming updates
- Native vector storage (vectorize integrations)
- Excellent for multi-tenant applications
- Built-in global distribution

### What's the difference between vectors and operational data?

- **Vectors:** Embeddings used for semantic search (text-embedding-3-nano)
- **Operational Data:** Chat messages, session state, user information

Cosmos DB stores both in the same database for unified management.

### How does the change feed work?

Cosmos DB automatically captures all data mutations. A processor function listens to changes and can trigger actions (e.g., re-indexing via embeddings).

### Can I use a different AI model?

Yes, modify `main.bicep`:
- Change `modelType` variable to a different model name
- Ensure the model is available in your Foundry Project region
- Update API calls in frontend/backend accordingly

## Troubleshooting

### Deployment fails with "Quota exceeded"

Check available quotas:
```bash
az quota list --scope /subscriptions/<id>/providers/Microsoft.Compute/locations/eastus
```

Request quota increase in Azure Portal, or try a different region.

### Frontend won't connect to backend

1. Verify Cosmos DB account is deployed
2. Check firewall rules allow your IP
3. Verify connection string in frontend config
4. Check Azure Portal > Cosmos DB > Connection String

### Models not available in Foundry

1. Verify region supports the model
2. Check Foundry Project created successfully in Portal
3. Ensure quotas allow model deployment
4. See [ROADMAP.md](ROADMAP.md) for available models

### How do I enable real-time updates?

Real-time is automatic via Cosmos DB change feed. The change feed processor (planned feature) will handle indexing on mutations.

## Development

### How do I run the frontend locally?

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in browser.

### How do I modify the infrastructure?

Edit `infra/main.bicep` and redeploy:
```bash
az deployment group create \
  --resource-group <rg> \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json
```

### Can I use Cosmopilot without Foundry?

No, Foundry is core to this demo. However, you can modify to use OpenAI API directly.

### How do I add voice support?

See [ROADMAP.md](ROADMAP.md). Voice support is planned for Q3 2024.

## Data & Security

### Is my data encrypted?

- **In transit:** Yes, HTTPS/TLS enforced
- **At rest:** Cosmos DB default encryption applies
- **Backups:** Cosmos DB automatic backups

### Can I export my data?

Yes, Cosmos DB supports export via:
- Azure Cosmos DB Data Migration tool
- Azure Data Factory
- Custom scripts using SDK

### How do I comply with data residency requirements?

Deploy to region matching your requirements (Sweden Central for EU, etc.). See supported regions above.

### Is PII deleted automatically?

No. Implement retention policies or manual cleanup as needed for your compliance requirements.

## Contributing & Community

### How do I report a bug?

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue templates and guidelines.

### How do I contribute code?

1. Fork the repository
2. Create a feature branch
3. Make changes and test
4. Submit pull request
5. See [CONTRIBUTING.md](CONTRIBUTING.md) for details

### How do I report a security issue?

See [SECURITY.md](SECURITY.md) for private reporting instructions.

### Where can I get help?

- GitHub Discussions for questions
- GitHub Issues for bugs
- Email maintainers for urgent matters
- See [SUPPORT.md](SUPPORT.md) for all options

## Still Have Questions?

- Check [README.md](README.md) and project documentation
- Open a GitHub Discussion
- See [SUPPORT.md](SUPPORT.md) for more resources
- Review infrastructure comments in `main.bicep`

---

**Last Updated:** 2024-06-25
