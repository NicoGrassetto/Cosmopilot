# Evaluation Framework

Reusable evaluation infrastructure for all Foundry agents in this repo.

## Structure

```
evaluations/
├── evals/                    # Shared evaluators (the core)
│   ├── suites.py             # All 28 built-in evaluators grouped into composable bundles
│   ├── tone.py               # Custom: prompt-based tone checker
│   ├── domain_accuracy.py    # Custom: code-based fact validation
│   └── response_format.py   # Custom: structural format checks
│
├── agents/                   # Pluggable agent targets
│   ├── base.py               # AgentTarget protocol
│   └── foundry_agent.py      # Adapter for Foundry-deployed agents
│
├── config/                   # Configuration (no secrets!)
│   ├── model_config.yaml     # Judge model settings
│   ├── project_config.yaml   # Foundry project connection
│   └── thresholds.yaml       # Pass/fail thresholds per evaluator
│
├── datasets/
│   ├── shared/               # Reusable across all agents (safety prompts, etc.)
│   └── per_agent/            # Agent-specific ground truth
│
├── simulators/               # Synthetic + adversarial data generation
│   ├── synthetic_gen.py      # Multi-turn conversation generator
│   └── adversarial_gen.py    # Attack prompt generator
│
├── redteam/                  # PyRIT-based red teaming
│   └── runner.py             # Automated attack batteries
│
├── runner.py                 # CLI entrypoint: pick agent + suite → run
├── report.py                 # Aggregate results → markdown report
├── results/                  # Gitignored run outputs
└── pyproject.toml            # Dependencies
```

## Quick Start

```bash
cd evaluations
pip install -e .

# Run quality + safety evaluation against an agent
python runner.py --agent adventure-works --suites quality,safety

# Run everything
python runner.py --agent adventure-works --suites all

# Run with a specific dataset
python runner.py --agent my-agent --suites agentic --dataset datasets/per_agent/my-agent.jsonl

# Generate report from results
python report.py results/
```

## Adding a New Agent

1. Create a JSONL dataset at `datasets/per_agent/<agent-name>.jsonl`
2. Run: `python runner.py --agent <agent-name> --suites quality,safety`

No evaluation code changes needed — the framework reuses everything.

## Adding a Custom Evaluator

1. Create `evals/my_evaluator.py` with a callable class
2. Export it from `evals/__init__.py`
3. (Optional) Add it to a suite in `suites.py` or use standalone in the runner

## Environment Variables

```bash
AZURE_AI_PROJECT_ENDPOINT=https://...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_SUBSCRIPTION_ID=...
AZURE_RESOURCE_GROUP=...
AZURE_AI_PROJECT_NAME=...
```
