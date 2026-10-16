#!/usr/bin/env bash
# PreToolUse hook: denies agent edits to paths that must only change under
# explicit human instruction.
#
# Input : the hook event JSON on stdin (uses the target file path)
# Output: a decision in the calling agent's dialect — see hookio.py
#
# Copy this directory (with hookio.py) into the repo and edit PROTECTED below.
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

FILE_PATH="$(field file_path)"
[ -z "$FILE_PATH" ] && allow

# Agents whose hook config cannot filter by tool (Copilot) send every tool
# call here, reads included. Only writes are policed; reading is not editing.
if [ "$FORMAT" != "claude" ] && ! printf '%s' "$INPUT" | python3 "$DIR/hookio.py" writeish; then
  allow
fi

# TODO: replace with this repo's real protected paths.
PROTECTED=(
  "db/migrations/"
  "/generated/"
  "infra/"
  "vendor/"
  ".github/workflows/"
  "CLAUDE.md"
  "AGENTS.md"
  "REVIEW.md"
  ".claude/"
  ".cursor/"
  ".github/hooks/"
  ".sdlc/guards/"
)

for pattern in "${PROTECTED[@]}"; do
  case "$FILE_PATH" in
    *"$pattern"*)
      deny "$FILE_PATH is a protected path (matched '$pattern'). Changes here need explicit human instruction. Say what you want to change and why, and let a person make the call."
      ;;
  esac
done

allow
