# Architecture

This document describes the architecture and design of Cosmopilot.

## System Overview

Cosmopilot is a real-time AI-powered chat application that combines:
- **Azure Cosmos DB** for unified data storage (operational + vectors)
- **Microsoft Foundry** for model deployment and inference
- **Svelte frontend** for user interface
- **Change feed processing** for real-time indexing

```
┌─────────────────────────────────────────────────────────────────┐
│                       Frontend (Svelte)                         │
│  - Chat UI, message display, real-time updates                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  API Gateway    │
                    │  (Future)       │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐      ┌────────▼────────┐    ┌────▼──────┐
   │ Cosmos  │      │  AI Foundry     │    │  Storage  │
   │   DB    │◄────►│   (Models)      │    │  (Blob)   │
   │         │      │                 │    │           │
   │ - Chat  │      │ - GPT-4o Nano   │    │ - Assets  │
   │ - Ops   │      │ - Embeddings    │    │ - Logs    │
   │ - Users │      │ - Inference     │    │           │
   └────┬────┘      └────────┬────────┘    └───────────┘
        │                    │
        └────────┬───────────┘
                 │
        ┌────────▼────────┐
        │ Change Feed     │
        │ Processor       │
        │ (Azure Func)    │
        │ - Indexing      │
        │ - Vector Gen    │
        │ - Aggregation   │
        └─────────────────┘
```

## Core Components

### 1. Frontend (Svelte + Vite)

**Location:** `/frontend`

**Responsibilities:**
- User interface for chat
- Real-time message display
- User input handling
- Session management
- WebSocket/API communication

**Technologies:**
- Svelte 4 for reactive components
- Vite for fast build and dev server
- CSS for styling

**Key Files:**
- `src/App.svelte` — Main app component
- `src/components/Chatbot.svelte` — Chat interface
- `src/components/MessageBubble.svelte` — Message display
- `src/components/InputBox.svelte` — User input

---

### 2. Cosmos DB

**Type:** SQL API (Document store)

**Database:** `cosmopilot`

**Container:** `conversations`

**Partition Key:** `/tenantId` (supports multi-tenant)

**Data Model:**

```json
{
  "id": "msg-12345",
  "tenantId": "user-abc",
  "conversationId": "conv-xyz",
  "role": "user|assistant",
  "content": "Hello, how can you help?",
  "embedding": [0.123, 0.456, ...],  // text-embedding-3-nano
  "timestamp": "2024-06-25T16:00:00Z",
  "metadata": {
    "model": "gpt-4o-nano",
    "tokens": { "prompt": 10, "completion": 25 }
  }
}
```

**Configuration:**
- **Throughput:** 400 RU/s (configurable)
- **Consistency:** Session-level
- **Indexing:** Automatic (all fields except `_etag`)
- **TTL:** Off (permanent storage)
- **Backup:** Continuous (7 days)

**Change Feed:**
- Enabled by default
- Captures all mutations (insert, update, delete)
- Ordered per partition key
- Used by indexing processor

---

### 3. Azure AI Foundry

**Project:** `cosmopilot-<unique-suffix>`

**Models Deployed:**

| Model | Purpose | Provider | Quota |
|-------|---------|----------|-------|
| `gpt-4o-nano` | Chat inference | OpenAI | Shared (TPM) |
| `text-embedding-3-nano` | Vector embeddings | OpenAI | Shared (TPM) |

**Configuration:**
- **Region:** East US, East US 2, West Europe, UK South, Sweden Central
- **Public Access:** Enabled (configurable)
- **Data Isolation:** Disabled (optional)
- **Managed Identity:** SystemAssigned

**Quota System:**
- Uses TPM (Tokens Per Minute) shared quota
- Default ~20K TPM per region per subscription
- Monitor usage in Azure Portal
- Request increase if needed

---

### 4. Change Feed Processor

**Location:** `/src` (future implementation)

**Type:** Azure Function (time-triggered)

**Responsibilities:**
1. Poll Cosmos DB change feed
2. Extract new/updated messages
3. Call `text-embedding-3-nano` for vectors
4. Store vectors back in Cosmos DB
5. Update search indices

**Trigger:** Every 5 minutes (configurable)

**Pseudocode:**
```python
def process_change_feed():
    changes = cosmos.read_change_feed()
    for msg in changes:
        if not msg.embedding:
            vector = foundry.embed(msg.content)
            cosmos.update(msg.id, {"embedding": vector})
    return len(changes)
```

---

### 5. Infrastructure as Code

**Location:** `/infra`

