<h1 align="center"> Cosmopilot</h1>

<p align="center">
  <img src="assets/banner.png" alt="Cosmopilot Banner" width="60%" />
</p>

<p align="center">A demo of the beautiful things we can achieve when we combine all of what Microsoft Foundry has to offer.</p>

<p align="center">
  <a href="LICENSE"><img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-2ea44f" /></a>
  <a href="LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-2ea44f" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot/codespaces"><img alt="Open in Codespaces" src="https://img.shields.io/badge/Open%20in-Codespaces-fb8c00?logo=github" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NicoGrassetto/Cosmopilot" /></a>
</p>

Cosmopilot is a demo showcasing Microsoft Foundry as your AI platform choice. This repo aims at covering every feature Microsoft Foundry offers (GA and Preview) in a somewhat standardised repo structure drawn from what I've observed at my customers and through the Microsoft documentation and OS IP. This does not reflect in any shape of form what YOU should be doing but merely shows you how Microsoft and other folks organise these things.

> [!WARNING]
> This project is simply a demo of Microsoft Foundry capabilities and is intended solely for exploration and validation purposes. 

---

## Project Structure

```text
Cosmopilot/
├── src/                    # Application code
│   ├── agents/             # Microsoft Foundry agents (one folder per agent)
│   │   ├── browser-assistant/
│   │   ├── deep-research-assistant/
│   │   ├── devops-assistant/
│   │   ├── hr-agent/
│   │   ├── insights-assistant/
│   │   ├── integration-assistant/
│   │   ├── knowledge-assistant/
│   │   ├── orchestrator-assistant/
│   │   └── research-assistant/
│   └── main.py             # Entry point
├── frontend/               # Lightweight Svelte frontend
├── infra/                  # Bicep templates and deployment scripts
├── data/                   # Sample documents and evaluation datasets
│   ├── datasets/           # Evaluation datasets (uploaded to Foundry)
│   └── documents/          # Fake docs indexed into Azure AI Search
├── docs/                   # Tool catalog, evaluations, and roadmaps
├── notebooks/              # Exploratory notebooks
├── tests/                  # Evaluation runner and tests
├── assets/                 # Images used in docs
└── requirements.txt        # Python dependencies
```

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
