---
name: create-sdk-tests
description: 'Create pytest integration tests for SDK public-API regressions, without fixtures or private methods. Use whenever introducing a new SDK client module or nested operation group under client.*, adding or changing SDK method calls, upgrading the SDK, or requesting SDK test coverage, public method discovery, or parameter coverage. Produces one test_<module_path>.py file per operation group, one test_<public_method> function per public method, and an explicit API inventory. Applies to client.agents and any other client.* group, not just methods already used by the application.'
argument-hint: 'SDK client module or operation group, for example client.agents'
---

# SDK Regression Integration Tests

## Purpose

Make the installed SDK's public API readable while detecting SDK and service regressions. Test the SDK directly against real services, not only the application's wrappers. Create only pytest integration tests: no unit tests, mocks, fixtures, or private methods.

## When to Use

- Whenever application code starts using a new SDK module or operation group anywhere under `client.*`, including nested groups.
- When adding or changing public SDK method calls or parameters in an already covered group.
- When an SDK dependency changes, to review and update the affected public API contracts.
- When asked to create SDK tests, enumerate public methods, or improve parameter coverage.

## 1. Verify the SDK Surface

1. Read the repository instructions, dependency pins, pytest configuration, and the nearest relevant tests. Preserve existing local changes.
2. Use the repository-root `.venv`. Verify the installed package version against `requirements.txt`; do not silently upgrade the SDK or guess APIs from another release.
3. Identify the concrete SDK client and full operation-group path used by the application. For Cosmopilot this is normally `azure.ai.projects.AIProjectClient`, but this workflow applies to any SDK client used in the repository.
4. Inspect the installed group's public methods using `inspect`, including public inherited methods. Inspect `inspect.signature`, `typing.get_overloads`, public docstrings, and version-matched official SDK documentation. Follow applicable Python fact-grounding guidance. Introspection must not issue service requests.
5. Inventory **all** public methods exposed by that group, not just those the application currently calls. Private methods are not allowed: never call or test SDK methods or attributes beginning with `_`, including private operation groups or transport internals. Do not add private helper methods or functions to the suite. Nested public operation groups are not methods; apply this workflow separately when they are used.
6. Enumerate the parameters of every public overload, including positional-only, keyword-only, optional, and documented keyword arguments accepted through `**kwargs`. Exclude implicit receivers such as `self` or a classmethod's receiver. A public response callback named `cls` is still a parameter, not a receiver.

An arbitrary `**kwargs` container is not a finite parameter list. Resolve its documented supported keywords from the installed SDK and official references; record that boundary explicitly. Do not invent keywords or treat passing an empty dictionary as coverage. Do not substitute private transport settings for public method parameters.

## 2. Use One File per SDK Operation Group

- Put the suite in `tests/test_<module_path>.py`, removing the `client.` prefix and replacing remaining dots with underscores. For example, `client.agents` maps to `tests/test_agents.py`; `client.<parent>.<module>` maps to `tests/test_<parent>_<module>.py`. Use this prefix naming pattern for all future SDK suites.
- If different SDK clients expose the same path, qualify the filename with the SDK name and record the complete path in the file.
- Reuse an existing matching suite. Do not rename unrelated legacy `test_*.py` files or duplicate existing integration coverage.
- Use pytest's standard `test_*.py` discovery; do not add a custom suffix naming pattern.
- Define exactly one top-level test function per public method: `def test_<public_method_name>(...):`. Keep the actual SDK method invocation visible in that function.
- Use `@pytest.mark.parametrize` with descriptive case IDs to cover variations within that one function. Do not split parameter cases into differently named test functions or hide methods behind a generic smoke-test loop.
- Set `pytestmark = pytest.mark.integration` at module scope. Every collected test must call a real service.
- Do not define or consume pytest fixtures, including built-in fixtures such as `request`, `tmp_path`, `monkeypatch`, or `capsys`. Do not add `conftest.py`, `usefixtures`, autouse fixtures, indirect parametrization, or setup/teardown hooks as substitutes.
- Keep setup, SDK calls, assertions, and cleanup inside each test function. Only direct `@pytest.mark.parametrize` values may be injected as test arguments. Use standard-library context managers such as `tempfile.TemporaryDirectory` when temporary files are needed.

## 3. Make the File an API Reference

Start the file with a module docstring identifying the SDK package, verified version, full client path, official reference URLs, and required environment variable names. Never include real endpoint values or credentials.

Include a compact inventory in that same file with one row per public method:

| Public Method | Test Function | Parameters and Overloads | Cases and Assertions | Coverage Gaps |
| --- | --- | --- | --- | --- |

Populate the inventory with verified names, required and optional parameters, defaults, and overload alternatives. Explain what each method does briefly in its test docstring. Keep the inventory beside the tests rather than creating a separate documentation tree.

Record the public method and parameter contract as readable documentation or explicit module-level data, including parameter kinds, defaults, and overload alternatives. Compare it with the installed SDK during authoring and offline validation, and check that every inventoried method has its named test function.