**File:** `main.bicep` (compiled to `main.json`)

**Resources Deployed:**
1. Cosmos DB Account (with database & container)
2. AI Foundry Project
3. Auto-managed resources:
   - Storage Account (for Foundry)
   - Key Vault (for secrets)
   - Application Insights (for monitoring)

**Deployment Script:** `deploy.sh`
- Prompts for configuration
- Generates `main.parameters.json`
- Runs `az deployment group create`

---

## Data Flow

### 1. User Sends Message

```
User Input
    ↓
Frontend (Svelte)
    ↓
Validate & Format
    ↓
POST /api/messages → Backend API (future)
    ↓
Cosmos DB (insert)
    ↓
Return MessageId
    ↓
Frontend Updates UI
```

### 2. AI Generates Response

```
Message stored in Cosmos
    ↓
API Handler triggers Foundry
    ↓
Call gpt-4o-nano (via Foundry)
    ↓
Get response
    ↓
Cosmos DB (insert assistant message)
    ↓
Frontend receives update (WebSocket/polling)
    ↓
Display in chat
```

### 3. Embedding & Indexing (Change Feed)

```
Message inserted/updated in Cosmos
    ↓
Change Feed detects mutation
    ↓
Processor polls change feed (every 5 min)
    ↓
Extract message content
    ↓
Call text-embedding-3-nano (via Foundry)
    ↓
Get 1536-dim vector
    ↓
Update Cosmos with embedding field
    ↓
Vector searchable in Cosmos
```

### 4. Semantic Search

```
User searches "help with Azure"
    ↓
Frontend calls /api/search
    ↓
Backend embeds query via text-embedding-3-nano
    ↓
Vector search in Cosmos (cosine similarity)
    ↓
Return top-K matching messages
    ↓
Display search results
```

---

## Scalability Considerations

### Vertical Scaling (within single region)

**Cosmos DB:**
- Increase RU/s: 400 → 1000 → 10,000+ (on-demand)
- Automatic partitioning as data grows
- Max partition size: 10 GB

**Foundry:**
- TPM quota auto-scales with usage
- No manual intervention needed for shared models
- Consider Provisioned Throughput Units (PTU) for predictable cost

### Horizontal Scaling (multi-region)

**Cosmos DB:**
- Enable multi-region replication
- Reads from nearest region
- Writes to primary region

**Foundry:**
- Deploy to multiple regions
- Route requests to nearest endpoint
- Independent quota per region

### Change Feed Processing

**Current:** Single processor (time-triggered function)

**Future:** Scale with workload
- Parallel processing per partition
- Lease container for distributed coordination
- Auto-scaling based on queue depth

---

## Security Architecture

### Data Protection

1. **In Transit:**
   - HTTPS/TLS 1.2+ enforced
   - API authentication via tokens
   - Managed service endpoints

2. **At Rest:**
   - Cosmos DB encryption (Microsoft-managed keys by default)
   - Key Vault for secrets
   - Blob storage encryption

### Identity & Access

1. **Application Identity:**
   - Foundry Project: SystemAssigned Managed Identity
   - Functions: Managed Identity (future)
   - No connection strings in code

2. **User Authentication:**
   - Entra ID integration (future)
   - Multi-tenant isolation via `tenantId`
   - Row-level security in Cosmos

3. **Network:**
   - Public endpoints (configurable)
   - Private endpoints optional (via VNet)
   - Network ACLs on Key Vault

### Secrets Management

- Connection strings → Key Vault
- API keys → Managed Identity
- No secrets in code or config files
- Automatic rotation support

---

## Performance Optimization

### Cosmos DB

**Query Optimization:**
- Index all frequently queried fields
- Use partition key in WHERE clause
- Avoid cross-partition queries
- Cache results where possible

**RU/s Optimization:**
- Monitor query cost (RU consumption)
- Use smaller document size
- Batch operations
- Enable autoscale for variable workloads

**Change Feed:**
- Process in batches (not per-item)
- Use leases for distributed processing
- Monitor lag and backlog

### Foundry Models

**Inference Optimization:**
- Batch embedding requests
- Cache embeddings for repeated text
- Monitor TPM usage
- Use nano models for speed (not quality trade-off)

**Embedding:**
- 1536-dim vectors (text-embedding-3-nano)
- Suitable for cosine similarity search
- Can be compressed for storage savings

---

## Monitoring & Observability

### Key Metrics

1. **Cosmos DB:**
   - RU/s usage vs provisioned
   - Query latency (p50, p95, p99)
   - Change feed lag
   - Storage size (GB)

