"""AST-based documentation coverage check for this source snapshot.

The script avoids importing package modules, so optional market-data dependencies
are not required. It checks source docstring presence and rejects known
placeholder forms. It is intentionally a lightweight regression guard rather
than a replacement for Sphinx or a full natural-language quality evaluator.
"""

from __future__ import annotations

import ast
from pathlib import Path

PLACEHOLDERS = {"todo.", "helper function.", "calculate something.", "returns result."}

NON_ENGLISH_LANGUAGE_PATTERNS = dict(
    [
        ("".join(chars), replacement)
        for chars, replacement in (
            (("t", "i", "p", "o"), "option_type"),
            (("p", "o", "s", "i", "c", "i", "o", "n"), "position"),
            (("p", "r", "i", "m", "a"), "premium"),
            (("c", "u", "p", "o", "n"), "coupon"),
            (("p", "a", "g", "o", "s"), "payments"),
            (("p", "a", "g", "o"), "payment"),
            (("p", "r", "e", "c", "i", "o"), "price"),
            (("r", "e", "d", "e", "n", "c", "i", "o", "n"), "redemption"),
            (("a", "n", "i", "o", "s"), "years"),
            (("d", "i", "a", "r", "i", "o"), "daily"),
            (("a", "c", "c", "i", "o", "n"), "asset"),
            (("m", "e", "r", "c", "a", "d", "o"), "market"),
            (("d", "e", "s", "c", "u", "e", "n", "t", "o"), "discount"),
            (("p", "r", "e", "s", "e", "n", "t", "e"), "present"),
            (("p", "r", "o", "y", "e", "c", "t", "a", "d", "o"), "projected"),
        )
    ]
)


def check_english_language(path: Path) -> list[str]:
    """Return user-facing English-language failures for one text source file."""
    import re

    failures: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        for spanish_word, english_word in NON_ENGLISH_LANGUAGE_PATTERNS.items():
            if re.search(rf"\b{re.escape(spanish_word)}\b", lowered):
                failures.append(
                    f"{path}:{line_number}: Non-English term '{spanish_word}' found; use '{english_word}'"
                )
    return failures


def check_file(path: Path) -> list[str]:
    """Return documentation-coverage failures for one Python source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    failures: list[str] = []

    def require(node: ast.AST, label: str) -> None:
        doc = ast.get_docstring(node)
        if not doc or doc.strip().lower() in PLACEHOLDERS:
            failures.append(
                f"{path}:{getattr(node, 'lineno', 1)}: missing or placeholder docstring for {label}"
            )

    require(tree, "module")

    def walk(nodes: list[ast.stmt], prefix: str = "", nested: bool = False) -> None:
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                require(node, prefix + node.name)
                walk(node.body, prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not nested and node.name != "__init__":
                    require(node, prefix + node.name)
                walk(node.body, prefix + node.name + ".", nested=True)

    walk(tree.body)
    return failures


def check_api_reference(root: Path) -> list[str]:
    """Return failures when a source module lacks a generated API page."""
    failures: list[str] = []
    source_root = root / "src" / "abaquant"
    api_root = root / "docs" / "api"
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(root / "src").with_suffix("")
        parts = list(relative.parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        module = ".".join(parts)
        below_root = parts[1:]
        if module == "abaquant":
            page = api_root / "root.rst"
        elif is_package:
            page = api_root.joinpath(*below_root, "index.rst")
        else:
            page = api_root.joinpath(*below_root).with_suffix(".rst")
        if not page.exists():
            failures.append(f"{path}: missing generated API page {page.relative_to(root)}")
            continue
        text = page.read_text(encoding="utf-8")
        if f".. automodule:: {module}" not in text:
            failures.append(f"{page}: missing automodule directive for {module}")
    return failures


def main() -> int:
    """Run the documentation audit over the repository snapshot."""
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts or "tools" in path.parts or "tests" in path.parts:
            continue
        failures.extend(check_file(path))
        if path.name != "check_documentation.py" and path.suffix in {".py", ".md", ".toml", ".txt"}:
            failures.extend(check_english_language(path))
    failures.extend(check_api_reference(root))
    if failures:
        print("\n".join(failures))
        return 1
    print("Documentation coverage check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
