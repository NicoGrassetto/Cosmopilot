# Adventure Works Trail Guide Agent

## Business problem

Hikers and campers need advice that fits their experience, fitness, route, weather, and available equipment. Generic outdoor recommendations can overlook changing trail conditions, inadequate gear, or a route that exceeds the user's ability, increasing the chance of discomfort, getting lost, or injury.

## Solution

The Adventure Works Trail Guide Agent provides practical, safety-focused hiking and camping guidance. It considers the user's experience and fitness, expected weather and trail conditions, and the demands of the planned activity before making a recommendation.

Its responses provide specific gear guidance, clear safety precautions, and backup options when the preferred plan may not be suitable. The agent is designed to help users prepare and make better choices, not to replace local authorities, official trail notices, or professional medical and emergency advice.

## Implementation

[create_trail_guide_agent.py](create_trail_guide_agent.py) uses `azure-ai-projects==2.7.0` directly, without the shared agent helper module. It creates a stable prompt agent with no tools or runtime skills. The source directory is `trail_guide_agent`; the registered Foundry name remains `trail-guide-agent`.

The [versioned prompt](prompts/v1_instructions.md) is loaded as UTF-8 relative to the script, independently of the working directory. The existing prompt-version metadata and model sampling defaults are preserved. `DefaultAzureCredential` retains its environment-sensitive credential-chain defaults.

Set `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_DEPLOYMENT_NAME` in the process environment and authenticate with Azure before running the creation script. It does not load `.env` automatically. With the repository virtual environment activated, run from the repository root:

```bash
python src/agents/trail_guide_agent/create_trail_guide_agent.py
```

This command creates a remote agent version. Lifecycle logs go to stderr; stdout contains only the created agent's name and version as JSON. Failures exit with status 1.

## Some examples of interactions

### Plan an appropriate hike

**User:** I am new to hiking and can comfortably walk five miles. What kind of trail should I choose this weekend?

**Agent:** Asks for the location and relevant conditions, recommends manageable distance, elevation, and terrain, and provides essential gear, turnaround criteria, and a lower-risk backup option.

### Prepare equipment

**User:** What essential gear do I need for a summer day hike?

**Agent:** Recommends hydration, navigation, sun protection, suitable footwear and clothing, first aid, lighting, food, and emergency supplies, adjusted for the route and forecast.

### Respond to poor conditions

**User:** Thunderstorms are forecast for the afternoon. Can I still do a mountain hike?

**Agent:** Explains the exposure risk, recommends checking official forecasts and trail notices, suggests an early turnaround time or postponement, and offers a safer low-elevation alternative.

### Choose gear for a trip

**User:** Do I need a day pack or a backpacking pack for an overnight hike?

**Agent:** Compares pack capacity and support, then recommends an option based on trip length, required shelter, food, water, weather layers, and total load.