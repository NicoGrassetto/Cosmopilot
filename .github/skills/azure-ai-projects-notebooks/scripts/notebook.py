"""Inventory and check notebooks for the azure-ai-projects-notebooks skill.

Run from the repository root with the .venv interpreter:

    python .github/skills/azure-ai-projects-notebooks/scripts/notebook.py inventory client.agents
    python .github/skills/azure-ai-projects-notebooks/scripts/notebook.py check notebooks/agents.ipynb

Both commands work offline: the client is constructed, but no request is ever sent.
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import inspect
import io
import json
import re
import sys
import tokenize
import typing
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
DISTRIBUTION = "azure-ai-projects"
LEARN_URL = (
    "https://learn.microsoft.com/en-us/python/api/azure-ai-projects/"
    "azure.ai.projects.operations.{page}?view={moniker}"
)
SOURCE_URL = (
    "https://github.com/Azure/azure-sdk-for-python/blob/azure-ai-projects_{version}/"
    "sdk/ai/azure-ai-projects/{path}#L{line}"
)
MODULE = r"client(?:\.[a-z][a-z0-9_]*)+"
TITLE = re.compile(rf"# (?P<title>\S.*?): `(?P<module>{MODULE})`")
TITLE_WORDS = range(5, 16)
PARAMETER_DOC = re.compile(r"^:(?:param|keyword)[ \t]+(?:\S+[ \t]+)*?(\w+):(.*(?:\n[ \t]+.*)*)", re.MULTILINE)


class OfflineCredential:
    """Lets the client be constructed; any attempt to authenticate fails."""

    def get_token(self, *scopes: str, **kwargs: typing.Any) -> typing.NoReturn:
        raise RuntimeError("This script never sends requests.")


class Method(typing.NamedTuple):
    name: str
    parameters: list[inspect.Parameter]
    notes: dict[str, str]
    returns: str

    @property
    def preview(self) -> list[str]:
        return [p.name for p in self.parameters if self.notes.get(p.name, "").startswith("(Preview)")]


def fail(message: str) -> typing.NoReturn:
    sys.exit(f"error: {message}")


def pinned_version() -> str:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    pin = re.search(rf"^{re.escape(DISTRIBUTION)}(?:\[[^\]]*\])?==(\S+)", requirements, re.MULTILINE)
    if pin is None:
        fail(f"requirements.txt does not pin {DISTRIBUTION}.")
    try:
        installed = importlib.metadata.version(DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError:
        installed = None
    if installed != pin.group(1):
        fail(
            f"requirements.txt pins {DISTRIBUTION}=={pin.group(1)}, but this interpreter has "
            f"{installed or 'no version'} installed; run `python -m pip install -r requirements.txt` in the .venv."
        )
    return installed


def operations_class(module: str) -> type:
    from azure.ai.projects import AIProjectClient

    if not re.fullmatch(MODULE, module):
        fail(f"`{module}` is not a module path such as `client.agents` or `client.beta.memory_stores`.")
    client = AIProjectClient(
        endpoint="https://offline.services.ai.azure.com/api/projects/offline",
        credential=OfflineCredential(),
    )
    try:
        target: object = client
        for name in module.split(".")[1:]:
            target = getattr(target, name, None)
            if target is None:
                fail(f"`{module}` is not a namespace of AIProjectClient.")
    finally:
        client.close()
    # client.beta.* namespaces are proxies that add the preview header to a real operations object.
    target = getattr(target, "_operation", target)
    if callable(target) or not type(target).__module__.startswith("azure.ai.projects."):
        fail(f"`{module}` is not a namespace of AIProjectClient.")
    return type(target)


def showcase(cls: type, name: str) -> tuple[inspect.Signature, str]:
    """Return the signature a section must pass in full, and the docstring that describes it."""
    for owner in cls.__mro__:
        function = vars(owner).get(name)
        if function is None:
            continue
        overloads = typing.get_overloads(function)
        if overloads:
            # Generated methods take either typed keywords or a raw JSON/bytes `body`; show the typed form.
            typed = [overload for overload in overloads if "body" not in inspect.signature(overload).parameters]
            chosen = (typed or overloads)[0]
            return inspect.signature(chosen), inspect.getdoc(chosen) or ""
        if "body" not in inspect.signature(function).parameters:
            break
    implementation = getattr(cls, name)
    return inspect.signature(implementation), inspect.getdoc(implementation) or ""


def descriptions(docstring: str) -> dict[str, str]:
    """First sentence of every :param: and :keyword: entry of a Sphinx docstring."""
    found = {}
    for match in PARAMETER_DOC.finditer(docstring):
        text = " ".join(match.group(2).split())
        sentence = re.match(r".+?\.(?=\s|$)", text)
        found[match.group(1)] = sentence.group(0) if sentence else text
    return found


def annotation(value: object) -> str:
    if value is inspect.Parameter.empty:
        return ""
    text = value if isinstance(value, str) else inspect.formatannotation(value)
    text = re.sub(r"\b(?:[A-Za-z_]\w*\.)+(?=[A-Za-z_])", "", text).replace("'", "")
    return text if len(text) <= 100 else text[:99] + "…"


def default(parameter: inspect.Parameter) -> str:
    # Required keywords in implementation signatures default to the SDK's bare `object()` sentinel.
    if parameter.default is parameter.empty or type(parameter.default) is object:
        return ""
    return f" = {parameter.default!r}"


def inventory(module: str) -> tuple[str, type, list[Method]]:
    version = pinned_version()
    cls = operations_class(module)
    methods = []
    for name in sorted(n for n, member in inspect.getmembers(cls) if not n.startswith("_") and callable(member)):
        signature, docstring = showcase(cls, name)
        methods.append(
            Method(
                name=name,
                parameters=[
                    p
                    for p in signature.parameters.values()
                    if p.name != "self" and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                ],
                notes=descriptions(docstring),
                returns=annotation(signature.return_annotation),
            )
        )
    if not methods:
        fail(f"`{module}` has no public methods of its own; each child namespace gets its own notebook.")
    return version, cls, methods


def links(cls: type, version: str) -> tuple[str, str]:
    import azure.ai.projects as package
    import azure.ai.projects.operations as operations

    if getattr(operations, cls.__name__, None) is not cls:
        fail(f"{cls.__name__} is not exported from azure.ai.projects.operations, so it has no API reference page.")
    moniker = "azure-python-preview" if re.search(r"\d(?:a|b|rc)\d+|\.dev\d+", version) else "azure-python"
    site_packages = Path(package.__file__).resolve().parents[3]
    source_path = Path(inspect.getsourcefile(cls)).resolve().relative_to(site_packages).as_posix()
    return (
        LEARN_URL.format(page=cls.__name__.lower(), moniker=moniker),
        SOURCE_URL.format(version=version, path=source_path, line=inspect.getsourcelines(cls)[1]),
    )


def notebook_name(module: str) -> str:
    return re.sub(r"[._]", "-", module.removeprefix("client.")) + ".ipynb"


def preview_parameters(module: str, methods: list[Method]) -> list[str]:
    """Preview parameters of a stable module; `client.beta.*` already opts in to preview."""
    if module.startswith("client.beta."):
        return []
    return [f"{method.name}({name})" for method in methods for name in method.preview]


def print_inventory(module: str) -> None:
    version, cls, methods = inventory(module)
    learn, source = links(cls, version)
    print(f"{module} -> azure.ai.projects.operations.{cls.__name__} ({DISTRIBUTION} {version})")
    print(f"File:     notebooks/{notebook_name(module)}")
    print(f'Metadata: "cosmopilot": {json.dumps({"sdk_version": version, "modules": [module]})}')
    print("\nCell 1 (markdown):\n")
    print(f"# <action title>: `{module}`\n")
    print(f"**API reference:** [`{cls.__name__}`]({learn}) · **Version:** [`{DISTRIBUTION}=={version}`]({source})")
    preview = preview_parameters(module, methods)
    if preview:
        print(f"\nCell 2: pass allow_preview=True to AIProjectClient; preview parameters: {', '.join(preview)}.")
    print(f"\nSections ({len(methods)} public methods). Pass every parameter below by keyword, in this order:")
    for method in methods:
        print(f"\n## `{method.name}` -> {method.returns}")
        for parameter in method.parameters:
            note = method.notes.get(parameter.name)
            print(
                f"    {parameter.name}: {annotation(parameter.annotation)}{default(parameter)}"
                + (f"  # {note}" if note else "")
            )
        if not method.parameters:
            print("    (no parameters)")


def text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def headings(markdown: str) -> list[str]:
    """ATX heading lines outside fenced code blocks."""
    found, fenced = [], False
    for line in markdown.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and re.match(r" {0,3}#{1,6}(?:\s|$)", line):
            found.append(line.strip())
    return found


def dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def environment_names(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        key = None
        if isinstance(node, ast.Subscript) and dotted(node.value) == "os.environ":
            key = node.slice
        elif isinstance(node, ast.Call) and dotted(node.func) in ("os.environ.get", "os.getenv") and node.args:
            key = node.args[0]
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            names.add(key.value)
    return names


def comment_lines(source: str) -> set[int]:
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return {token.start[0] for token in tokens if token.type == tokenize.COMMENT}


def call_problems(call: ast.Call, method: Method, source: str) -> list[str]:
    expected = [parameter.name for parameter in method.parameters]
    passed = [keyword.arg for keyword in call.keywords if keyword.arg]
    missing = [name for name in expected if name not in passed]
    unknown = [name for name in passed if name not in expected]
    problems = []
    if call.args:
        problems.append("pass every parameter by keyword.")
    if any(keyword.arg is None for keyword in call.keywords):
        problems.append("write each parameter out instead of unpacking **kwargs.")
    if missing:
        problems.append(f"missing {', '.join(missing)}.")
    if unknown:
        problems.append(f"not in the signature: {', '.join(unknown)}.")
    if not missing and not unknown and passed != expected:
        problems.append(f"pass the parameters in signature order: {', '.join(expected)}.")
    lines = [keyword.lineno for keyword in call.keywords]
    if call.lineno in lines or len(set(lines)) != len(lines):
        problems.append("put each parameter on its own line.")
    commented = comment_lines(source)
    uncommented = [keyword.arg for keyword in call.keywords if keyword.arg and keyword.lineno not in commented]
    if uncommented:
        problems.append(f"add an inline comment to {', '.join(uncommented)}.")
    return problems


def check(path: Path) -> list[str]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    if not cells or cells[0].get("cell_type") != "markdown":
        return ["cell 1: must be the markdown cell with the title and links."]
    lines = text(cells[0]).splitlines()
    title = TITLE.fullmatch(lines[0].strip()) if lines else None
    if title is None:
        return ["cell 1: must start with the title line  # <action title>: `client.<module>`"]
    module = title["module"]
    version, cls, methods = inventory(module)
    learn, source = links(cls, version)
    problems = []

    words = len(title["title"].split())
    if words not in TITLE_WORDS:
        problems.append(
            f"cell 1: the action title has {words} words; "
            f"write one sentence of {TITLE_WORDS.start} to {TITLE_WORDS.stop - 1} words."
        )
    if title["title"][-1] in ".!?;:,":
        problems.append("cell 1: end the action title without punctuation.")
    targets = re.findall(r"\]\(([^)\s]+)\)", text(cells[0]))
    for url in (learn, source):
        if url not in targets:
            problems.append(f"cell 1: missing link {url}")
    if len(targets) != 2:
        problems.append("cell 1: the line under the title has exactly two links, API reference and version.")
    markdown = [cell for cell in cells if cell.get("cell_type") == "markdown"]
    level_one = sum(heading.startswith("# ") for cell in markdown for heading in headings(text(cell)))
    if level_one != 1 or len(headings(text(cells[0]))) != 1:
        problems.append("the title must be the notebook's only `#` heading and cell 1's only heading.")

    expected_metadata = {"sdk_version": version, "modules": [module]}
    if notebook.get("metadata", {}).get("cosmopilot") != expected_metadata:
        problems.append(f'metadata: set "cosmopilot" to {json.dumps(expected_metadata)}.')
    if (notebook.get("nbformat", 0), notebook.get("nbformat_minor", 0)) < (4, 5):
        problems.append("use nbformat 4.5, where every cell has an id.")
    ids = [cell.get("id") for cell in cells]
    if None in ids or len(set(ids)) != len(ids):
        problems.append("give every cell a unique id.")
    if path.name != notebook_name(module):
        problems.append(f"name the file {notebook_name(module)}.")

    trees = {}
    for number, cell in enumerate(cells, start=1):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs") or cell.get("execution_count") is not None:
            problems.append(f"cell {number}: clear outputs and execution counts before committing.")
        try:
            trees[number] = ast.parse(text(cell))
        except SyntaxError as error:
            problems.append(f"cell {number}: not plain Python ({error.msg}); no magics or shell escapes.")

    preview = preview_parameters(module, methods)
    if len(cells) < 2 or cells[1].get("cell_type") != "code":
        problems.append("cell 2: must be the code cell with imports, environment variables, and the client.")
    elif 2 in trees:
        setup = trees[2]
        if not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(setup)):
            problems.append("cell 2: put the notebook's imports here.")
        clients = [n for n in ast.walk(setup) if isinstance(n, ast.Call) and dotted(n.func) == "AIProjectClient"]
        if len(clients) != 1:
            problems.append("cell 2: construct exactly one AIProjectClient.")
        elif preview and not any(
            k.arg == "allow_preview" and isinstance(k.value, ast.Constant) and k.value.value is True
            for k in clients[0].keywords
        ):
            problems.append(f"cell 2: pass allow_preview=True; preview parameters: {', '.join(preview)}.")
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        documented = set(re.findall(r"^[ \t]*(?:#[ \t]*)?([A-Z][A-Z0-9_]*)=", env_example, re.MULTILINE))
        for name in sorted(environment_names(setup) - documented):
            problems.append(f"cell 2: {name} is not listed in .env.example.")
    for number, tree in trees.items():
        if number == 2:
            continue
        if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree)):
            problems.append(f"cell {number}: move imports to cell 2.")
        if any(isinstance(n, ast.Attribute) and dotted(n) in ("os.environ", "os.getenv") for n in ast.walk(tree)):
            problems.append(f"cell {number}: read environment variables in cell 2 only.")

    by_name = {method.name: method for method in methods}
    seen = []
    for index in range(2, len(cells), 2):
        number, heading_cell = index + 1, cells[index]
        body = [line.strip() for line in text(heading_cell).splitlines() if line.strip()]
        match = None
        if heading_cell.get("cell_type") == "markdown" and body:
            match = re.fullmatch(r"## `(\w+)`", body[0])
        if match is None or match.group(1) not in by_name:
            problems.append(f"cell {number}: expected a section heading ## `<method>` for one of: {', '.join(by_name)}.")
            continue
        name = match.group(1)
        if name in seen:
            problems.append(f"cell {number}: `{name}` already has a section.")
        seen.append(name)
        if len(body) < 2:
            problems.append(f"cell {number}: add one sentence under the heading saying what `{name}` does.")
        if len(headings(text(heading_cell))) > 1:
            problems.append(f"cell {number}: a section has one heading.")
        if index + 1 >= len(cells) or cells[index + 1].get("cell_type") != "code":
            problems.append(f"cell {number + 1}: follow the heading with the code cell that calls `{name}`.")
            continue
        tree = trees.get(number + 1)
        if tree is None:
            continue
        calls = sorted(
            (n for n in ast.walk(tree) if isinstance(n, ast.Call) and dotted(n.func) == f"{module}.{name}"),
            key=lambda n: (n.lineno, n.col_offset),
        )
        if len(calls) != 1:
            problems.append(f"cell {number + 1}: call {module}.{name}(...) exactly once, through the full path.")
            continue
        for issue in call_problems(calls[0], by_name[name], text(cells[index + 1])):
            problems.append(f"cell {number + 1}: `{name}`: {issue}")
    missing = [name for name in by_name if name not in seen]
    if missing:
        problems.append(f"no section for: {', '.join(missing)}.")
    return problems


def main() -> int:
    if sys.version_info < (3, 11):
        fail("this script needs Python 3.11 or newer for typing.get_overloads.")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory_parser = commands.add_parser("inventory", help="print a module's header links and method signatures")
    inventory_parser.add_argument("module", help="module path, for example client.agents")
    check_parser = commands.add_parser("check", help="check notebooks against the skill")
    check_parser.add_argument("notebooks", nargs="+", type=Path)
    arguments = parser.parse_args()

    if arguments.command == "inventory":
        print_inventory(arguments.module)
        return 0
    failed = False
    for path in arguments.notebooks:
        problems = check(path)
        for problem in problems:
            print(f"{path}: {problem}")
        if not problems:
            print(f"{path}: OK")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
