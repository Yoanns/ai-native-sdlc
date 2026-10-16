#!/usr/bin/env python3
"""The spec gate: code changes land only with an approved spec and plan.

This is the gate that binds every agent and every human, whichever tool wrote
the change — it runs in CI and before push, not inside an agent. Agent hooks
are a fast local warning; this is the guarantee.

A change passes when either:

  - it touches no code (only exempt paths: the .sdlc/ artifacts, docs, ...), or
  - it is tied to at least one work item whose spec.md AND plan.md both carry
    `status: approved` in their front matter.

A change is tied to a work item by any of:

  - touching a file under .sdlc/<slug>/
  - a `Work-Item: <slug>` trailer in a commit message in the range
  - --work-item <slug> (CI can pass a slug taken from the PR)

Usage
  spec_gate.py                       # range origin/HEAD...HEAD, or main...HEAD
  spec_gate.py --base origin/main    # CI on a pull request
  spec_gate.py --base @{upstream}    # pre-push
  spec_gate.py --work-item invoice-pdf-bundle

Configuration (optional): .sdlc/gate.json
  {"exempt": ["docs/**", "*.md"], "sdlc_dir": ".sdlc"}

Exit: 0 pass, 1 gate failed, 2 could not evaluate (not a git repo, bad base).
Standard library only — no install step.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_EXEMPT = [
    ".sdlc/**",
    "docs/**",
    "*.md",
    "**/*.md",
    "LICENSE",
    "LICENSE.*",
    ".gitignore",
    ".gitattributes",
    ".github/**",
    ".cursor/**",
    ".claude/**",
    ".gemini/**",
    ".aider.conf.yml",
]

TRAILER = re.compile(r"^Work-Item:\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$", re.MULTILINE | re.IGNORECASE)
STATUS = re.compile(r"^status:\s*([A-Za-z-]+)", re.MULTILINE)


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def resolve_base(requested: str | None) -> str:
    candidates = [requested] if requested else ["origin/HEAD", "origin/main", "main", "origin/master", "master"]
    for ref in candidates:
        try:
            git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
            return ref
        except RuntimeError:
            continue
    raise RuntimeError(f"cannot resolve a base to compare against (tried: {', '.join(candidates)})")


def load_config(root: Path) -> tuple[list[str], str]:
    path = root / ".sdlc" / "gate.json"
    if not path.exists():
        return DEFAULT_EXEMPT, ".sdlc"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("exempt", DEFAULT_EXEMPT), data.get("sdlc_dir", ".sdlc")


def exempt(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def front_matter_status(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else ""
    match = STATUS.search(block)
    return match.group(1).lower() if match else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Code changes land only with an approved spec and plan.")
    parser.add_argument("--base", help="ref to compare against (default: origin/HEAD, then main)")
    parser.add_argument("--work-item", action="append", default=[], help="slug of a work item this change belongs to")
    args = parser.parse_args()

    try:
        root = Path(git("rev-parse", "--show-toplevel").strip())
        base = resolve_base(args.base)
        changed = [line for line in git("diff", "--name-only", f"{base}...HEAD").splitlines() if line]
        messages = git("log", "--format=%B", f"{base}..HEAD")
    except RuntimeError as exc:
        print(f"spec gate: cannot evaluate — {exc}", file=sys.stderr)
        return 2

    patterns, sdlc_dir = load_config(root)
    code = [path for path in changed if not exempt(path, patterns)]

    if not code:
        print(f"spec gate: pass — no code changed against {base} ({len(changed)} file(s), all exempt)")
        return 0

    slugs: set[str] = set(args.work_item)
    prefix = sdlc_dir.rstrip("/") + "/"
    for path in changed:
        if path.startswith(prefix):
            parts = path[len(prefix):].split("/")
            if len(parts) > 1 and not parts[0].startswith((".", "_")) and parts[0].upper() != "TEMPLATES":
                slugs.add(parts[0])
    slugs.update(TRAILER.findall(messages))

    report: list[str] = []
    approved: list[str] = []
    for slug in sorted(slugs):
        spec = front_matter_status(root / sdlc_dir / slug / "spec.md")
        plan = front_matter_status(root / sdlc_dir / slug / "plan.md")
        ok = spec == "approved" and plan == "approved"
        if ok:
            approved.append(slug)
        report.append(f"  {slug}: spec.md {spec or 'missing'}, plan.md {plan or 'missing'}" + ("  ✓" if ok else ""))

    if approved:
        print(f"spec gate: pass — {len(code)} code file(s) changed, covered by approved work item(s): {', '.join(approved)}")
        return 0

    print(f"spec gate: FAIL — {len(code)} code file(s) changed against {base} with no approved work item.", file=sys.stderr)
    for path in code[:10]:
        print(f"    {path}", file=sys.stderr)
    if len(code) > 10:
        print(f"    … and {len(code) - 10} more", file=sys.stderr)
    if report:
        print("  Work items referenced, none fully approved:", file=sys.stderr)
        print("\n".join(report), file=sys.stderr)
    else:
        print("  No work item referenced.", file=sys.stderr)
    print(
        "\n  Fix: tie the change to a work item whose spec.md and plan.md both say\n"
        "  `status: approved` — touch a file under .sdlc/<slug>/, or add a\n"
        "  `Work-Item: <slug>` trailer to a commit message.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
