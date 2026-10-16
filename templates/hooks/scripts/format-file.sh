#!/usr/bin/env bash
# PostToolUse hook: formats the file that was just written, so style never
# reaches review. Post-edit hooks cannot block — this formats and stays quiet.
#
# Input : the hook event JSON on stdin (uses the target file path)
# Output: nothing; exit 0 always, so a formatter failure never derails the
#         session. Works unchanged for Claude Code, Cursor (afterFileEdit) and
#         Copilot (postToolUse).
#
# Copy this directory (with hookio.py) into the repo and set the formatters.
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$(cat)"

FILE_PATH="$(printf '%s' "$INPUT" | python3 "$DIR/hookio.py" field file_path)"

[ -z "$FILE_PATH" ] && exit 0
[ -f "$FILE_PATH" ] || exit 0

# TODO: replace with this repo's formatters. Anything not listed is left alone.
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.md)
    command -v prettier >/dev/null 2>&1 && prettier --write "$FILE_PATH" >/dev/null 2>&1
    ;;
  *.py)
    command -v ruff >/dev/null 2>&1 && ruff format "$FILE_PATH" >/dev/null 2>&1
    ;;
  *.go)
    command -v gofmt >/dev/null 2>&1 && gofmt -w "$FILE_PATH" >/dev/null 2>&1
    ;;
  *.rs)
    command -v rustfmt >/dev/null 2>&1 && rustfmt "$FILE_PATH" >/dev/null 2>&1
    ;;
esac

exit 0
