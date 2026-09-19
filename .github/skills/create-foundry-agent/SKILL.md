---
name: create-foundry-agent
description: 'Create Microsoft Foundry agents with the Python SDK. Use whenever the user asks to create an agent, add an agent, build an agent, scaffold an agent, implement a new agent, or create a weather or other domain agent in Cosmopilot. Enforces agent folder and file naming, required Markdown prompt and SKILL.md skill folders, verified SDK release selection, complete SDK calls with documented parameters, and standard-library lifecycle logging. Not for VS Code custom agent definitions in .agent.md files.'
argument-hint: 'Agent name, purpose, model deployment, and required Foundry features'
user-invocable: true
disable-model-invocation: false
---

# Create a Microsoft Foundry Agent

Apply this workflow to every request to create a Microsoft Foundry application agent in this repository. Creating code does not authorize provisioning resources, deploying an agent, or running live integration tests.

## Establish Requirements

1. Read the repository instructions, dependency pins, and the nearest relevant agent implementation and tests.
2. Identify the agent name, purpose, model deployment, instructions, tools, and explicitly requested Foundry features. Reuse supplied configuration; ask only for missing information that blocks implementation. Do not invent deployment names or endpoints.
3. Preserve existing local changes. Limit work to the requested agent, necessary dependencies, and related tests or documentation.

## Folder and File Naming

- Create new agents under repository-root `agents/`, not `src/agents/` or `.github/agents/`.
- Give each agent its own directory: `agents/<agent_name>_agent/`. Normalize the base name to lowercase snake_case and append `_agent` once.
- Name Python files `<action>_<what>.py`. For example, the weather agent creation script is `agents/weather_agent/create_weather_agent.py`.
- Every new agent must have both a `prompts/` directory containing Markdown prompt files and a `skills/` directory containing its agent skills. These directories are mandatory, not optional supporting assets.
- Store prompts as `prompts/<prompt_name>.md` and each skill as `skills/<skill-name>/SKILL.md`. The skill filename is exactly `SKILL.md`, uppercase and singular, not `skills.md` or `skill.md`.
- Add supporting tools or assets inside the agent or individual skill directory only when needed.
- Existing agents under `src/agents/` are legacy locations for this workflow. Do not move or rename them unless explicitly requested.

Required layout:

```text
agents/
	<agent_name>_agent/
		create_<agent_name>_agent.py
		prompts/
			instructions.md
		skills/
			<skill-name>/
				SKILL.md
```

## Prompt and Skill Files

