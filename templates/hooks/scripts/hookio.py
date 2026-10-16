#!/usr/bin/env python3
"""Shared input/output for the guard scripts, in every agent's hook dialect.

The guard scripts decide; this module reads the event they were given and
writes the decision in the shape the calling agent expects. One policy, one
script per guard, any agent.

  hookio.py field <tool_name|command|file_path>   read stdin, print the field
  hookio.py writeish                              exit 0 if the tool writes (or is unknown)
  hookio.py emit <format> allow|deny [reason]     print the decision, exit with its code

Formats
  claude   Claude Code      JSON hookSpecificOutput.permissionDecision, exit 0
  cursor   Cursor           JSON {"permission": ...}, exit 0
  copilot  GitHub Copilot   allow: silent exit 0 / deny: JSON + stderr + exit 2
                            (exit 2 is a deny in VS Code, the Copilot CLI and
                            the Copilot cloud agent alike)
  exit     anything else    allow: exit 0 / deny: reason on stderr, exit 2

Input shapes differ between agents and harnesses, so field lookup is tolerant:
snake_case and camelCase envelopes, tool arguments nested or top-level, and
tool arguments delivered as a JSON string.
"""

from __future__ import annotations

import json
import re
import sys

FORMATS = ("claude", "cursor", "copilot", "exit")

# Tool names that write, across agents: Claude (Write, Edit, NotebookEdit),
# Cursor (Write, Delete), Copilot (names vary by harness).
WRITE_TOOL = re.compile(
    r"write|edit|create|replace|delete|remove|patch|apply|insert|move|rename|notebook",
    re.IGNORECASE,
)

PATH_KEYS = ("file_path", "filePath", "path", "target_file", "targetFile", "filename", "file")
COMMAND_KEYS = ("command", "cmd")


def _load_event() -> dict:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _tool_input(event: dict) -> dict:
    for key in ("tool_input", "toolInput", "toolArgs", "tool_args"):
        value = event.get(key)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        if isinstance(value, dict):
            return value
    return {}


def _first(mapping: dict, keys) -> str:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def field(event: dict, name: str) -> str:
    args = _tool_input(event)
    if name == "tool_name":
        return _first(event, ("tool_name", "toolName"))
    if name == "command":
        return _first(args, COMMAND_KEYS) or _first(event, COMMAND_KEYS)
    if name == "file_path":
        return _first(args, PATH_KEYS) or _first(event, PATH_KEYS)
    raise SystemExit(f"hookio: unknown field {name!r}")


def emit(fmt: str, decision: str, reason: str = "") -> int:
    if fmt not in FORMATS:
        print(f"hookio: unknown format {fmt!r}; expected one of {', '.join(FORMATS)}", file=sys.stderr)
        return 2  # fail closed
    deny = decision == "deny"

    if fmt == "claude":
        if not deny and not reason:
            print('{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}')
        else:
            out = {"hookEventName": "PreToolUse", "permissionDecision": decision}
            if reason:
                out["permissionDecisionReason"] = reason
            print(json.dumps({"hookSpecificOutput": out}))
        return 0

    if fmt == "cursor":
        out = {"permission": decision}
        if deny:
            out["user_message"] = reason
            out["agent_message"] = reason
        print(json.dumps(out))
        return 0

    if fmt == "copilot":
        if not deny:
            return 0
        print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason}))
        print(reason, file=sys.stderr)
        return 2

    # exit
    if deny:
        print(reason, file=sys.stderr)
        return 2
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    command = argv[1]
    if command == "field" and len(argv) == 3:
        print(field(_load_event(), argv[2]))
        return 0
    if command == "writeish":
        tool = field(_load_event(), "tool_name")
        return 0 if (not tool or WRITE_TOOL.search(tool)) else 1
    if command == "emit" and len(argv) in (4, 5):
        return emit(argv[2], argv[3], argv[4] if len(argv) == 5 else "")
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
