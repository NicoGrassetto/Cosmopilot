The minimum addition is one APIM instance; you can reuse your Foundry resource and monitoring. Redis and Content Safety are optional, while private networking adds work. One important constraint for future HA planning: the current v2 documentation still lists built-in multi-region deployment as unavailable.
**My recommendation:** add one APIM v2 instance, reuse your existing Foundry and monitoring resources, and initially implement authentication, token limits, and telemetry. Redis, additional model deployments, and a separate proxy application are not required for the first version.

### Implementation Effort
These are engineering estimates for one Azure-experienced developer, assuming access and model deployments are already available.

| Scope | Estimated Effort |
|---|---|
| Portal PoC: one model, authentication, token limit, logs | **0.5-1 day** |
| Repeatable Cosmopilot MVP: Bicep, policies, agent integration, tests | **3-5 days** |
| Production setup: private networking, tenant isolation, resilience, load testing, operational procedures | **2-4 weeks**, excluding approval delays |

APIM’s [AI gateway capabilities](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities) are built into APIM, not a separate gateway service you must host.

### Services Needed
| Service | Requirement |
|---|---|
| **Azure API Management** | New resource. Basic v2 for the PoC; Standard v2 is a practical production starting point. |
| **Foundry resource, project, model deployments** | Reuse those already defined in [infra/resources.bicep](infra/resources.bicep#L171). |
| **Managed identities and Entra RBAC** | Configure caller authorization and APIM-to-Foundry authentication separately. |
| **Application Insights + Log Analytics** | Reuse your [existing resources](infra/resources.bicep#L418); add APIM logging and diagnostics configuration. |
| **Azure AI Content Safety** | Optional, for centralized prompt/response moderation and prompt-attack checks. |
| **Azure Managed Redis + embeddings deployment** | Optional, only for semantic caching. Requires a compatible vector-search cache configuration. |
| **VNet, private endpoints, private DNS** | Required if you want private connectivity and network-level bypass prevention. |
| **Key Vault** | Optional for provider keys or certificates; unnecessary for a purely managed-identity authentication path. |

**Tier considerations:** Standard v2 supports outbound VNet integration and inbound private endpoints. Premium v2 adds VNet injection and zone redundancy. Current [v2 documentation](https://learn.microsoft.com/en-us/azure/api-management/v2-service-tiers-overview) still lists built-in multi-region deployment as unavailable.

### AI Policies
| Control | Policy or Configuration | Recommendation |
|---|---|---|
| Caller authorization | `validate-azure-ad-token` | Validate audience, allowed applications, and roles/claims. |
| Backend authentication | `authentication-managed-identity`, or backend identity configuration | For Azure OpenAI models, grant APIM **Cognitive Services OpenAI User** on Foundry; use the Cognitive Services token audience. |
| Request throttling | `rate-limit-by-key` | Protect against excessive requests independently of token consumption. |
| Token budgets | [`llm-token-limit`](https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy) | Set per-app/project TPM and daily/monthly quotas. |
| Usage visibility | [`llm-emit-token-metric`](https://learn.microsoft.com/en-us/azure/api-management/llm-emit-token-metric-policy) + diagnostics | Track model and consumer usage; avoid logging raw prompts by default. |
| Content protection | [`llm-content-safety`](https://learn.microsoft.com/en-us/azure/api-management/llm-content-safety-policy) | Optional prompt shields and input/output moderation; retain model-side safeguards. |
| Routing and resilience | `set-backend-service`, backend pools, circuit breakers, bounded `retry` | Respect `Retry-After`; failover needs compatible deployments with available capacity. |
| Streaming | `forward-request` with `buffer-response="false"` | Preserve streaming and test long-running responses. |
| Semantic caching | `llm-semantic-cache-lookup` + `llm-semantic-cache-store` | Defer initially, especially for personalized or stateful agent interactions. |

Key budgets by a **validated identity**, not an arbitrary caller-supplied header. Token limits are guardrails rather than exact spending caps: concurrency can overshoot, streaming involves estimates, and counters are maintained per gateway. Avoid blindly retrying agent actions or distributing stateful conversations across unrelated backends.

### Connecting Foundry
There are different integration paths, depending on which traffic you want to govern.

1. **Application or hosted agent → APIM → Foundry model.**  
   In APIM, select **APIs → Add API → Microsoft Foundry**, import the appropriate API, and configure identity/policies. Point the model client at APIM’s configured OpenAI-compatible base URL. The [import wizard](https://learn.microsoft.com/en-us/azure/api-management/azure-ai-foundry-api) can configure the backend and managed identity. This is the most explicit routing option.

2. **Native Foundry AI Gateway integration, currently documented as preview.**  
   In Foundry, select **Manage → AI Gateway → Add AI Gateway**. Create Basic v2 or associate an existing **v2 instance in the same tenant and subscription**. Explicitly add your existing project, then configure project/deployment token limits. New projects are enabled by default. See the [setup guide](https://learn.microsoft.com/en-us/azure/foundry/configuration/enable-ai-api-management-gateway-portal). This governs supported project traffic; it is not a general interception mechanism for every Foundry management API or arbitrary outbound request.

3. **Foundry prompt agent → existing enterprise APIM → model.**  
   Add an **Admin-connected models → Azure API Management** connection, configure its base URL and authentication, and select the agent model as `<connection-name>/<model-name>`. The [BYOM guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/ai-gateway) currently limits this mechanism to prompt agents and lists Responses as unsupported. That is a connector limitation, not a blanket APIM limitation: APIM itself supports Responses APIs.

4. **Foundry agent → APIM → MCP tool.**  
   [Native tool governance](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/governance) is separate and currently preview. It applies to eligible new portal-created MCP tools; existing tools are not automatically rerouted, and managed-OAuth tools are excluded.

### For Cosmopilot
Your hosted agent constructs its model client in [main.py](src/agents/pong-ping-agent/main.py#L8). That is the relevant integration point for its model calls, not just the deployment script. Exposing the agent’s Responses endpoint through APIM would govern **incoming agent requests**, but would not by itself govern every model call the agent makes.

I would first enable native project integration and verify your actual hosted-agent traffic in APIM logs. If that runtime path is not mediated, explicitly configure its model client to call APIM. **Do not replace `AZURE_AI_PROJECT_ENDPOINT` with an OpenAI gateway URL indiscriminately:** project APIs and model APIs have different contracts.

The MVP acceptance checks should cover successful inference, rejected unauthorized callers, TPM `429`, quota `403`, streaming, usage attribution, and blocked direct-backend access where gateway enforcement is required. Infrastructure changes can remain within the existing Bicep deployment model.

This assessment is based on repository inspection and current Microsoft documentation; no resources were deployed or live routing tested.