# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in Cosmopilot, please **do not** open a public GitHub issue.

Instead, please report it privately via **GitHub Security Advisories**:

1. Go to [Security Advisories](https://github.com/NicoGrassetto/Cosmopilot/security/advisories)
2. Click "Report a vulnerability"
3. Provide details:
   - Type of vulnerability
   - Location in code (file, line number)
   - Potential impact
   - Suggested fix (if known)

## Response Timeline

- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 1 week
- **Fix & Release:** Within 2-4 weeks depending on severity

## Security Best Practices for Users

### Azure Resources
- Use managed identities instead of connection strings where possible
- Enable authentication via Azure Entra ID
- Keep Cosmos DB public access disabled unless necessary
- Regularly rotate access keys
- Use Azure Firewall or NSG rules to restrict traffic

### API Security
- Store sensitive credentials in Azure Key Vault
- Use HTTPS for all communications
- Validate and sanitize all user inputs
- Implement rate limiting for API endpoints

### Data Protection
- Enable encryption at rest in Cosmos DB
- Use encryption in transit (TLS 1.2+)
- Regularly backup critical data
- Monitor access logs for unusual activity

## Supported Versions

Security updates are provided for:
- Latest release: Full support
- Previous release: 3 months

## Compliance

Cosmopilot is designed with security in mind but is provided as-is. Users are responsible for:
- Configuring Azure resources securely
- Managing access controls
- Monitoring and auditing usage
- Compliance with applicable regulations

## Questions

For non-security questions, use GitHub Discussions or Issues.