- Put authored agent instructions and prompt templates in `.md` files under `prompts/`, rather than embedding them as long Python strings. Include at least one meaningful prompt and one task-relevant skill; do not create empty placeholder documents to satisfy the layout.
- Load prompt contents as UTF-8 text and pass the contents to the SDK. Resolve prompt and skill paths relative to the creation script using `Path(__file__).resolve().parent`, not the process working directory.
- Follow the [Agent Skills specification](https://agentskills.io/specification). Each skill directory must contain a `SKILL.md` with YAML frontmatter delimited by `---`, followed by a nonempty Markdown body containing actionable instructions.
- Require `name` and `description` in the frontmatter. The skill name must match its parent directory, be 1-64 characters, and use lowercase letters, digits, and hyphens without leading, trailing, or consecutive hyphens. Agent directory names remain snake_case; skill directory names use the specification's hyphenated convention.
- Keep the description between 1 and 1024 characters and explain both what the skill does and when to use it. Keep the body focused on the skill's procedure, relevant examples, and edge cases.
- Optional `scripts/`, `references/`, and `assets/` belong inside the individual skill directory. Use relative references and verify that the referenced resources exist.
- These are runtime agent assets, not Copilot customizations under `.github/skills/`. Use the selected SDK release's documented skill import and attachment mechanism; creating local folders alone does not make their skills available to the Foundry agent.

## Select and Verify the SDK Release

1. Use the Microsoft Foundry SDK for Python: `azure-ai-projects`, `azure.ai.projects.AIProjectClient`, and its typed models. Use `DefaultAzureCredential` for authentication. Do not substitute the legacy `azure-ai-agents` package or a different agent framework.
2. At execution time, check the [published package releases](https://pypi.org/project/azure-ai-projects/#history) and [SDK release notes](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/ai/azure-ai-projects/CHANGELOG.md). Select the latest stable, non-yanked release by default. Do not assume the repository pin, installed version, or a remembered version is the latest.
3. Check the documentation for each explicitly requested feature. A preview feature may already be included in the stable package; do not choose a prerelease solely because the feature is labeled preview.
4. If an explicitly requested feature requires another release, notify the user before implementation. State the selected version, why the latest stable release cannot provide the feature, and any preview or compatibility implications. Use a release verified to support that feature, not a guessed version.
5. Compare the selected version with `requirements.txt` and the repository-root `.venv`. When a version change is needed, update the exact dependency pin and any affected documented version or SDK contracts. Validate the complete dependency resolution, not just the new import. Avoid unrelated dependency upgrades.
6. If release or feature availability cannot be verified, disclose the limitation and obtain the missing information. Never claim an unverified version is the latest stable release.

## Fully Specify SDK Calls

Apply these rules to SDK constructors, model construction, and method calls, including `client.agents.create_version`:

1. Verify the function signature for the selected SDK version using its API reference and installed SDK inspection, such as Pylance, `inspect.signature`, or SDK source. Inspect overloads and documented keyword arguments when the runtime signature is generic.
2. Pass every concrete public parameter in the applicable signature, including optional parameters whose defaults remain unchanged. Prefer explicit keyword arguments; preserve positional-only parameters where required. Do not pass implicit `self` or `cls` arguments.
3. Put one argument on each line. Add an inline comment to the right of every argument explaining in one sentence what that parameter controls. This explicit requirement also applies to nested SDK model constructors and takes precedence over a general preference to avoid inline comments.
4. Use meaningful values or the documented defaults. Use `None` only where its documented semantics are correct; do not replace omission or sentinel behavior with null values. If a parameter cannot safely be supplied explicitly, explain that limitation to the user instead of guessing.
5. Select one valid overload. Do not combine mutually exclusive arguments or alternative request-body forms merely to list every overload's parameters. Explain any resulting exclusions to the user.
6. `*args` and `**kwargs` are variadic containers, not an enumerable parameter list. Include all documented, named options supported by the selected call form, but do not invent arguments or add arbitrary transport options. Report any remaining signature uncertainty before generating the call.
7. Keep arguments visible at the call site. Do not hide them in unpacked dictionaries or shared wrappers, and do not use ellipses or placeholder arguments to suggest an incomplete call is finished.

## Logging

Follow the lifecycle logging conventions used by the repository's agent helpers:

- Use Python's standard-library `logging` module and define `logger = logging.getLogger(__name__)` at module scope. Do not add a logging dependency or shared logging wrapper.
- Configure logging once in the CLI's `main()` using `logging.basicConfig`, `level=logging.INFO`, and `format="%(asctime)s %(levelname)-8s %(name)s | %(message)s"`. Do not configure the root logger or add handlers when a reusable module is imported.
- Log an INFO message before each external operation and another after it succeeds. Include the operation and safe key/value context such as `name=%s`, `model=%s`, `version=%s`, `draft=%s`, or `tool_count=%d`, as applicable. Use actual result identifiers in completion messages.
- Use lazy logging arguments, for example `logger.info("Creating agent version name=%s kind=%s draft=%s", agent_name, definition.kind, bool(draft))`. Do not use f-strings, string concatenation, or eagerly formatted strings in logging calls.
- Capture `started = perf_counter()` before the operation and include `duration_ms=%.0f` with `(perf_counter() - started) * 1000` in the success log. Log success only after the operation, poller, or stream has completed. For lists and streams, report final item or byte counts instead of logging every item or chunk.
- At the CLI boundary, catch failures with `logger.exception` inside the exception handler, include safe command or agent context, and exit nonzero with `raise SystemExit(1)`. Let reusable helpers propagate exceptions without swallowing them or logging the same failure at every layer.
- Keep logging on stderr so stdout remains available for JSON or other command results. Do not replace structured command output with logging.
- Never log credentials, tokens, authorization headers, environment dumps, full prompts, user messages, or complete request/response payloads. Prefer identifiers, counts, and presence flags over potentially sensitive content; do not enable SDK HTTP-body logging by default.

## Implement and Validate

- Use explicit context managers at each SDK call site for credentials and clients; do not introduce a shared context-manager helper.
- Read configuration from environment variables in line with the repository conventions. Do not hard-code credentials or real endpoint values, and do not assume `.env` is automatically loaded.
- Enable preview behavior only as documented for the selected SDK version. In the current API, `client.beta.*` already opts into preview behavior; preview features exposed through stable clients require `allow_preview=True`.
- Reuse nearby testing patterns and mocks. Prefer focused, offline checks; run live Azure operations or integration tests only when explicitly authorized.
- Cover start/success logging, elapsed-time fields, and CLI failure logging in focused offline tests using existing mocks and pytest's `caplog` where appropriate. Check that logs do not contaminate stdout or disclose sensitive payloads.
- Before any live SDK call, validate that both required directories contain their expected files, prompts load from `.md` files independently of the working directory, and every skill has the exact `SKILL.md` filename, valid frontmatter, nonempty instructions, and resolvable resource references. Verify skill import and attachment with mocked SDK calls.
- Check folder and file names, imports, the selected SDK signature, complete argument lists, and per-argument inline comments. Syntax checks alone do not verify signature compatibility.
- Run focused tests from the repository root using `.venv`. Set `PYTHONPATH=src` when tests import the existing source modules. If dependencies changed, validate the full requirements resolution and run `python -m pip check` in that environment.
- In the completion summary, report created files, the exact SDK version and any release exception, and the checks performed. Disclose checks that could not be run.