2. **Foundry:**
   - TPM usage vs quota
   - Model inference latency
   - Error rates
   - Token usage

3. **Frontend:**
   - Page load time
   - Time to first message
   - Error rate
   - User session duration

### Logging & Debugging

- **Application Insights:** Full telemetry
- **Cosmos DB Diagnostics:** Query performance
- **Browser DevTools:** Frontend debugging
- **Azure CLI:** Resource health checks

---

## Future Architecture Changes

### Planned Additions

1. **API Gateway:**
   - Authentication & authorization
   - Rate limiting
   - Request logging
   - OpenAPI documentation

2. **Voice Processing:**
   - Speech-to-text (Azure Speech Service)
   - Text-to-speech (Cognitive Services)
   - WebRTC for real-time audio

3. **Advanced Indexing:**
   - Hierarchical Navigable Small-World (HNSW)
   - diskANN for large-scale vectors
   - Semantic caching

4. **Evaluation Framework:**
   - Model performance tracking
   - A/B testing infrastructure
   - Automated quality metrics

---

## Technology Choices

### Why Cosmos DB?

✅ **Real-time change feed** — Perfect for streaming updates
✅ **Vector storage** — Native support for embeddings
✅ **Multi-tenant** — Partition key isolation
✅ **Global distribution** — Low latency worldwide
✅ **Flexible schema** — Evolves with needs

### Why Foundry?

✅ **Managed models** — No infrastructure to manage
✅ **Speed** — Nano models optimized for latency
✅ **Cost-effective** — Pay only for usage
✅ **Enterprise integration** — Works with Azure ecosystem
✅ **Easy scaling** — TPM shared quota

### Why Svelte?

✅ **Lightweight** — Small bundle size
✅ **Reactive** — Real-time updates natural
✅ **Developer experience** — Fast build/dev cycle
✅ **Performance** — Minimal runtime overhead

---

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│        Bicep Infrastructure as Code         │
│  (infra/main.bicep → main.json compiled)    │
└──────────────┬──────────────────────────────┘
               │
        ┌──────▼───────┐
        │ deploy.sh    │ (Interactive setup)
        └──────┬───────┘
               │
        ┌──────▼──────────────────────────────┐
        │  az deployment group create         │
        │  (Validates & deploys)              │
        └──────┬───────────────────────────────┘
               │
        ┌──────▼──────────────────────────────┐
        │  Azure Resource Manager             │
        │  (Orchestrates resource creation)   │
        └──────┬───────────────────────────────┘
               │
    ┌──────────┼──────────────┐
    │          │              │
┌───▼──┐  ┌────▼────┐    ┌───▼──┐
│Cosmos│  │Foundry  │    │Other │
│  DB  │  │ Project │    │Svc   │
└──────┘  └─────────┘    └──────┘
```

---

## Disaster Recovery

### Backup & Recovery

1. **Cosmos DB:**
   - Automatic backups (7 days)
   - Point-in-time restore available
   - Cross-region replication optional

2. **Infrastructure:**
   - Bicep template is source of truth
   - Redeploy to recreate resources
   - Parameters in version control

3. **Frontend:**
   - Deployed as static files (can be cached)
   - Recoverable from git repository

### RTO & RPO

- **RTO (Recovery Time Objective):** ~15 minutes (redeploy infrastructure)
- **RPO (Recovery Point Objective):** Real-time for Cosmos DB changes

---

## Cost Analysis

### Monthly Estimate (Demo Environment)

| Component | Cost | Notes |
|-----------|------|-------|
| Cosmos DB | $25-30 | 400 RU/s with free tier |
| Foundry (inference) | $5-50 | Variable based on usage |
| Foundry (embeddings) | $5-50 | Variable based on usage |
| Storage (metadata) | $1-5 | Auto-managed by Foundry |
| **Total** | **$36-135** | Per month (demo scale) |

### Cost Optimization

- Use nano models (cheaper)
- Batch requests (fewer calls)
- Cache embeddings (avoid recomputation)
- Set TTL on temporary data
- Monitor TPM quota usage
- Use autoscale only when needed

---

## References

- [Cosmos DB Documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/)
- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-services/foundry/)
- [Change Feed Overview](https://learn.microsoft.com/en-us/azure/cosmos-db/change-feed)
- [Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Svelte Guide](https://svelte.dev/docs)

---

**Last Updated:** 2024-06-25

For questions, see [FAQ.md](FAQ.md) or [SUPPORT.md](SUPPORT.md).
