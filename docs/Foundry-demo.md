# EU Intelligence and Resilience Command Center

## Executive storyline

Europe already has the data needed to spot cascading crises, but that data is spread across agencies, domains, formats, and operating rhythms. Copernicus sees environmental stress. ECDC sees public-health impact. EFSA sees food-system risk. Eurostat sees population exposure. EBA and ESM see financial-system vulnerability. Each view is valuable, but no single agency has the complete chain of consequence.

The production storyline is the **EU Intelligence and Resilience Command Center**: a shared Microsoft Fabric platform that fuses environmental, health, food, demographic, financial, and macroeconomic signals into one operational picture. The business demo preserves that architecture while using a local evidence adapter in place of a live Fabric connection.

The central question:

> Which EU regions are at highest risk of cascading societal impact in the next 30 days, and why?

The answer is not one dashboard, one model, or one chatbot. It is a governed data and intelligence fabric:

1. OneLake unifies trusted data from agencies and open sources.
2. Lakehouse and Warehouse workloads harmonize those sources into common regional facts.
3. Real-Time Intelligence captures alerts such as wildfire, flood, health, food, and banking stress signals.
4. Power BI provides the central command dashboard.
5. Fabric IQ adds the business meaning: Region, Event, Population, Food Supply, Health System, Bank, and Stability Risk.
6. A Fabric data agent lets decision-makers ask natural-language questions grounded in semantic models and ontology.

The cross-agency coordination application is the downstream Foundry scenario: the evidence layer identifies the risk and explains the chain of impact; Foundry applies the response playbook and turns that evidence into a controlled, human-approved action.

## Demo narrative: The Summer Crisis

Europe enters a prolonged summer heatwave. In this version of the demo, the environmental evidence layer is grounded in the two supplied EU 2026 wildfire datasets:

- `estimates-overview-ba_EU_2026_2006_2025 (1).csv`: burned area by EU country, comparing 2026 with the 2006-2025 annual average.
- `estimates-overview-nf_EU_2026_2006_2025.csv`: number of fires by EU country, comparing 2026 with the 2006-2025 annual average.

The synthetic model uses **all 27 EU countries represented in those files**, not only a small sample set. The dashboard uses country-level grain for the summit storyline, while the same pattern can drill down later into NUTS regions.

In isolation, each signal looks manageable:

- Copernicus and EFFIS detect burned area, number of fires, heat, drought, vegetation stress, and wildfire probability.
- EFSA sees crop-yield pressure and regional water stress.
- ECDC sees heat-related hospitalizations and respiratory cases rising.
- Eurostat identifies regions with high elderly population share and dense urban exposure.
- EBA sees banks with concentrated agricultural loan exposure and stress-test capital vulnerability in affected countries.
- ESM sees early economic stress and recovery-fund pressure.

The command center exposes the real issue: the crisis is not only environmental. It is a cross-domain resilience problem:

`Heatwave -> Drought -> Crop stress -> Food supply pressure -> Health system load -> GDP impact -> Banking exposure -> Financial stability risk`

This is the Fabric IQ moment. Fabric can report what is happening; Fabric IQ explains how the concepts are connected.

## Foundry demo: From governed insight to approved action

The business audience should see a decision-support experience, not another data-analysis tool or a developer agent.

### The differentiation

The Foundry agent does not duplicate the production Fabric data agent. The handoff is explicit:

> **Fabric supplies governed evidence. Foundry converts that evidence into a policy-constrained, human-approved, auditable coordination action.**

| Fabric and Fabric IQ | Microsoft Foundry |
| --- | --- |
| Unify and govern the source data | Consume the governed evidence package |
| Rank countries and explain the contributing indicators | Validate whether the evidence is sufficient for action |
| Connect Region, Event, Population, Food Supply, Health System, Bank, and Stability Risk | Apply the cross-agency coordination playbook |
| Answer **what is happening and why** | Recommend **what should happen next** |
| Support exploration through dashboards, semantic models, and a data agent | Prepare an action, request approval, execute it, and return a receipt |

The Foundry prompt agent is the **EU Cross-Agency Coordination Agent**. Its responsibility begins after the configured evidence provider has identified and explained a material resilience risk. Fabric is that provider in production; the local adapter is the provider in this demo.

