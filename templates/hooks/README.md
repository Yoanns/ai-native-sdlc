# Hooks

Skills advise; hooks enforce. Any policy that must always hold gets a hook
behind the skill that describes it.

## Installing

Two supported homes for this configuration — pick one:

1. **`.claude/settings.json`** — merge the `hooks` key from `hooks.json`
   into the repo's settings file. This is the usual place for project hooks
   and the one teammates get when they clone the repo.
2. **`.claude/hooks/hooks.json`** — keep it as its own file, with the same
   `{"hooks": {...}}` wrapper.

Either way, copy `hooks/scripts/*.sh` to `.claude/hooks/scripts/` and
`chmod +x` them.

## What each hook does

| Event | Matcher | Hook | Effect |
|---|---|---|---|
| PreToolUse | `Write\|Edit\|NotebookEdit` | `protect-paths.sh` | Denies edits to migrations, generated code, infrastructure, vendored code, and the guardrail files themselves |
| PreToolUse | `Write\|Edit` | prompt hook | Denies edits that would weaken a test during a bug fix |
| PreToolUse | `Bash` | `block-credentials.sh` | Denies commands that read credential material |
| PreToolUse | `Bash` | `require-release-auth.sh` | Denies production deploys without a named human authorization |
| PostToolUse | `Write\|Edit` | `format-file.sh` | Formats the written file, so style never reaches review |
| Stop | — | prompt hook | Checks build, tests, lint and evals before the session reports done |

## The contract these scripts implement

Each script reads the hook input as JSON on **stdin**. The fields used here:

| Field | Meaning |
|---|---|
| `tool_name` | The tool being called, e.g. `Bash`, `Edit` |
| `tool_input.file_path` | Target path, for file tools |
| `tool_input.command` | The command line, for `Bash` |
| `cwd` | Working directory of the session |

Each script writes a decision as JSON on **stdout** and exits 0:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
```

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse",
 "permissionDecision":"deny",
 "permissionDecisionReason":"Explanation shown to the user and to Claude"}}
```

`permissionDecision: "deny"` blocks the call. Exiting 2 also blocks, with
stderr as the reason — the JSON form is preferred because the reason reaches
Claude as context it can act on.

PostToolUse cannot block; it can only add context, so `format-file.sh`
formats and stays quiet.

## Before trusting any of this

Trigger every hook once and watch it fire. An untested hook is a comment.

```bash
# protected path
echo '{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"db/migrations/001_init.sql"}}' \
  | .claude/hooks/scripts/protect-paths.sh

# credential read
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"cat .env"}}' \
  | .claude/hooks/scripts/block-credentials.sh

# unauthorized production deploy
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"make deploy-production"}}' \
  | .claude/hooks/scripts/require-release-auth.sh
```

Each should print a `deny` decision with a readable reason.
