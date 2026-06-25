<h1 align="center">🤖 Cosmopilot</h1>

<p align="center">
  <img src="assets/banner.png" alt="Cosmopilot Banner" width="60%" />
</p>

<p align="center">AI-powered chatbot with real-time operational data and voice capabilities.</p>

<p align="center">
  <a href="LICENSE"><img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-%E2%9D%A4-2ea44f" /></a>
  <a href="https://github.com/NicoGrassetto/Cosmopilot"><img alt="GitHub stars" src="https://img.shields.io/github/stars/NicoGrassetto/Cosmopilot" /></a>
</p>

Cosmopilot is a conversational AI application that combines Azure Cosmos DB for real-time operational data storage with Microsoft Foundry for fast inference and embeddings. It features a lightweight frontend built with Svelte, real-time message synchronization via Cosmos DB change feeds, and integrated voice capabilities.

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
