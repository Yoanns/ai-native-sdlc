#!/usr/bin/env bash
# PreToolUse hook: denies shell commands that would read credential material.
# Settings deny direct reads where the agent supports it; this catches
# indirect access through the shell.
#
# Input : the hook event JSON on stdin (uses the shell command)
# Output: a decision in the calling agent's dialect — see hookio.py
#
# Copy this directory (with hookio.py) into the repo and extend PATTERNS.
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
