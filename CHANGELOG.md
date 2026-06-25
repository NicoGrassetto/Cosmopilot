# Changelog

All notable changes to Cosmopilot are documented in this file.

## [Unreleased]

### Added
- Consolidated infrastructure deployment (Cosmos DB + AI Foundry in single main.bicep)
- README with project description and branding
- Repository documentation suite (CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, etc.)

### Planned
- Voice capabilities (speech-to-text and text-to-speech)
- ML evaluation framework integration
- Change feed-based indexing pipeline
- Bootstrap script for operational data
- Frontend chat UI enhancements

## [0.1.0] - 2024-06-25

### Added
- Initial project setup
- Azure infrastructure as code:
  - Cosmos DB account with SQL API
  - AI Foundry Project for model deployments
  - Automated infrastructure deployment script
- Frontend scaffolding with Svelte + Vite
- Project documentation

### Infrastructure
- Cosmos DB: SQL API, Session consistency, 400 RU/s
- AI Foundry: GPT-4o Nano inference, text-embedding-3-nano embeddings
- Supported regions: East US, East US 2, West Europe, UK South, Sweden Central

---

## Version Format

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md with release notes
3. Create git tag: `git tag vX.Y.Z`
4. Push tag and create GitHub Release
5. Announce in project discussions
