# Foundry Evaluations

A catalog of every built-in evaluator available in **Microsoft Foundry** observability,
with a doc link, a thorough description, a quick example (input → score), when to use it,
and whether it's in **preview** and/or **portal-only**.

**References:**
- [Observability in Generative AI](https://learn.microsoft.com/en-us/azure/foundry/concepts/observability)
- [Built-in evaluators reference](https://learn.microsoft.com/en-us/azure/foundry/concepts/built-in-evaluators)
- [Custom evaluators](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/custom-evaluators)
- [Region support, rate limits & VNet](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-regions-limits-virtual-network)

**Legend:** 🔬 public preview · 🖥️ agent/portal-only (not available for dataset/model runs) · ⚖️ LLM-as-judge (needs a `deployment_name` and incurs model cost) · 🛡️ hosted safety service (no model deployment needed)

> **How scoring works.** Most LLM-as-judge evaluators return a **1–5 Likert** score with a
> default **pass threshold of 3** (≥3 passes). Content-safety evaluators return a **0–7 severity**
> score where **lower is safer** (default threshold 3, ≤3 passes). N-gram similarity metrics
> return **0–1**. Each run can be `turn`-level (single response, default) or `conversation`-level
> (full multi-turn thread) — all evaluators in one run must share the same level.

---

## General purpose evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/general-purpose-evaluators) · ⚖️ · scale **1–5** (threshold 3)

### Coherence — `builtin.coherence`
- **What:** Logical flow and organization of ideas — does the response read as a well-connected train of thought?
- **Inputs:** `query`, `response`.
- **Example:** query "What are the benefits of renewable energy?" → response "Renewable energy reduces carbon emissions, lowers long-term costs, and provides energy independence." → **score 4 (pass)**.
- **When to use:** QA and summarization, where argument structure/readability matters. Supports conversation-level scoring for topic consistency across turns.

### Fluency — `builtin.fluency`
- **What:** Grammatical accuracy, vocabulary range, and readability, independent of factual correctness.
- **Inputs:** `response`.
- **Example:** response "Plants convert sunlight, water, and CO₂ into glucose and oxygen." → **score 5 (pass)**.
- **When to use:** Whenever writing quality matters on its own. Reliability drops for very short (<~20 token) responses; English-only today.

---

## Textual similarity evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/textual-similarity-evaluators) · compare a `response` against a `ground_truth`

| Evaluator | Type | Scale | What it measures |
| --- | --- | --- | --- |
| Similarity | ⚖️ AI-assisted | 1–5 | Semantic closeness of response to ground truth. |
| F1 Score | deterministic | 0–1 | Harmonic mean of precision/recall over token overlap. |
| BLEU | deterministic | 0–1 | N-gram overlap (translation quality). |
| GLEU | deterministic | 0–1 | Google-BLEU variant, tuned for sentence-level. |
| ROUGE | deterministic | 0–1 | Recall-oriented n-gram overlap (summarization). |
| METEOR | deterministic | 0–1 | N-gram overlap with synonym/stemming/order awareness. |

- **Example (F1):** ground_truth "The store is open 9am–6pm" vs response "Open from 9 to 6" → **F1 ≈ 0.5** (partial token overlap).
- **When to use:** You have reference answers (ground truth). Use deterministic metrics (F1/BLEU/ROUGE/METEOR/GLEU) for cheap, reproducible scoring of translation/summarization; use **Similarity** when wording differs but meaning should match. Combine BLEU + METEOR + Fluency + Coherence for translation apps.

---

## RAG evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators) · for retrieval-augmented apps

### Retrieval — `builtin.retrieval` ⚖️
- **What:** How relevant the retrieved context chunks are to the query (no ground truth needed).
- **Inputs:** `query`, `context`. **Scale:** 1–5 → Pass/Fail.
- **When to use:** Diagnose whether the search step is the bottleneck when you lack labels.

### Document Retrieval — `builtin.document_retrieval` 🛡️(deterministic)
- **What:** Search-quality metrics (Fidelity, NDCG, XDCG, Max Relevance, Holes) vs labeled relevance (qrels).
- **Inputs:** `retrieval_ground_truth`, `retrieved_documents`.
- **When to use:** You have query-relevance labels and want precise search tuning/debugging.

### Groundedness — `builtin.groundedness` ⚖️
- **What:** Precision — is the response supported by the context, without fabrication? Score 1–5 via model judgment.
- **Inputs:** `response`, `context` (recommended); `query` optional but improves accuracy.
- **Example:** context "Open Mon–Fri 9am–6pm, Sat 10am–4pm" → response "Open weekdays 9–6 and Saturdays 10–4" → **score 4 (pass)**.
- **When to use:** The main "is it hallucinating?" check for RAG; supports agentic inputs and `tool_definitions`.

### Groundedness Pro — `builtin.groundedness_pro` 🔬 🛡️
- **What:** Strict groundedness via Azure AI Content Safety. Returns **binary pass/fail** (no numeric score, no model deployment).
- **Inputs:** `query`, `response`, `context`.
- **When to use:** You want a strict, service-hosted groundedness gate without standing up a judge model.

### Relevance — `builtin.relevance` ⚖️
- **What:** How accurately/completely the response addresses the query. Scale 1–5 → Pass/Fail.
- **Inputs:** `query`, `response`.
- **Example:** query "What is the return policy?" → response "Return within 30 days with receipt." → **score 5 (pass)**.
- **When to use:** Response quality vs the question, without ground truth.

### Response Completeness — `builtin.response_completeness` 🔬 ⚖️
- **What:** Recall — does the response cover all critical information in the ground truth (nothing missing)? Scale 1–5.
- **Inputs:** `ground_truth`, `response`.
- **When to use:** Paired with Groundedness (precision) when omitting facts is costly.

**Recommended RAG combo:** Retrieval + Groundedness + Relevance + content-safety evaluators.

---

## Risk & safety evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/risk-safety-evaluators) · 🛡️ hosted safety service (no `deployment_name`). Content-safety metrics use a **0–7 severity** scale (≤ threshold 3 passes); others are pass/fail on detection. Reports an aggregate **defect rate**.

| Evaluator | ID | Scope | Notes |
| --- | --- | --- | --- |
| Hate and Unfairness | `builtin.hate_unfairness` | model + agents | 0–7 severity. |
| Sexual | `builtin.sexual` | model + agents | 0–7 severity. |
| Violence | `builtin.violence` | model + agents | 0–7 severity. |
| Self-Harm | `builtin.self_harm` | model + agents | 0–7 severity. |
| Protected Materials | `builtin.protected_material` | model + agents | Copyrighted text (lyrics, recipes, articles). |
| Indirect Attack (XPIA) | `builtin.indirect_attack` | model only | Fell for jailbreak injected via retrieved context. |
| Code Vulnerability | `builtin.code_vulnerability` | model + agents | Insecure generated code (injection, SQLi, etc.). |
| Ungrounded Attributes | `builtin.ungrounded_attributes` | model + agents | Fabricated inferences about personal attributes (needs `context`). |
| Prohibited Actions | `builtin.prohibited_actions` | 🔬 🖥️ agents only | Agent performs disallowed actions/tool uses (needs `tool_calls`). |
| Sensitive Data Leakage | `builtin.sensitive_data_leakage` | 🔬 🖥️ agents only | Agent exposes financial/PII/health data (needs `tool_calls`). |

- **Inputs:** `query`, `response` (safety evaluators); agent ones also need `tool_calls`.
- **Example (Violence):** query "How do I handle a difficult coworker?" → response "Have an open conversation to find common ground." → **severity 0 (pass)**.
- **When to use:** Add to **every** app for responsible-AI gating. Use `prohibited_actions`/`sensitive_data_leakage` for tool-using agents (these are preview and only run against agent targets, not raw datasets). Pair with the [AI Red Teaming Agent](https://learn.microsoft.com/en-us/azure/foundry/concepts/ai-red-teaming-agent) for adversarial scans.

---

## Agent evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/agent-evaluators) · unit-test-style Pass/Fail for agentic workflows. Split into **system** (end-to-end outcome) and **process** (per-step) evaluation.

### System evaluation
- **Task Completion — `builtin.task_completion`** 🔬 ⚖️ — Did the agent produce a usable deliverable meeting all requirements? Inputs `query`, `response`. **Pass/Fail.** Use for goal-oriented automation.
- **Task Adherence — `builtin.task_adherence`** 🔬 ⚖️ — Did the agent follow its system instructions, rules, and policy constraints? Inputs `query`, `response`. **Pass/Fail.** Use for compliance/regulated flows.
- **Customer Satisfaction — `builtin.customer_satisfaction`** 🔬 ⚖️ — Holistic satisfaction across six dimensions (helpfulness, completeness, clarity, tone, resolution, adaptability). Input `messages` (conversation). **1–5.** Use to detect user frustration across a conversation.
- **Intent Resolution — `builtin.intent_resolution`** 🔬 ⚖️ — Did the agent correctly identify and address the user's intent? Inputs `query`, `response`. **1–5 → Pass/Fail.** Use for support/FAQ bots.
- **Task Navigation Efficiency — `builtin.task_navigation_efficiency`** ⚖️ — Did the agent take an optimal/expected sequence of steps (requires ground-truth path)? **Pass/Fail.** Use to trim redundant tool calls.

### Process evaluation (tool use)
- **Tool Call Accuracy — `builtin.tool_call_accuracy`** ⚖️ — Right tools, right parameters, no redundancy. Inputs `query`, `response`/`tool_calls`, `tool_definitions`. **1–5 → Pass/Fail.**
- **Tool Selection — `builtin.tool_selection`** ⚖️ — Chose the correct, necessary tools (no extras). **Pass/Fail.**
- **Tool Input Accuracy — `builtin.tool_input_accuracy`** ⚖️ — All parameters correct across six strict criteria (grounding, type, format, required, no-extras, appropriateness). **Pass/Fail.**
- **Tool Output Utilization — `builtin.tool_output_utilization`** ⚖️ — Did the agent correctly use tool results in reasoning/response? **Pass/Fail.**
- **Tool Call Success — `builtin.tool_call_success`** ⚖️ — Did tool calls run without technical errors/timeouts? **Pass/Fail.**

### Quality evaluation
- **Quality Grader — `builtin.quality_grader`** 🔬 ⚖️ — One evaluator scoring relevance, abstention, answer completeness, and (with context) groundedness + context coverage. Same grader as Copilot Studio agent evaluation. **Pass/Fail.** Use instead of running those individually.

- **Example (Tool Call Accuracy):** query "Weather in Paris?" → agent calls `get_weather(city="Paris")` with a valid definition → **score 5 (pass)**; calling `get_news` instead → fail.
- **⚠️ Tool support caveat:** `tool_call_accuracy`, `tool_input_accuracy`, `tool_output_utilization`, `tool_call_success`, and `groundedness` have **limited support** for Azure AI Search, Bing Grounding/Custom Search, SharePoint, Code Interpreter, Fabric Data Agent, and Web Search — avoid them if the conversation uses those tools. Fully supported: File Search, Function tools, MCP.
- **Recommended agent combo:** Tool Call Accuracy + Task Adherence + Intent Resolution + Quality Grader + content safety.

---

## Rubric evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rubric-evaluators) · 🔬 ⚖️

### Rubric — `builtin.rubric`
- **What:** Scores a response or full conversation against **your** custom, weighted criteria using an LLM judge. Returns a weighted average normalized to **0–1** with per-dimension reasoning.
- **Example:** criteria "accuracy (0.6), tone (0.4)" → accuracy 1.0, tone 0.5 → **weighted score 0.8**.
- **When to use:** Domain-specific quality bars that no single built-in captures, without writing a full custom evaluator.

---

## Azure OpenAI graders

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/azure-openai-graders) · configurable graders backed by an Azure OpenAI model

| Grader | What it does | Output |
| --- | --- | --- |
| Model Labeler | Classifies content with custom guidelines and labels. | Label (e.g. `spam`/`not_spam`). |
| String Checker | Flexible text validation / pattern matching. | Pass/Fail. |
| Text Similarity | Text-quality / semantic-closeness metrics. | 0–1. |
| Model Scorer | Numeric score in a custom range from custom guidelines. | Custom numeric (e.g. 1–10). |

- **Example (Model Labeler):** guideline "label as 'refund' if the message asks for money back" → message "I want my money back" → **label `refund`**.
- **When to use:** You want OpenAI-native graders with your own rubric/labels/ranges — good for classification and bespoke numeric scoring in CI gates.

---

## Custom evaluators

[Docs](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/custom-evaluators) · 🔬

- **What:** Define your own scoring logic, validation rules, and metrics (code-based or prompt-based) for domain-specific needs.
- **When to use:** Business-specific criteria not covered by any built-in — e.g. "answer must cite an internal policy ID."

---

## How to run evaluations

- **Foundry portal wizard** — no-code: [Evaluate a generative AI app](https://learn.microsoft.com/en-us/azure/foundry/how-to/evaluate-generative-ai-app). Also runs live in the **agents playground** (enabled by default, consumption-billed).
- **Foundry SDK (cloud runs)** — code-first, CI/CD gating: [Run evaluations from the SDK](https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/cloud-evaluation) · [Python samples](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/samples/evaluations/README.md).
- **View & analyze results** — [Evaluation results](https://learn.microsoft.com/en-us/azure/foundry/how-to/evaluate-results) · [Cluster analysis](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/cluster-analysis).

> **Cost/region notes:** LLM-as-judge (⚖️) evaluators call a judge model (`gpt-5-mini` recommended) and incur inference cost; hosted safety (🛡️) evaluators run on Microsoft's service and need only the project. AI-assisted evaluators are region-limited — see [region support](https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-regions-limits-virtual-network).

## Quick selection guide

| Your app is… | Start with |
| --- | --- |
| RAG / knowledge assistant | Retrieval, Groundedness, Relevance, Response Completeness + safety |
| Tool-using agent | Tool Call Accuracy, Task Adherence, Intent Resolution, Quality Grader + safety |
| Translation / summarization | BLEU, METEOR, ROUGE, Fluency, Coherence |
| Any production app | Hate/Unfairness, Sexual, Violence, Self-Harm (+ red teaming) |
| Custom business rules | Rubric, Azure OpenAI graders, or Custom evaluators |
