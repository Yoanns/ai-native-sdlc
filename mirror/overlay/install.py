#!/usr/bin/env python3
"""Install the AI-native SDLC into a repository, for any coding agent.

  python3 install.py /path/to/repo                    # detect the agents in use
  python3 install.py /path/to/repo --agents cursor,copilot
  python3 install.py /path/to/repo --agents all
  python3 install.py /path/to/repo --dry-run          # show, change nothing

Always installed: AGENTS.md (lifecycle block), REVIEW.md, the playbook, the
artifact templates, the guard scripts, the spec gate and its CI workflow, and a
pre-push hook. Per agent: Cursor rules and hooks, Copilot instructions and
hooks, Gemini CLI and Aider settings so they read AGENTS.md. Codex, Jules, Zed,
Windsurf, Devin, Amp, Junie and others read AGENTS.md with nothing extra.

Three kinds of file:

  managed  owned by the installer, refreshed on every run (playbook, rules,
           templates, hookio.py, spec_gate.py)
  yours    written once, then left alone so your edits survive (REVIEW.md,
           the guard scripts with their TODO lists, the CI workflow);
           --force overwrites them
  merged   shared with other tools — the installer adds only its own part
           (AGENTS.md between its markers, .cursor/hooks.json entries,
           .gemini/settings.json, .aider.conf.yml)

Safe to re-run: that is how you update. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS = ("cursor", "copilot", "gemini", "aider")
BEGIN, END = "<!-- sdlc:begin", "<!-- sdlc:end -->"

MANAGED = [
    ("playbook", ".sdlc/playbook"),
    ("templates/spec.md", ".sdlc/templates/spec.md"),
    ("templates/plan.md", ".sdlc/templates/plan.md"),
    ("guards/hookio.py", ".sdlc/guards/hookio.py"),
    ("enforcement/spec_gate.py", ".sdlc/enforcement/spec_gate.py"),
]
YOURS = [
    ("templates/REVIEW.md", "REVIEW.md"),
    ("guards/protect-paths.sh", ".sdlc/guards/protect-paths.sh"),
    ("guards/block-credentials.sh", ".sdlc/guards/block-credentials.sh"),
    ("guards/require-release-auth.sh", ".sdlc/guards/require-release-auth.sh"),
    ("guards/format-file.sh", ".sdlc/guards/format-file.sh"),
    ("monitor/watch-metrics.sh", ".sdlc/monitor/watch-metrics.sh"),
    ("enforcement/sdlc-gate.yml", ".github/workflows/sdlc-gate.yml"),
]
PER_AGENT_MANAGED = {
    "cursor": [("adapters/cursor/rules", ".cursor/rules")],
    "copilot": [("adapters/copilot/instructions", ".github/instructions"),
                ("adapters/copilot/hooks/sdlc.json", ".github/hooks/sdlc.json")],
}
EXECUTABLE_SUFFIXES = (".sh", ".py")


class Installer:
    def __init__(self, target: Path, dry_run: bool, force: bool):
        self.target = target
        self.dry_run = dry_run
        self.force = force
        self.log: list[tuple[str, str]] = []

    # -- primitives ---------------------------------------------------------

    def note(self, action: str, path: str) -> None:
        self.log.append((action, path))

    def write_text(self, rel: str, text: str, action: str) -> None:
        self.note(action, rel)
        if self.dry_run:
            return
        path = self.target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        self.make_executable(path)

    def copy_file(self, src: Path, rel: str, owned: bool) -> None:
        dst = self.target / rel
        if dst.exists():
            if dst.read_bytes() == src.read_bytes():
                self.note("unchanged", rel)
                return
            if not owned and not self.force:
                self.note("kept yours", rel)
                return
        self.note("updated" if dst.exists() else "created", rel)
        if self.dry_run:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        self.make_executable(dst)

    def copy_tree(self, src: Path, rel: str) -> None:
        for path in sorted(src.rglob("*")):
            if path.is_file():
                self.copy_file(path, f"{rel}/{path.relative_to(src).as_posix()}", owned=True)

    @staticmethod
    def make_executable(path: Path) -> None:
        if os.name != "nt" and (path.suffix in EXECUTABLE_SUFFIXES or path.name == "pre-push"):
            path.chmod(path.stat().st_mode | 0o111)

    def install(self, src: str, rel: str, owned: bool) -> None:
        source = HERE / src
        if source.is_dir():
            self.copy_tree(source, rel)
        else:
            self.copy_file(source, rel, owned)

    # -- merges -------------------------------------------------------------

    def merge_agents_md(self) -> None:
        template = (HERE / "templates/AGENTS.md").read_text(encoding="utf-8")
        start, end = template.index(BEGIN), template.index(END) + len(END)
        block = template[start:end]
        path = self.target / "AGENTS.md"
        if not path.exists():
            self.write_text("AGENTS.md", template, "created")
            return
        current = path.read_text(encoding="utf-8")
        if BEGIN in current and END in current:
            s, e = current.index(BEGIN), current.index(END) + len(END)
            merged = current[:s] + block + current[e:]
            if merged == current:
                self.note("unchanged", "AGENTS.md")
            else:
                self.write_text("AGENTS.md", merged, "merged (lifecycle block updated)")
        else:
            self.write_text("AGENTS.md", current.rstrip() + "\n\n" + block + "\n", "merged (lifecycle block added)")

    def merge_cursor_hooks(self) -> None:
        ours = json.loads((HERE / "adapters/cursor/hooks.json").read_text(encoding="utf-8"))
        rel = ".cursor/hooks.json"
        path = self.target / rel
        if not path.exists():
            self.write_text(rel, json.dumps(ours, indent=2) + "\n", "created")
            return
        try:
            theirs = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.note("SKIPPED (not valid JSON — add the entries from adapters/cursor/hooks.json by hand)", rel)
            return
        theirs.setdefault("version", ours["version"])
        hooks = theirs.setdefault("hooks", {})
        added = 0
        for event, entries in ours["hooks"].items():
            existing = hooks.setdefault(event, [])
            commands = {entry.get("command") for entry in existing}
            for entry in entries:
                if entry["command"] not in commands:
                    existing.append(entry)
                    added += 1
        if added:
            self.write_text(rel, json.dumps(theirs, indent=2) + "\n", f"merged ({added} hook entries added)")
        else:
            self.note("unchanged", rel)

    def merge_gemini(self) -> None:
        rel = ".gemini/settings.json"
        path = self.target / rel
        settings: dict = {}
        if path.exists():
            try:
                settings = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.note('SKIPPED (not valid JSON — set "context": {"fileName": ["AGENTS.md", "GEMINI.md"]} by hand)', rel)
                return
        context = settings.setdefault("context", {})
        names = context.get("fileName")
        if names is None:
            names = ["AGENTS.md", "GEMINI.md"]
        elif isinstance(names, str):
            names = [names]
        if "AGENTS.md" in names and path.exists() and context.get("fileName") is not None:
            self.note("unchanged", rel)
            return
        if "AGENTS.md" not in names:
            names = ["AGENTS.md", *names]
        context["fileName"] = names
        self.write_text(rel, json.dumps(settings, indent=2) + "\n", "merged" if path.exists() else "created")

    def merge_aider(self) -> None:
        rel = ".aider.conf.yml"
        path = self.target / rel
        if not path.exists():
            self.copy_file(HERE / "adapters/aider/.aider.conf.yml", rel, owned=True)
            return
        text = path.read_text(encoding="utf-8")
        if "AGENTS.md" in text:
            self.note("unchanged", rel)
        elif re.search(r"^read\s*:", text, re.M):
            self.note("ACTION NEEDED (add AGENTS.md to the existing 'read:' entry by hand)", rel)
        else:
            self.write_text(rel, text.rstrip() + "\nread: AGENTS.md\n", "merged")

    def git_hook(self) -> None:
        try:
            result = subprocess.run(["git", "-C", str(self.target), "rev-parse", "--git-path", "hooks"],
                                    capture_output=True, text=True)
        except FileNotFoundError:
            self.note("SKIPPED (git not found)", "pre-push hook")
            return
        if result.returncode != 0:
            self.note("SKIPPED (not a git repository)", "pre-push hook")
            return
        hooks_dir = Path(result.stdout.strip())
        if not hooks_dir.is_absolute():
            hooks_dir = self.target / hooks_dir
        dst = hooks_dir / "pre-push"
        src = HERE / "enforcement/pre-push"
        label = os.path.relpath(dst, self.target).replace(os.sep, "/")
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            self.note("kept yours (an existing pre-push hook — call .sdlc/enforcement/spec_gate.py from it)", label)
            return
        if dst.exists():
            self.note("unchanged", label)
            return
        self.note("created", label)
        if not self.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            self.make_executable(dst)

    # -- detection ----------------------------------------------------------

    def detect(self) -> list[str]:
        t = self.target
        found = []
        if (t / ".cursor").exists() or (t / ".cursorrules").exists():
            found.append("cursor")
        if any((t / ".github" / p).exists() for p in ("copilot-instructions.md", "instructions", "hooks", "agents", "chatmodes")):
            found.append("copilot")
        if (t / ".gemini").exists() or (t / "GEMINI.md").exists():
            found.append("gemini")
        if (t / ".aider.conf.yml").exists() or any(t.glob(".aider*")):
            found.append("aider")
        return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the AI-native SDLC into a repository.")
    parser.add_argument("target", help="the repository to install into")
    parser.add_argument("--agents", default="auto",
                        help="comma-separated: cursor, copilot, gemini, aider — or auto (default), all, none")
    parser.add_argument("--dry-run", action="store_true", help="show what would change; write nothing")
    parser.add_argument("--force", action="store_true", help="also overwrite files you own (REVIEW.md, guards, workflow)")
    parser.add_argument("--no-git-hook", action="store_true", help="do not install the pre-push hook")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"install: {target} is not a directory", file=sys.stderr)
        return 1

    inst = Installer(target, args.dry_run, args.force)
    if args.agents == "auto":
        agents = inst.detect()
    elif args.agents == "all":
        agents = list(AGENTS)
    elif args.agents == "none":
        agents = []
    else:
        agents = [a.strip() for a in args.agents.split(",") if a.strip()]
        unknown = [a for a in agents if a not in AGENTS]
        if unknown:
            print(f"install: unknown agent(s) {', '.join(unknown)}; choose from {', '.join(AGENTS)}", file=sys.stderr)
            return 1

    for src, rel in MANAGED:
        inst.install(src, rel, owned=True)
    for src, rel in YOURS:
        inst.install(src, rel, owned=False)
    inst.merge_agents_md()
    if not args.no_git_hook:
        inst.git_hook()

    for agent in agents:
        for src, rel in PER_AGENT_MANAGED.get(agent, []):
            inst.install(src, rel, owned=True)
        if agent == "cursor":
            inst.merge_cursor_hooks()
        elif agent == "gemini":
            inst.merge_gemini()
        elif agent == "aider":
            inst.merge_aider()

    version = (HERE / "playbook/VERSION").read_text(encoding="utf-8").strip()
    print(f"agent-native-sdlc {version} → {target}{'  (dry run — nothing written)' if args.dry_run else ''}")
    print(f"agents: {', '.join(agents) if agents else 'none detected — AGENTS.md only (pass --agents to add more)'}\n")
    changed = [entry for entry in inst.log if entry[0] != "unchanged"]
    width = max((len(a) for a, _ in changed), default=0)
    for action, path in changed:
        print(f"  {action:<{width}}  {path}")
    unchanged = len(inst.log) - len(changed)
    if unchanged:
        print(f"  {'':<{width}}  … and {unchanged} file(s) already up to date")

    notes = []
    if any((target / p).exists() for p in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")):
        notes.append("This repository has a CLAUDE.md, so Claude Code will not read AGENTS.md. For Claude Code,\n"
                     "    install the ai-native-sdlc plugin, or add the line @AGENTS.md to CLAUDE.md.")
    notes.append("Next: follow .sdlc/playbook/setup.md — fill in AGENTS.md, tailor the guards, and make the\n"
                 "    spec-gate check required in branch protection.")
    print()
    for note in notes:
        print(f"  • {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
