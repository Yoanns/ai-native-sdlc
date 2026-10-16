#!/usr/bin/env bash
# PreToolUse hook: production deploys require a named human authorization.
# Development is free, staging is controlled, production is gated — this is
# the gate.
#
# Input : the hook event JSON on stdin (uses the shell command)
# Output: a decision in the calling agent's dialect — see hookio.py
#
# Copy this directory (with hookio.py) into the repo and set DEPLOY_PATTERNS.
set -euo pipefail

# Hook dialect: --format claude|cursor|copilot|exit, or SDLC_HOOK_FORMAT.
# Defaults to claude. The policy below is the same in every dialect;
# hookio.py reads the event and writes the decision the calling agent expects.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORMAT="${SDLC_HOOK_FORMAT:-claude}"
while [ $# -gt 0 ]; do
  case "$1" in
    --format)   FORMAT="${2:-}"; shift 2 ;;
    --format=*) FORMAT="${1#*=}"; shift ;;
    *)          shift ;;
  esac
done

INPUT="$(cat)"
field() { printf '%s' "$INPUT" | python3 "$DIR/hookio.py" field "$1"; }
allow() { python3 "$DIR/hookio.py" emit "$FORMAT" allow "${1:-}"; exit $?; }
deny()  { python3 "$DIR/hookio.py" emit "$FORMAT" deny "$1"; exit $?; }

CMD="$(field command)"
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
  allow "Production release authorized by ${RELEASE_AUTHORIZED_BY}."
fi

deny "This is a production deploy and no named human authorization is present. A release manager must authorize it (set RELEASE_AUTHORIZED_BY, or run the approved release workflow). An AI agent cannot authorize its own deploy."
