#!/usr/bin/env python3
"""Validate every file in this plugin against its documented schema.

Checks, in order:
  - plugin.json and marketplace.json shape
  - SKILL.md frontmatter: allowed keys only, name matches directory,
    description within the 1,536-character limit
  - agent frontmatter: valid YAML (the <example> trap), allowed keys only,
    name matches filename
  - eval cases and graders: allowed keys, known grader types, compilable regexes
  - hooks.json: top-level "hooks" wrapper, known event names, known hook keys,
    prompt hooks carrying $ARGUMENTS
  - settings.json: known top-level keys, well-formed permission rules,
    no invented sandbox keys
  - shell scripts: bash syntax
  - every ${CLAUDE_PLUGIN_ROOT} reference resolves

Key sets come from the Claude Code documentation cited in SOURCES.md. If a
documented format changes, update the constants below first.

Usage: python3 scripts/validate.py [plugin-root]
Exit:  0 all checks passed, 1 otherwise.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

SKILL_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
AGENT_KEYS = {
    "name", "description", "tools", "disallowedTools", "model",
    "permissionMode", "maxTurns", "skills", "mcpServers", "hooks", "memory",
    "background", "omitClaudeMd", "effort", "isolation", "color",
    "initialPrompt", "experimental",
}
CASE_KEYS = {
    "schema_version", "name", "description", "tags", "plugins", "runs",
    "expected_outcome", "model", "max_turns", "timeout_seconds",
    "allowed_tools", "append_system_prompt",
}
GRADER_KEYS = {
    "type", "weight", "arm", "pattern", "flags", "match", "target", "tool",
    "input_match", "min", "max", "before", "after", "path", "exists",
    "criteria", "focus", "baseline_file",
}
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}
HOOK_EVENTS = {
    "SessionStart", "SessionEnd", "Setup", "UserPromptSubmit",
    "UserPromptExpansion", "Stop", "StopFailure", "PreToolUse", "PostToolUse",
    "PostToolUseFailure", "PermissionRequest", "PermissionDenied",
    "PostToolBatch", "PreCompact", "PostCompact", "Notification",
    "SubagentStart", "SubagentStop",
}
HOOK_KEYS = {
    "type", "command", "args", "timeout", "statusMessage", "prompt", "model",
    "async", "asyncRewake", "shell", "if", "once",
}
HOOK_TYPES = {"command", "prompt", "http", "mcp_tool", "agent"}
SETTINGS_KEYS = {
    "$schema", "permissions", "sandbox", "hooks", "env", "model",
    "enabledPlugins", "statusLine",
}

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"ok    {msg}")


def frontmatter(path: str):
    text = open(path, encoding="utf-8").read()
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not match:
        return None, text
    try:
        return yaml.safe_load(match.group(1)), text[match.end():]
    except yaml.YAMLError as exc:
        fail(f"{path}: frontmatter is not valid YAML — {str(exc).splitlines()[0]}")
        return False, text


def check_manifests() -> None:
    manifest = json.load(open(".claude-plugin/plugin.json", encoding="utf-8"))
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", manifest.get("name", "")):
        fail("plugin.json: name is not kebab-case")
    elif not isinstance(manifest.get("author", {}), dict):
        fail("plugin.json: author must be an object")
    else:
        ok(f"plugin.json: {manifest['name']} v{manifest.get('version', '?')}")

    market_path = ".claude-plugin/marketplace.json"
    if not os.path.exists(market_path):
        return
    market = json.load(open(market_path, encoding="utf-8"))
    for field in ("name", "owner", "plugins"):
        if field not in market:
            fail(f"marketplace.json: missing required field {field}")
    if not isinstance(market.get("owner", {}), dict) or "name" not in market.get("owner", {}):
        fail("marketplace.json: owner must be an object with a name")
    entries = market.get("plugins", [])
    bad = [e for e in entries if "name" not in e or "source" not in e]
    for entry in bad:
        fail(f"marketplace.json: plugin entry needs both name and source: {entry}")
    if not bad:
        ok(f"marketplace.json: {len(entries)} plugin entry/entries")


def check_skills() -> None:
    for path in sorted(glob.glob("skills/*/SKILL.md")):
        data, body = frontmatter(path)
        base = os.path.basename(os.path.dirname(path))
        if data is None:
            fail(f"{path}: no frontmatter")
            continue
        if data is False:
            continue
        unknown = set(data) - SKILL_KEYS
        if unknown:
            fail(f"{path}: unknown frontmatter keys {sorted(unknown)} (these are a hard error)")
        elif data.get("name") != base:
            fail(f"{path}: name '{data.get('name')}' does not match directory '{base}'")
        elif len(str(data.get("description", ""))) > 1536:
            fail(f"{path}: description exceeds the 1536-character limit")
        else:
            ok(f"skill {base}: {len(str(data['description']))}-char description, {len(body.split())}-word body")


def check_agents() -> None:
    for path in sorted(glob.glob("agents/*.md")):
        data, _ = frontmatter(path)
        base = os.path.basename(path)[:-3]
        if data is None:
            fail(f"{path}: no frontmatter")
            continue
        if data is False:
            continue
        unknown = set(data) - AGENT_KEYS
        if unknown:
            fail(f"{path}: unknown frontmatter keys {sorted(unknown)}")
        elif data.get("name") != base:
            fail(f"{path}: name '{data.get('name')}' does not match filename '{base}'")
        elif not isinstance(data.get("description"), str):
            fail(f"{path}: description must be a string — use a literal block scalar for multi-line text")
        else:
            ok(f"agent {base}: tools={data.get('tools')!r}")


def check_eval_cases() -> None:
    for root in ("evals", "templates/evals"):
        for path in sorted(glob.glob(f"{root}/*/prompt.md")):
            case_dir = os.path.dirname(path)
            data, body = frontmatter(path)
            if not data:
                fail(f"{path}: missing or invalid frontmatter")
                continue
            unknown = set(data) - CASE_KEYS
            if unknown:
                fail(f"{path}: unknown case keys {sorted(unknown)}")
            elif not body.strip():
                fail(f"{path}: empty prompt body")
            else:
                ok(f"case {case_dir}")

            graders = glob.glob(os.path.join(case_dir, "graders", "*.md"))
            if not graders:
                fail(f"{case_dir}: no graders")
            for grader in sorted(graders):
                gdata, _ = frontmatter(grader)
                if not gdata:
                    fail(f"{grader}: missing or invalid frontmatter")
                    continue
                unknown = set(gdata) - GRADER_KEYS
                if unknown:
                    fail(f"{grader}: unknown grader keys {sorted(unknown)}")
                elif gdata.get("type") not in GRADER_TYPES:
                    fail(f"{grader}: unknown grader type {gdata.get('type')!r}")
                else:
                    ok(f"  grader {os.path.basename(grader)}: {gdata['type']}")
                if gdata.get("type") == "regex":
                    try:
                        re.compile(gdata.get("pattern", ""))
                    except re.error as exc:
                        fail(f"{grader}: uncompilable regex — {exc}")


def check_hooks() -> None:
    path = "templates/hooks.json"
    if not os.path.exists(path):
        return
    config = json.load(open(path, encoding="utf-8"))
    if set(config) != {"hooks"}:
        fail(f"{path}: top-level keys {sorted(config)} — events must be wrapped in a 'hooks' key")
        return
    for event, groups in config["hooks"].items():
        if event not in HOOK_EVENTS:
            fail(f"{path}: unknown event {event!r} (skipped with a warning at load time)")
        for group in groups:
            unknown = set(group) - {"matcher", "hooks"}
            if unknown:
                fail(f"{path}/{event}: unknown group keys {sorted(unknown)}")
            for hook in group.get("hooks", []):
                unknown = set(hook) - HOOK_KEYS
                if unknown:
                    fail(f"{path}/{event}: unknown hook keys {sorted(unknown)}")
                if hook.get("type") not in HOOK_TYPES:
                    fail(f"{path}/{event}: unknown hook type {hook.get('type')!r}")
                if hook.get("type") == "prompt" and "$ARGUMENTS" not in hook.get("prompt", ""):
                    fail(f"{path}/{event}: prompt hook does not include $ARGUMENTS, so it never sees the event")
    ok(f"{path}: wrapper, events, and hook entries valid")


def check_settings() -> None:
    path = "templates/settings.json"
    if not os.path.exists(path):
        return
    settings = json.load(open(path, encoding="utf-8"))
    unknown = set(settings) - SETTINGS_KEYS
    if unknown:
        fail(f"{path}: unexpected top-level keys {sorted(unknown)}")
    for bucket in ("allow", "deny", "ask"):
        for rule in settings.get("permissions", {}).get(bucket, []):
            if not re.fullmatch(r"[A-Za-z]+\(.+\)", rule):
                fail(f"{path}: malformed permission rule {rule!r} — skipped silently at load time")
    if "allowlist" in json.dumps(settings.get("sandbox", {})):
        fail(f"{path}: sandbox uses 'allowlist'; the documented key is network.allowedDomains")
    else:
        ok(f"{path}: keys and permission rules valid")


def check_shell() -> None:
    for script in sorted(glob.glob("templates/**/*.sh", recursive=True)):
        result = subprocess.run(["bash", "-n", script], capture_output=True, text=True)
        if result.returncode == 0:
            ok(f"{script}: bash syntax")
        else:
            fail(f"{script}: {result.stderr.strip()}")


def check_references() -> None:
    broken = False
    for path in glob.glob("**/*.md", recursive=True):
        text = open(path, encoding="utf-8").read()
        for ref in set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w\-./]+)", text)):
            if not os.path.exists(ref):
                fail(f"{path}: broken reference to {ref}")
                broken = True
    if not broken:
        ok("all ${CLAUDE_PLUGIN_ROOT} references resolve")


def main() -> int:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..")
    os.chdir(root)
    print(f"Validating plugin at {os.getcwd()}\n")

    check_manifests()
    check_skills()
    check_agents()
    check_eval_cases()
    check_hooks()
    check_settings()
    check_shell()
    check_references()

    print()
    if failures:
        print(f"RESULT: FAIL — {len(failures)} problem(s)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
