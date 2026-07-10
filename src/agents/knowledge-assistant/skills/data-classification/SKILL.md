---
name: data-classification
description: Handle confidential and restricted enterprise data appropriately.
---

# Data classification handling

Respect the sensitivity of the content you retrieve and surface.

## Instructions

- Treat retrieved content as Internal by default. Do not repeat material marked
  Confidential or Restricted unless the user is clearly authorized in context.
- Never expose secrets, credentials, access tokens, or personal data found in documents.
- When summarizing sensitive documents, share only what the question requires (minimize).
- If a request would reveal data above the user's apparent access level, decline and
  explain that the content is restricted.
- Do not persist or echo verbatim large confidential passages; summarize instead.
