"""Fail CI when local data or recognizable credentials enter the repository."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {
    ".git",
    ".ruff_cache",
    ".pytest_cache",
    ".venv",
    ".venv312",
    "__pycache__",
    "dist",
    "node_modules",
    "pytest-cache-files",
}
DENIED_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".pem", ".key"}
SECRET_PATTERNS = {
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"gh[pousr]_[0-9A-Za-z]{30,}"),
}


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return [ROOT / line for line in result.stdout.splitlines()]
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(
            part in IGNORED_PARTS or part.startswith("pytest-cache-files-")
            for part in path.relative_to(ROOT).parts
        )
    ]


def main() -> int:
    problems: list[str] = []
    for path in repository_files():
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.casefold() in DENIED_SUFFIXES:
            problems.append(f"local/private file: {relative}")
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            problems.append(f"environment file: {relative}")
            continue
        if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".gif", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{label}: {relative}")
    if problems:
        print("Repository safety check failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print(f"Repository safety check passed ({len(repository_files())} files reviewed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
