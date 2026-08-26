---
name: frontend-javascript-htmx
description: 'Build and modify Cosmopilot frontend interfaces with JavaScript and HTMX. Use for frontend pages, browser interactions, forms, requests, and partial-page updates.'
---

# Frontend Development

Use JavaScript and HTMX for frontend development in this repository.

## Technology Choices

- Use plain JavaScript for browser-side behavior and client-only state.
- Use HTMX for server-driven interactions, requests, and HTML fragment updates.
- Prefer HTMX attributes over custom JavaScript when HTMX can express the interaction clearly.
- Do not introduce TypeScript or a JavaScript frontend framework unless the task explicitly requires it.
- Preserve the existing no-build frontend structure unless a requested change requires otherwise.
- Keep all frontend markup in one HTML file and all frontend styles in one CSS file.
- Extend those files instead of splitting markup or styles across additional files unless the task explicitly requires it.

## Workflow

1. Review the existing HTML, CSS, JavaScript, and server endpoint involved.
2. Implement request-driven interactions with HTMX attributes.
3. Return focused HTML fragments from endpoints used by HTMX.
4. Add JavaScript only for behavior that is client-only or not clearly handled by HTMX.
5. Verify the interaction with JavaScript enabled and ensure controls remain accessible.