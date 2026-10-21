"""Report installed distributions that the project does not use.

A distribution is "unused" when:
  * no project Python file imports it, AND
  * it is not (transitively) required by any distribution that IS used.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

from importlib import metadata

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    "venv", ".git", "node_modules", "__pycache__", ".pytest_cache",
    "frontend", "output", "uploads", "test_uploads",
    ".idea", ".vscode", ".cursor", ".claude", ".gemini", ".kiro",
    ".qoder", ".code-review-graph", ".responsive-check", "Kotlin",
    "research_Paper",
}


def norm(name: str) -> str:
    """PEP 503 normalized distribution name."""
    import re

    return re.sub(r"[-_.]+", "-", name).lower()


# Not imported, but invoked from config: .mcp.json runs
# `python -m code_review_graph serve` and .claude hooks call its CLI.
EXTRA_ROOTS = {"code-review-graph"}


def project_imports() -> set[str]:
    found: set[str] = set()
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    found.add(node.module.split(".")[0])
    return found


def main() -> None:
    dists = {norm(d.metadata["Name"]): d for d in metadata.distributions()
             if d.metadata["Name"]}
    imports = project_imports()

    # import-name -> distribution names
    top_to_dists = metadata.packages_distributions()

    used: set[str] = set()
    stack: list[str] = []
    for root in EXTRA_ROOTS:
        if norm(root) in dists:
            used.add(norm(root))
            stack.append(norm(root))
    for imp in imports:
        for name in top_to_dists.get(imp, []):
            key = norm(name)
            if key in dists and key not in used:
                used.add(key)
                stack.append(key)

    # expand transitive closure of requirements
    while stack:
        cur = stack.pop()
        for req in dists[cur].requires or []:
            req_name = req.split(";")[0].split("[")[0]
            req_name = norm(req_name.split("=")[0].split(">")[0]
                            .split("<")[0].split("~")[0].split("!")[0]
                            .split(" ")[0].strip())
            if req_name in dists and req_name not in used:
                used.add(req_name)
                stack.append(req_name)

    unused = sorted(set(dists) - used)
    print("=== UNUSED DISTRIBUTIONS (candidates) ===")
    for name in unused:
        # who else requires this candidate? only safe if no kept dist needs it
        requirers = []
        for other, dist in dists.items():
            if other == name or other in used:
                continue
            for req in dist.requires or []:
                req_name = norm(req.split(";")[0].split("[")[0]
                                .split("=")[0].split(">")[0]
                                .split("<")[0].split("~")[0]
                                .split("!")[0].split(" ")[0].strip())
                if req_name == name:
                    requirers.append(other)
        flag = "KEEP (needed by " + ", ".join(requirers) + ")" if requirers else "REMOVE"
        print(f"  {name}=={dists[name].version}  -> {flag}")
    print(f"\ntotal installed: {len(dists)}, used: {len(used)}, unused: {len(unused)}")

    print("\n=== top-level imports found in project code ===")
    print("  " + ", ".join(sorted(i for i in imports if i in top_to_dists)))


if __name__ == "__main__":
    main()