Do not implement that authoring check as a pytest fixture, private helper, or contract-only pytest test. The generated pytest suite must contain integration tests only. Review intentional SDK changes before updating the inventory; do not silently regenerate the expected contract at test runtime.

## 4. Exercise Every Public Parameter

For each method's single test function:

1. Exercise a minimal valid call with all required parameters and assert the documented result or side effect.
2. Exercise every optional parameter explicitly with a meaningful non-default value where supported. Merely passing `None`, the default, or an empty value everywhere is not coverage.
3. Cover each public overload and mutually exclusive argument shape with separate parametrized cases. Do not pass incompatible options together just to fit every parameter into one invocation.
4. Map each parameter and case to an observable assertion. Check returned identifiers, values, persisted state, filters, metadata, or documented error behavior as appropriate. A call that merely does not raise is insufficient.
5. Cover relevant accepted boundaries and documented validation failures where they distinguish the parameter's behavior. Exhaustive Cartesian products are unnecessary, but no exposed parameter may be silently omitted.
6. Consume paged and streaming results so deferred service failures are observed. Await asynchronous operations and use SDK pollers with bounded timeouts for long-running operations. Verify persisted effects for methods that return no value.

Use typed SDK models and explicit arguments consistent with the repository. Test documented alternative body formats when they are public overloads. Each test creates its own prerequisites inline, runs independently, and does not rely on another test having created or deleted something.

If a method, overload, or parameter cannot be exercised because of permissions, missing features, unavailable resources, or unsafe side effects, report the exact gap and prerequisite. Coverage remains incomplete. Do not use placeholders, unconditional `xfail`, broad exception swallowing, or skipped service failures to claim completion.

## 5. Use Real Services Safely

- Call the real SDK method on the configured service. No mocked clients, patched SDK calls, fake endpoints, or recorded-response playback count as integration coverage.
- Obtain configuration from the environment. Cosmopilot uses `DefaultAzureCredential`; its modules do not automatically load `.env`. Use the selected azd environment or explicitly exported values as described in the repository instructions.
- Use explicit credential and client context managers inside each test. Do not introduce shared fixture or context-manager abstractions to remove repeated `with` blocks.
- For Foundry preview features on stable clients, use `allow_preview=True` where required. Calls through `client.beta.*` already opt into preview behavior. Preserve the pinned SDK's actual typed contracts.
- Do not authenticate, create clients, or contact services at module import or pytest collection time. Validate required configuration inside each test and fail with an actionable message if it is absent.
- Use uniquely named disposable resources, for example a `pytest-` prefix plus `uuid4`. Mutating and destructive methods must target resources owned by the current test, not pre-existing user resources.
- Protect resource creation and assertions with `try/finally` inside each test. Track resources as they are created, handle partial setup failures, and clean dependent resources in reverse dependency order. Do not use fixture finalizers.
- Verify cleanup and surface failures. An expected not-found result after the method under test already deleted its resource can be handled specifically; never swallow all cleanup exceptions.
- Keep live cost bounded with minimal resources, small inputs, bounded polling, and existing deployments where read-only use is appropriate. Never log credentials, tokens, connection strings, or sensitive payloads.
- Creating tests is not permission to execute them against Azure. Run live cases only when the user explicitly requests or authorizes live integration validation. Do not provision infrastructure, change RBAC, or alter CI to run live tests without that authorization.

## 6. Validate and Report

1. Run focused syntax and editor diagnostics on changed files.
2. Collect the new suite without making network requests. For example, from the repository root on Windows:

   ```powershell
   $env:PYTHONPATH = "src"
   & .\.venv\Scripts\python.exe -m pytest --collect-only -q tests/test_agents.py
   ```

3. Confirm standard discovery includes the suite, every public method has exactly one test function, every case has the integration marker, and the inventory accounts for every public parameter and overload. Verify there are no fixtures, fixture arguments, private method calls, or private helper functions. Collection alone does not verify the service contract.
4. When live validation is authorized, inject the required environment and run only the relevant suite with `-m integration`. Use the root `.venv` interpreter and `PYTHONPATH=src`; do not run all existing live tests by default.
5. Report the SDK version, covered client path, test file, public methods and parameters covered, validation actually performed, cleanup outcome for live runs, and any coverage gaps. Clearly distinguish tests collected from tests executed against the service.

## Completion Criteria

- A discoverable `test_<module_path>.py` exists for each newly used SDK operation group.
- Every public method has one readable, independent `test_<method>` function marked as integration.
- The suite uses only public SDK APIs and contains no fixtures, private helpers, or unit tests; every test owns its setup and cleanup inline.
- Every public parameter and overload has a concrete case and meaningful assertion, with no unreported gaps.
- The file documents the public API, and offline authoring checks verify the method and parameter inventory against the installed SDK.
- Live execution and resource cleanup have been verified when authorized; otherwise the report explicitly states that service behavior remains unverified.