### Demo implementation without Fabric access

The demo environment does not require access to Microsoft Fabric. Instead, a local **Fabric-compatible evidence adapter** reads the curated EU27 datasets and exposes them to the Foundry prompt agent through function calling.

This adapter reproduces the contract that Fabric would provide in production:

- Ranked country priorities
- Country-level evidence packages
- Observation dates and source labels
- Geographic grain
- Synthetic-data classifications
- Confidence and data limitations

The local adapter does not emulate Fabric services, Fabric IQ, OneLake, or a semantic model. It only supplies a stable, structured evidence package so the Foundry coordination workflow can be demonstrated end to end. Replacing it with a Fabric data agent later should require changing the evidence provider, not the agent's business behavior.

During the business presentation, the audience sees a single EU Cross-Agency Coordination Agent. Function names, local files, Python execution, and other implementation details remain backstage. The presenter describes the evidence as a **curated demo snapshot representing the governed evidence package that Fabric would provide in production**, never as a live Fabric query.

### Foundry tools used

All demo integrations will use Foundry `FunctionTool` definitions. The Foundry model selects a tool, the local chat backend executes the corresponding Python function, and the result is returned to the model as structured JSON.

| Tool | Purpose | Demo behavior |
| --- | --- | --- |
| `get_resilience_priorities` | Answer where leadership should focus | Reads the static EU27 scorecard and returns a ranked list with score, severity, date, and evidence-package identifier |
| `get_country_resilience_evidence` | Explain why a country is a priority | Joins the environmental, wildfire, food, health, economic, population, and banking records for one country |
| `evaluate_coordination_playbook` | Decide whether coordinated review is justified | Applies deterministic demo thresholds and returns the criteria met, lead agency, supporting agencies, playbook version, and limitations |
| `open_coordination_case` | Record the approved business action | Accepts only an approved decision-card payload and returns a mock case identifier, timestamp, status, and evidence correlation identifier |

The first two functions are the **mock Fabric interaction**. They are read-only and operate on the supplied data archive. `evaluate_coordination_playbook` keeps the escalation logic explicit and repeatable instead of asking the model to invent policy. `open_coordination_case` is the only side-effecting operation; for this demo it writes to a local in-memory or file-backed case register and can later be replaced by Azure DevOps or another case-management API.

Human approval is enforced by the application, not only by prompt wording. Preparing a decision card never calls `open_coordination_case`; the function becomes eligible only after the user explicitly approves the displayed draft.

### Agent skills used

Skills provide reusable behavioral instructions to the prompt agent. They guide interpretation and presentation but do not replace deterministic tools or application controls.

| Skill | Responsibility |
| --- | --- |
| `evidence-grounding` | Use tool results for factual claims, include dates and sources, preserve country-level grain, and report missing or conflicting evidence |
| `synthetic-data-disclosure` | Distinguish source-derived, derived, and synthetic values and prevent EBA scenarios from being described as forecasts or current bank distress |
| `coordination-playbook` | Explain the returned playbook criteria and agency assignments without presenting the illustrative demo rules as formal EU policy |
| `human-approval-safety` | Separate preparation from execution, preserve pending status, and require explicit approval before opening a case |
| `executive-briefing` | Produce concise business language, prioritize the strongest drivers, and clearly distinguish observations, interpretations, and plausible scenarios |

These skills will be stored with the EU agent and injected into its instructions when the agent version is created.

### Business problem

Environmental, health, food, economic, and banking teams each see part of a developing crisis. In production, Fabric reconciles those views into a governed operational picture. In the demo, the local evidence adapter supplies the same business-facing evidence contract from a curated static snapshot. Leadership still needs a consistent way to decide whether the evidence meets the criteria for coordinated review, identify the accountable agencies, and record the decision.

The Foundry agent closes that gap by:

1. Requesting a Fabric-compatible evidence package from the local adapter.
2. Checking provenance, observation date, confidence, geographic grain, and synthetic-data limitations.
3. Applying a configured cross-agency coordination playbook.
4. Explaining whether escalation criteria are met and which evidence supports that conclusion.
5. Selecting a lead agency and the supporting agencies required for review.
6. Preparing a decision card without taking action.
7. Waiting for explicit human approval.
8. Opening the approved coordination case and returning an execution receipt.

