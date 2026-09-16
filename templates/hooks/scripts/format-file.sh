#!/usr/bin/env bash
# PostToolUse hook: formats the file that was just written, so style never
# reaches review. PostToolUse cannot block — it formats and stays quiet.
#
# Input : hook JSON on stdin (uses tool_input.file_path)
# Output: nothing on success; exit 0 always, so a formatter failure never
#         derails the session.
#
# Copy to .claude/hooks/scripts/ and set the formatter for each extension.
set -uo pipefail

INPUT="$(cat)"

FILE_PATH="$(printf '%s' "$INPUT" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print((d.get("tool_input") or {}).get("file_path",""))
')"

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
