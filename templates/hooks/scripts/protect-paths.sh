#!/usr/bin/env bash
# PreToolUse hook: denies agent edits to paths that must only change under
# explicit human instruction.
#
# Input : hook JSON on stdin (uses tool_input.file_path)
# Output: {"hookSpecificOutput":{"hookEventName":"PreToolUse",
#          "permissionDecision":"allow"|"deny","permissionDecisionReason":"..."}}
#
# Copy to .claude/hooks/scripts/ and edit PROTECTED below.
set -euo pipefail

allow() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}\n'
  exit 0
}

deny() {
  python3 -c '
import json,sys
print(json.dumps({"hookSpecificOutput":{
    "hookEventName":"PreToolUse",
    "permissionDecision":"deny",
    "permissionDecisionReason":sys.argv[1]}}))' "$1"
  exit 0
}

INPUT="$(cat)"

FILE_PATH="$(printf '%s' "$INPUT" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print((d.get("tool_input") or {}).get("file_path",""))
')"

[ -z "$FILE_PATH" ] && allow

# TODO: replace with this repo's real protected paths.
PROTECTED=(
  "db/migrations/"
  "/generated/"
  "infra/"
  "vendor/"
  ".github/workflows/"
  "CLAUDE.md"
  "REVIEW.md"
  ".claude/"
)

for pattern in "${PROTECTED[@]}"; do
  case "$FILE_PATH" in
    *"$pattern"*)
      deny "$FILE_PATH is a protected path (matched '$pattern'). Changes here need explicit human instruction. Say what you want to change and why, and let a person make the call."
      ;;
  esac
done

allow