The playbook used in this demo is illustrative and must not be represented as formal EU policy.

### Visible action

Call the action:

> **Open a cross-agency coordination case**

The action starts an internal review involving the appropriate agencies. It does not issue a public warning, make a financial decision, allocate funds, or automatically trigger an emergency response.

Azure DevOps may be used as the hidden case register, but the business experience must not describe the action as "creating an Azure DevOps work item." The visible outcome is a coordination case and its case identifier.

### Agent operating boundary

The agent must clearly separate:

1. **Evidence package**: sourced observations and governed indicators supplied by Fabric in production or the local adapter in the demo.
2. **Derived interpretation**: the agent's explanation of why the evidence matters.
3. **Scenario**: a plausible consequence chain, never presented as a forecast.
4. **Playbook result**: the coordination criteria that are met or not met.
5. **Proposed action**: a draft that has no operational effect.
6. **Approval status**: pending, approved, rejected, or expired.
7. **Execution result**: the case identifier and returned system status.

The agent must identify synthetic banking records, synthetic climate-credit losses, composite vulnerability scores, and country fallback estimates as synthetic. EBA adverse-scenario results must not be described as forecasts of bank failure or as evidence of current financial distress. Country-level evidence must not be presented as regional or local evidence.

### Business demo walkthrough

#### 1. Establish the priority from the evidence layer

Ask the EU Cross-Agency Coordination Agent:

> "Where should EU leadership focus today?"

The agent calls `get_resilience_priorities`. The local evidence adapter identifies Spain, Italy, and Portugal and returns a short executive summary grounded in the curated EU27 snapshot.

Ask:

> "Why is Spain the priority?"

The agent calls `get_country_resilience_evidence` and explains the principal drivers in plain language: wildfire and drought, food and water pressure, health-system load, and financial exposure. It discloses the snapshot date, country-level grain, and synthetic banking overlays.

#### 2. Evaluate the response in Foundry

Ask the EU Cross-Agency Coordination Agent:

> "Does Spain meet the criteria for cross-agency coordination?"

The agent validates the evidence package, calls `evaluate_coordination_playbook`, and explains which criteria are met. It reports stale, missing, conflicting, or synthetic evidence as limitations rather than silently filling gaps.

Ask:

> "What could this mean for Europe?"

The agent presents the consequence chain as a **plausible scenario**, not a forecast:

`Wildfire and drought -> Crop stress -> Food supply pressure -> Health-system load -> GDP impact -> Banking exposure -> Financial-stability pressure`

Ask:

> "Who should be involved?"

The agent recommends Copernicus as the lead and explains the roles of ECDC, EFSA, EBA, and ESM. Agency selection comes from the coordination playbook, not solely from model judgment.

#### 3. Prepare, approve, and execute the action

Ask:

> "Prepare a coordination action for Spain."

The agent displays a decision card without executing anything. The card shows:

- Country and priority level
- Reason for coordination
- Evidence values, source, and observation date
- Classification of source-derived, derived, and synthetic evidence
- Playbook criteria met
- Lead and participating agencies
- Plausible scenario chain
- Proposed review steps
- Confidence and limitations
- Status: **Pending approval**

Preparing an action never implies approval. The case-opening tool remains unavailable until the user explicitly approves the displayed draft.

Ask:

> "Approve and open the coordination case."

Only then does the agent invoke `open_coordination_case`. It records the approved payload in the demo case register and returns an execution receipt containing:

- Coordination case identifier
- Submission status and timestamp
- Approving user or role, when supplied by the identity layer
- Lead and participating agencies
- Evidence snapshot or correlation identifier
- Link to the case in the business experience

### Three-minute demo message

The audience should leave with one clear distinction:

> **A Fabric-compatible evidence layer found and explained the risk. Foundry applied the operating rules, kept a human in control, and turned the approved decision into a traceable action. In production, Fabric replaces the local evidence adapter without changing the business workflow.**