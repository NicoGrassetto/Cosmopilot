# Weather Agent

## Business problem

People need timely weather information to plan travel, work, and outdoor activities. Weather changes quickly, place names can be ambiguous, and severe-weather terminology is easy to misunderstand. Answers based on stale knowledge or unsupported assumptions can lead to poor or unsafe decisions.

## Solution

The Weather Agent uses web search for every current-conditions or forecast request. It prefers authoritative meteorological sources and preserves their citations instead of inventing weather data.

The agent:

- Clarifies a missing or ambiguous location before reporting a location-specific forecast.
- Reports the location, conditions, temperature, and forecast period.
- Clearly separates observed conditions from forecasts.
- Includes relevant official alerts and warnings when available.
- Explains whether an alert is a watch, warning, or advisory.
- Places immediate protective actions before general forecast details when hazardous weather is present.
- States uncertainty when an alert's timing or affected area is unclear.

The agent supports on-demand questions. The repository also defines a disabled routine that can request a Brussels weather report on weekday mornings.

## SDK requirements and registration

[create_weather_agent.py](create_weather_agent.py) requires Python 3.10 or newer, `azure-ai-projects==2.7.0`, and `openai==3.0.0`. The repository-wide requirements still pin older SDK versions; apply the required dependency updates before running this agent.

The script reads `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_DEPLOYMENT_NAME` from the process environment. It uploads [the safety skill](skills/severe-weather-safety/SKILL.md) through Foundry's preview `create_from_files` API, then attaches the returned immutable skill version when creating the agent. Each execution creates a new skill version and agent version without changing the skill's shared default.

Web Search is required programmatically on every request, including clarification turns. The registered Foundry agent name remains `weather-agent`; only the source directory is named `weather_agent`.

## Some examples of interactions

### Check current conditions

**User:** What is the current weather in Brussels, Belgium?

**Agent:** Searches authoritative sources and reports the current conditions, temperature, observation context, and citations.

### Request a forecast

**User:** What will the weather be in Tokyo tomorrow? Give temperatures in Celsius.

**Agent:** Returns a cited forecast for Tokyo, clearly labeled with the forecast period and temperatures in Celsius.

### Resolve an ambiguous request

**User:** Will it rain in Springfield tomorrow?

**Agent:** Asks which Springfield the user means before retrieving a forecast.

### Check a severe-weather alert

**User:** Is there a flash flood warning for Austin, Texas, and what should I do if one is active?

**Agent:** Checks official sources. If a warning is active, it leads with the affected area, severity, timing, issuing authority, and immediate protective actions, then provides supporting forecast details and citations.