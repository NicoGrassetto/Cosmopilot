# Support

We want to help you succeed with Cosmopilot! Here's how to get support.

## 📖 Documentation

Start with these resources:

- **[README.md](README.md)** - Project overview and quick start
- **[infra/main.bicep](infra/main.bicep)** - Infrastructure code with detailed comments
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[SECURITY.md](SECURITY.md)** - Security guidelines
- **[ROADMAP.md](ROADMAP.md)** - Planned features and timelines

## 💬 Getting Help

### For Questions
- **GitHub Discussions** - Ask questions and share ideas
- **GitHub Issues** - Report bugs or request features (use templates)
- **Email** - Contact project maintainers for urgent issues

### For Problems

**Deployment Issues:**
1. Check Azure CLI version: `az --version`
2. Verify quotas: `az quota list --scope /subscriptions/<id>/providers/Microsoft.Compute/locations/<region>`
3. Review deployment logs: `az deployment group show --resource-group <rg> --name <deployment>`
4. See troubleshooting in infrastructure code comments

**Frontend Issues:**
1. Check browser console for errors: `F12` or `Cmd+Option+I`
2. Verify Node.js version: `node --version` (18+ required)
3. Clear cache and reinstall: `rm -rf node_modules && npm install`
4. Check frontend README: [frontend/README.md](frontend/README.md)

**Runtime Issues:**
1. Check Azure Portal for resource health
2. Review Application Insights logs (if enabled)
3. Verify Cosmos DB connection string
4. Check firewall/network rules

## 🐛 Reporting Issues

When reporting a bug, include:

- [ ] Description of the problem
- [ ] Steps to reproduce
- [ ] Expected vs. actual behavior
- [ ] Screenshots (if applicable)
- [ ] Environment (OS, Node version, Azure region, etc.)
- [ ] Error messages or logs
- [ ] Version of Cosmopilot

## ✅ Before Opening an Issue

1. Search existing [GitHub Issues](https://github.com/NicoGrassetto/Cosmopilot/issues)
2. Check [FAQ.md](FAQ.md) for common questions
3. Review [SECURITY.md](SECURITY.md) for security concerns
4. Try the troubleshooting steps above

## 🚨 Security Issues

**Do not** open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for private reporting.

## 📞 Direct Contact

For urgent matters or non-public issues:
- DM project maintainers on GitHub
- Include detailed context and reproduce steps

## Community Support

- **Stack Overflow** - Tag `cosmopilot` or `azure-foundry`
- **Azure Forums** - Ask about Azure-specific questions
- **Discussions** - Share use cases and get advice from community

---

Thank you for using Cosmopilot! We're here to help. 🚀
