#!/usr/bin/env bash
# PreToolUse hook: production deploys require a named human authorization.
# Development is free, staging is controlled, production is gated — this is
# the gate.
#
# Input : hook JSON on stdin (uses tool_input.command)
# Output: PreToolUse permissionDecision JSON on stdout
#
# Copy to .claude/hooks/scripts/ and set DEPLOY_PATTERNS for this repo.
set -euo pipefail

allow_with() {
  python3 -c '
import json,sys
print(json.dumps({"hookSpecificOutput":{
    "hookEventName":"PreToolUse",
    "permissionDecision":"allow",
    "permissionDecisionReason":sys.argv[1]}}))' "$1"
  exit 0
}

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

# TODO: replace with the commands that actually reach production in this repo.
DEPLOY_PATTERNS=(
  'deploy.*(prod|production)'
  'kubectl.*(--context|-n).*(prod|production)'
  'terraform apply'
  'helm upgrade.*prod'
  'flyctl deploy'
  'git push.*(prod|release)'
)

is_deploy=0
for p in "${DEPLOY_PATTERNS[@]}"; do
  if printf '%s' "$CMD" | grep -Eiq "$p"; then is_deploy=1; break; fi
done

[ "$is_deploy" -eq 0 ] && allow

# A release is authorized by a named person, recorded for the duration of that
# release window. No name, no deploy.
# TODO: replace with your real authorization source — a signed release ticket,
# a CI approval step, or an entry in the release log.
if [ -n "${RELEASE_AUTHORIZED_BY:-}" ]; then
  allow_with "Production release authorized by ${RELEASE_AUTHORIZED_BY}."
fi

deny "This is a production deploy and no named human authorization is present. A release manager must authorize it (set RELEASE_AUTHORIZED_BY, or run the approved release workflow). Claude cannot authorize its own deploy."
