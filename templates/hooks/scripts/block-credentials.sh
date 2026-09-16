#!/usr/bin/env bash
# PreToolUse hook: denies shell commands that would read credential material.
# Settings deny direct reads; this catches indirect access through the shell.
#
# Input : hook JSON on stdin (uses tool_input.command)
# Output: PreToolUse permissionDecision JSON on stdout
#
# Copy to .claude/hooks/scripts/ and extend PATTERNS for this repo.
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

CMD="$(printf '%s' "$INPUT" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print((d.get("tool_input") or {}).get("command",""))
')"

[ -z "$CMD" ] && allow

# TODO: extend with this repo's credential locations and secret managers.
PATTERNS=(
  '\.env'
  'id_rsa'
  'id_ed25519'
  '\.pem\b'
  '\.p12\b'
  'credentials\.json'
  '\.aws/'
  '\.kube/config'
  '\.npmrc'
  '\.pypirc'
  'secrets?/'
)

for p in "${PATTERNS[@]}"; do
  if printf '%s' "$CMD" | grep -Eq "$p"; then
    deny "This command touches credential material (matched /$p/). Reading or copying secrets is blocked. If the task needs a credential, describe what it needs and let a person provide it through the approved secret manager."
  fi
done

allow
