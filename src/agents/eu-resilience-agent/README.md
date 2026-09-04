# EU Cross-Agency Coordination Agent

## Business problem

EU leaders need to identify the countries and risk domains that require attention across climate, health, food systems, and financial resilience. The supporting evidence can be fragmented, differently classified, or synthetic, which makes it difficult to compare priorities and turn analysis into a governed cross-agency response.

Leaders also need a clear review and approval process. A recommendation should not become an operational coordination case without an explicit human decision.

## Solution

The EU Cross-Agency Coordination Agent turns a curated EU27 resilience snapshot into concise, evidence-grounded recommendations for senior leaders. It can:

- Rank country priorities and explain the strongest risk drivers.
- Retrieve a country-level evidence package and distinguish source-derived, derived, and synthetic values.
- Evaluate the evidence against a deterministic coordination playbook.
- Identify proposed lead and participating agencies based on the playbook result.
- Generate a downloadable country briefing or EU priority report in DOCX format.
- Prepare a complete decision card with a `Pending approval` status.
- Open a mock coordination case only after the user explicitly approves the matching pending decision.

The agent treats its tools as the source of truth, reports uncertainty and data limitations, and presents future impacts as plausible scenarios rather than forecasts. Its evidence is a static demonstration snapshot at country level, not a source for public warnings, financial decisions, funding allocations, or emergency action.

## Some examples of interactions

### Identify priorities

**User:** Where should EU leadership focus today?

**Agent:** Retrieves the ranked EU27 snapshot, presents the highest-priority countries and their strongest risk drivers, and notes the snapshot date and limitations.

### Assess a country

**User:** Does Spain meet the criteria for cross-agency coordination?

**Agent:** Retrieves Spain's current evidence package, evaluates it against the coordination playbook, and explains which criteria are met, not met, or indeterminate.

### Prepare a decision

**User:** Prepare a coordination action for Spain.

**Agent:** Produces a decision card containing the supporting evidence, classifications, playbook result, proposed agencies, review steps, confidence, and limitations. It leaves the card at `Pending approval` and does not execute it.

### Approve an action

**User:** Approve and open the pending Spain coordination case.

**Agent:** Verifies that the request matches the pending decision card, opens the mock case once, and returns the business receipt supplied by the execution tool.

### Generate a briefing

**User:** Create a DOCX briefing for the five highest-priority countries.

**Agent:** Retrieves the current five-country ranking, generates the report, summarizes its scope, and directs the user to the application's trusted download card.