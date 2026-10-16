#!/usr/bin/env python3
"""Build the agent-agnostic mirror of this plugin.

The mirror (agent-native-sdlc) is generated from this repository and never
edited by hand. It carries the same lifecycle to agents other than Claude Code:
AGENTS.md as the entry point, the stage procedures as a plain-markdown
playbook, conditional rules for Cursor and Copilot, the guard scripts with
hook configs for both, and the repo-level spec gate that binds every agent.

Three kinds of content end up in the mirror:

  transformed  stage skills, references, review passes, templates — rewritten
               from Claude Code's vocabulary by the PHRASES table below
  overlay      mirror-only files maintained in mirror/overlay/ (setup guide,
               README, adapter configs, installer); *.tmpl files are rendered
  copied       agent-neutral assets: guard scripts, spec gate, artifact
               templates, LICENSE, SOURCES.md

Then the build checks its own output and fails on:

  - any Claude-specific term left in the output (the leak check) — so a new
    "Claude" or ".claude/" in a skill breaks the build instead of shipping
  - a reference to a playbook/template/guard path that does not exist
  - invalid JSON or front matter, shell or Python syntax errors

Usage
  python3 scripts/build_mirror.py --out ../agent-native-sdlc
  python3 scripts/build_mirror.py --out build/mirror --source-commit abc1234

The output directory is replaced, except its .git directory.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_REPO = "yoanns/ai-native-sdlc"
MIRROR_REPO = "yoanns/agent-native-sdlc"

# ----------------------------------------------------------------------------
# What goes where
# ----------------------------------------------------------------------------

STAGES = [
    # n, playbook name, source skill
    (1, "spec", "Spec", "sdlc-design-spec"),
    (2, "build", "Build", "sdlc-build-plan"),
    (3, "test", "Test", "sdlc-test-verify"),
    (4, "deploy", "Deploy", "sdlc-deploy-review"),
    (5, "maintain", "Maintain", "sdlc-maintain-monitor"),
]

REVIEW_PASSES = [
    ("sdlc-review-bugs", "bugs", "Bugs and logic"),
    ("sdlc-review-security", "security", "Security"),
    ("sdlc-review-spec", "spec", "Spec conformance"),
]

# Source skill/agent name -> where its content lives once installed.
NAME_MAP = {
    "sdlc-orchestrator": ".sdlc/playbook/README.md",
    "sdlc-setup-guardrails": ".sdlc/playbook/setup.md",
    **{skill: f".sdlc/playbook/{n}-{key}.md" for n, key, _, skill in STAGES},
    **{agent: f".sdlc/playbook/review-passes/{key}.md" for agent, key, _ in REVIEW_PASSES},
}

# Source file -> mirror path, transformed.
TRANSFORMED = {
    "skills/sdlc-orchestrator/SKILL.md": "playbook/README.md",
    **{f"skills/{skill}/SKILL.md": f"playbook/{n}-{key}.md" for n, key, _, skill in STAGES},
    "skills/sdlc-orchestrator/references/stage-map.md": "playbook/reference/stage-map.md",
    "skills/sdlc-orchestrator/references/loop.md": "playbook/reference/loop.md",
    "skills/sdlc-maintain-monitor/references/control-bands.md": "playbook/reference/control-bands.md",
    **{f"agents/{agent}.md": f"playbook/review-passes/{key}.md" for agent, key, _ in REVIEW_PASSES},
    "templates/REVIEW.md": "templates/REVIEW.md",
    "templates/spec.md": "templates/spec.md",
    "templates/plan.md": "templates/plan.md",
    "templates/monitor/watch-metrics.sh": "monitor/watch-metrics.sh",
}

# Source file -> mirror path, byte for byte. These are agent-neutral already.
COPIED = {
    "templates/hooks/scripts/hookio.py": "guards/hookio.py",
    "templates/hooks/scripts/protect-paths.sh": "guards/protect-paths.sh",
    "templates/hooks/scripts/block-credentials.sh": "guards/block-credentials.sh",
    "templates/hooks/scripts/require-release-auth.sh": "guards/require-release-auth.sh",
    "templates/hooks/scripts/format-file.sh": "guards/format-file.sh",
    "templates/enforcement/spec_gate.py": "enforcement/spec_gate.py",
    "templates/enforcement/pre-push": "enforcement/pre-push",
    "templates/enforcement/sdlc-gate.yml": "enforcement/sdlc-gate.yml",
    "LICENSE": "LICENSE",
    "SOURCES.md": "SOURCES.md",
}

EXECUTABLE = {"guards/protect-paths.sh", "guards/block-credentials.sh", "guards/require-release-auth.sh",
              "guards/format-file.sh", "guards/hookio.py", "enforcement/spec_gate.py",
              "enforcement/pre-push", "monitor/watch-metrics.sh", "install.py"}

# ----------------------------------------------------------------------------
# Vocabulary: Claude Code -> any agent. Applied in order; specific before
# general. The leak check below catches anything this table misses.
# ----------------------------------------------------------------------------

PHRASES: list[tuple[str, str]] = [
    # Paths inside the plugin -> paths inside the target repository
    (r"\$\{CLAUDE_PLUGIN_ROOT\}/templates/monitor/watch-metrics\.sh", ".sdlc/monitor/watch-metrics.sh"),
    (r"\$\{CLAUDE_PLUGIN_ROOT\}/templates/(spec|plan)\.md", r".sdlc/templates/\1.md"),
    (r"`references/([a-z-]+)\.md`", r"`.sdlc/playbook/reference/\1.md`"),
    (r"`\.claude/hooks/`", "`.sdlc/guards/`"),
    (r"CLAUDE\.md", "AGENTS.md"),
    (r"`\.sdlc/guards/`, `evals/`\.", "`.sdlc/guards/`, and the spec gate in CI (`.sdlc/enforcement/`)."),

    # Skills and agents -> playbook files
    (r"run the\s+\*\*sdlc-setup-guardrails\*\* skill", "follow `.sdlc/playbook/setup.md`"),
    (r"\| Skill to invoke \|", "| Read and follow |"),
    (r"\| \*\*Skill\*\* \|", "| **Playbook** |"),
    (r"4\. \*\*Invoke the stage skill\.\*\* Do not inline its work here\.",
     "4. **Read and follow the stage's playbook file.** Do not improvise its procedure."),
    (r"\| Pass \| Subagent \|", "| Pass | Instructions |"),
    (r"Read by the `sdlc-deploy-review` skill", "Read by stage 4 (`.sdlc/playbook/4-deploy.md`)"),
    (r"Each addition needs a subagent in the plugin's agents/ directory\.",
     "Each addition needs a pass file in `.sdlc/playbook/review-passes/`."),
    (r"as further subagents, and list them in REVIEW\.md\.",
     "as further pass files in `.sdlc/playbook/review-passes/`, and list them in REVIEW.md."),
    (r"Launch them as subagents simultaneously — they are independent:",
     "They are independent: run them in parallel as subagents where your agent supports that, otherwise one after another:"),

    # Claude Code modes -> what they mean
    (r"### 1\. Enter plan mode", "### 1. Plan read-only"),
    (r"Only then\s+leave plan mode\.", "Only then start editing."),
    (r"In plan mode \(read-only\),", "Working read-only — in your agent's planning mode, if it has one —"),
    (r"Plan mode enforces it\.", "Planning read-only enforces it."),
    (r"Free — auto mode, parallel sessions", "Free — autonomous edits, parallel sessions"),
    (r"Auto mode is appropriate", "Letting the agent edit without per-change approval is appropriate"),
    (r"## Subagents\n", "## Subagents, where your agent has them\n"),
    (r"Hooks should block agent edits to test files during a fix\.",
     "Where your agent supports it, a hook should block edits to test files during a fix; everywhere else this rule is yours to hold."),

    # Skills as a concept -> rules
    (r"standards skills", "standards rules"),
    (r"\bA skill\b", "A rule"),
    (r"\ba skill\b", "a rule"),
    (r"\bskills\b", "rules"),

    (r"\bClaude session\b", "agent session"),

    # Claude as the actor -> the agent. Capitalized at the start of a sentence,
    # a list item, a table cell, a heading or a bold run.
    (r"(^|(?<=[.!?] )|(?<=^- )|(?<=\| )|(?<=\*\*)|(?<=## )|(?<=# ))Claude's", "The agent's"),
    (r"(^|(?<=[.!?] )|(?<=^- )|(?<=\| )|(?<=\*\*)|(?<=## )|(?<=# ))Claude\b", "The agent"),
    (r"(?<=; )Claude\b", "the agent"),
    (r"\bClaude's\b", "the agent's"),
    (r"\bClaude\b", "the agent"),
]

# Anything matching these in the output fails the build, unless the file and
# line are allowed below.
LEAKS = [
    r"\bClaude\b", r"CLAUDE", r"\.claude/", r"claude plugin", r"\bplan mode\b", r"\bauto mode\b",
    r"SKILL\.md", r"\bskills?\b", r"\bplugin\b",
    r"\bsdlc-(design-spec|build-plan|test-verify|deploy-review|maintain-monitor|orchestrator|setup-guardrails|review-bugs|review-security|review-spec)\b",
]

# file -> regexes; a leaking line is allowed if it matches one of them.
ALLOWED = {
    "SOURCES.md": [r".*"],                      # the provenance record names its sources
    "README.md": [r"ai-native-sdlc", r"Claude Code", r"CLAUDE\.md",
                  r"stage skills that load on", r"`claude plugin eval`"],  # describing the Claude version
    "AGENTS.md": [r"ai-native-sdlc"],
    "install.py": [r"Claude Code", r"CLAUDE\.md", r"ai-native-sdlc", r"claude"],
    "playbook/setup.md": [r"Claude Code", r"CLAUDE\.md", r"ai-native-sdlc"],
    "templates/AGENTS.md": [r"Claude Code reads", r"CLAUDE\.md"],
    "guards/protect-paths.sh": [r'"CLAUDE\.md"', r'"\.claude/"'],   # protecting another agent's files is correct
    "enforcement/spec_gate.py": [r'"\.claude/\*\*"'],
    "guards/hookio.py": [r"Claude"],                # names Claude Code as one dialect it speaks
    "guards/format-file.sh": [r"Claude Code"],
}

PATH_REF = re.compile(r"\.sdlc/(playbook|templates|guards|enforcement|monitor)/([A-Za-z0-9_./<>-]*[A-Za-z0-9_-])")

# ----------------------------------------------------------------------------


def split_front_matter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not match:
        return "", text
    return match.group(1), text[match.end():]


def description_of(front: str) -> str:
    match = re.search(r"^description:\s*[>|]-?\s*\n((?:[ \t]+.*\n?)+)", front, re.M)
    if match:
        lines = [line.strip() for line in match.group(1).splitlines()]
        text = " ".join(line for line in lines if line)
    else:
        match = re.search(r"^description:\s*(.+)$", front, re.M)
        text = match.group(1).strip() if match else ""
    text = re.sub(r"^This skill should be used ", "Use ", text)
    return text


def transform(text: str) -> str:
    for pattern, replacement in PHRASES:
        text = re.sub(pattern, replacement, text, flags=re.M)
    for name, target in sorted(NAME_MAP.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"`{re.escape(name)}`", f"`{target}`", text)
        text = re.sub(rf"\*\*{re.escape(name)}\*\*", f"`{target}`", text)
        text = re.sub(rf"\b{re.escape(name)}\b", target, text)
    return text


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{[a-z_]+\}\}", text)
    if leftover:
        raise SystemExit(f"build_mirror: unrendered placeholders {sorted(set(leftover))}")
    return text


def write(out: Path, rel: str, text: str) -> None:
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_table_rows(text: str, heading: str) -> list[list[str]]:
    section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not section:
        raise SystemExit(f"build_mirror: section '## {heading}' not found")
    rows = []
    for line in section.group(1).splitlines():
        if line.startswith("|") and not re.match(r"^\|[-\s|]+\|$", line):
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows[1:]  # drop header


def stage_facts() -> dict[int, dict[str, str]]:
    """Gate and owner per stage, from the orchestrator; output, from the stage map."""
    orchestrator = (ROOT / "skills/sdlc-orchestrator/SKILL.md").read_text(encoding="utf-8")
    stage_map = (ROOT / "skills/sdlc-orchestrator/references/stage-map.md").read_text(encoding="utf-8")
    facts: dict[int, dict[str, str]] = {}
    for stage, gate, owner in parse_table_rows(orchestrator, "Gate owners"):
        n = int(stage.split()[0])
        facts[n] = {"gate": gate, "owner": owner}
    for n, _, title, _ in STAGES:
        block = re.search(rf"^## Stage {n} — {title}\n(.*?)(?=^## |\Z)", stage_map, re.S | re.M)
        if not block:
            raise SystemExit(f"build_mirror: stage {n} missing from stage-map.md")
        output = re.search(r"^\| \*\*Output\*\* \| (.+?) \|$", block.group(1), re.M)
        facts.setdefault(n, {})["output"] = output.group(1) if output else ""
    return facts


def build_rules(out: Path, facts: dict[int, dict[str, str]]) -> None:
    for n, key, title, skill in STAGES:
        front, _ = split_front_matter((ROOT / f"skills/{skill}/SKILL.md").read_text(encoding="utf-8"))
        description = transform(description_of(front)).replace('"', "'")
        body = (
            f"# SDLC stage {n} — {title}\n\n"
            f"Before doing any work in this stage, read `.sdlc/playbook/{n}-{key}.md`\n"
            f"and follow it step by step.\n\n"
            f"**Produces:** {facts[n]['output']}\n\n"
            f"**Gate:** {facts[n]['gate']}. **Decided by:** {facts[n]['owner']}.\n"
            f"Stop at the gate and ask. Never approve on a human's behalf, and never\n"
            f"start the next stage in the same turn as the request for approval.\n"
        )
        write(out, f"adapters/cursor/rules/sdlc-{n}-{key}.mdc",
              f'---\ndescription: "{description}"\nalwaysApply: false\n---\n\n{body}')
        write(out, f"adapters/copilot/instructions/sdlc-{n}-{key}.instructions.md",
              f'---\nname: "SDLC stage {n} — {title}"\ndescription: "{description}"\n---\n\n{body}')


def build_agents_md(out: Path, facts: dict[int, dict[str, str]], values: dict[str, str]) -> None:
    """templates/AGENTS.md: the repo-knowledge template plus the managed lifecycle block."""
    knowledge = transform((ROOT / "templates/CLAUDE.md").read_text(encoding="utf-8"))
    knowledge = knowledge.split("\n## Lifecycle", 1)[0].rstrip() + "\n"
    rows = "\n".join(
        f"| {n} | {title} | `.sdlc/playbook/{n}-{key}.md` | {facts[n]['output']} | {facts[n]['gate']} — {facts[n]['owner']} |"
        for n, key, title, _ in STAGES
    )
    block = render((ROOT / "mirror/lifecycle-block.md").read_text(encoding="utf-8"),
                   {**values, "stage_table": rows})
    write(out, "templates/AGENTS.md", knowledge + "\n" + block)


def build_review_passes(out: Path) -> None:
    for agent, key, title in REVIEW_PASSES:
        _, body = split_front_matter((ROOT / f"agents/{agent}.md").read_text(encoding="utf-8"))
        header = (
            f"# Review pass — {title}\n\n"
            f"Run this pass against the diff during stage 4. Where your agent supports\n"
            f"subagents, run each pass as its own subagent, in parallel, with only this\n"
            f"file as its instructions; otherwise run the passes one after another.\n\n"
        )
        write(out, f"playbook/review-passes/{key}.md", header + transform(body.lstrip()))


def build(out: Path, source_commit: str) -> None:
    version = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
    values = {"version": version, "source_repo": SOURCE_REPO, "mirror_repo": MIRROR_REPO,
              "source_commit": source_commit}

    if out.exists():
        for child in out.iterdir():
            if child.name == ".git":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    out.mkdir(parents=True, exist_ok=True)

    for src, dst in TRANSFORMED.items():
        text = (ROOT / src).read_text(encoding="utf-8")
        if src.startswith("skills/"):
            _, text = split_front_matter(text)
            text = text.lstrip()
        write(out, dst, transform(text))

    for src, dst in COPIED.items():
        (out / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src, out / dst)

    overlay = ROOT / "mirror/overlay"
    for path in sorted(overlay.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(overlay).as_posix()
        if rel.endswith(".tmpl"):
            write(out, rel[: -len(".tmpl")], render(path.read_text(encoding="utf-8"), values))
        else:
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, out / rel)

    facts = stage_facts()
    build_rules(out, facts)
    build_agents_md(out, facts, values)
    build_review_passes(out)

    write(out, "playbook/VERSION", version + "\n")
    write(out, ".mirror-source.json", json.dumps(
        {"generated_from": f"https://github.com/{SOURCE_REPO}", "source_commit": source_commit,
         "version": version, "do_not_edit": "Regenerate with scripts/build_mirror.py in the source repository."},
        indent=2) + "\n")

    for rel in EXECUTABLE:
        if (out / rel).exists():
            (out / rel).chmod(0o755)


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------


def check(out: Path) -> list[str]:
    problems: list[str] = []
    text_files = [p for p in out.rglob("*") if p.is_file() and ".git" not in p.parts]

    leak = re.compile("|".join(f"(?:{p})" for p in LEAKS))
    for path in text_files:
        rel = path.relative_to(out).as_posix()
        if rel == ".mirror-source.json":
            continue
        allowed = [re.compile(a) for a in ALLOWED.get(rel, [])]
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if leak.search(line) and not any(a.search(line) for a in allowed):
                problems.append(f"leak  {rel}:{number}: {line.strip()[:110]}")

    roots = {"playbook": "playbook", "templates": "templates", "guards": "guards",
             "enforcement": "enforcement", "monitor": "monitor"}
    for path in text_files:
        if path.suffix not in {".md", ".mdc", ".json", ".py", ".sh", ".yml", ""}:
            continue
        rel = path.relative_to(out).as_posix()
        for kind, ref in PATH_REF.findall(path.read_text(encoding="utf-8", errors="replace")):
            if "<" in ref or ref.endswith("/") or not ref:
                continue
            if not (out / roots[kind] / ref).exists():
                problems.append(f"ref   {rel}: .sdlc/{kind}/{ref} does not exist in the mirror")

    for path in text_files:
        rel = path.relative_to(out).as_posix()
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"json  {rel}: {exc}")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True, cfile=str(out / ".pycheck"))
            except py_compile.PyCompileError as exc:
                problems.append(f"py    {rel}: {exc.msg}")
        if path.suffix == ".sh" or rel == "enforcement/pre-push":
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                problems.append(f"sh    {rel}: {result.stderr.strip()}")
        if path.suffix == ".mdc" or path.name.endswith(".instructions.md"):
            front, _ = split_front_matter(path.read_text(encoding="utf-8"))
            if not re.search(r'^description: ".+"$', front, re.M):
                problems.append(f"front {rel}: missing or unquoted description")
    (out / ".pycheck").unlink(missing_ok=True)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the agent-agnostic mirror.")
    parser.add_argument("--out", required=True, help="output directory (replaced, except .git)")
    parser.add_argument("--source-commit", help="source commit to record (default: git HEAD)")
    args = parser.parse_args()

    commit = args.source_commit
    if not commit:
        result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True)
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"

    out = Path(args.out).resolve()
    if out == ROOT or ROOT in out.parents and (out / ".claude-plugin").exists():
        print("build_mirror: refusing to build into the source repository", file=sys.stderr)
        return 2

    build(out, commit)
    problems = check(out)
    files = sum(1 for p in out.rglob("*") if p.is_file() and ".git" not in p.parts)
    if problems:
        print(f"build_mirror: {len(problems)} problem(s) in {out}", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(f"build_mirror: {files} files written to {out}, all checks passed (source {commit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
