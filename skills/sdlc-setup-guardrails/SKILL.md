---
name: sdlc-setup-guardrails
description: >
  This skill should be used once per repository before the SDLC is run in it,
  or when the user says "set up the SDLC", "install the guardrails", "write a
  CLAUDE.md for this repo", "set up review policy", "add the hooks", or asks
  to bootstrap agent configuration. Installs CLAUDE.md, REVIEW.md, artifact
  templates, protective hooks, settings, and the eval suite scaffold, then
  reports which TODO markers the user must still fill in.
metadata:
  version: "0.1.0"
---

# Setup — Guardrails

Install the standing configuration the five stages depend on. Run this once
per repository. Everything installed here is version-controlled and reviewed
like code, because it steers every session that follows.

## What gets installed

| File | Purpose | Enforcement |
|---|---|---|
| `CLAUDE.md` | Institutional knowledge read at every session start | Advisory |
| `REVIEW.md` | Review passes and severity thresholds | Advisory, read by Stage 4 |
| `.sdlc/TEMPLATES/spec.md`, `plan.md` | Artifact shapes | Advisory |
| `.claude/hooks/hooks.json` + scripts | Protected paths, formatting, credential blocking | **Deterministic** |
| `.claude/settings.json` | Permissions, sandbox, allowed commands | **Deterministic** |
| `evals/` | Regression suite for configuration changes | Gate in CI |

**Skills are advisory; hooks are deterministic.** Encode a policy as a skill so
it is applied while code is written. Back it with a hook wherever the policy
must always hold — a skill can be reasoned around, a hook cannot.

## Procedure

### 1. Inspect the repo first

Do not write a generic `CLAUDE.md`. Read the repo and extract the real thing:

- Build, test, lint, and run commands — from `Makefile`, `package.json`,
  `pyproject.toml`, CI workflows. Verify each one actually runs.
- Directory layout and the boundaries between modules.
- Conventions visible in the code: naming, error handling, logging, imports,
  test structure.
- Protected paths: migrations, generated code, vendored code, infrastructure,
  secrets, licence headers.
- Git history for repeated review comments — those are the "common mistakes".

### 2. Write CLAUDE.md

Copy `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md` and fill it from what was
found. Four sections, nothing else:

1. **Commands** — the exact invocations, verified to work.
2. **Conventions** — what this repo does differently from the default.
3. **Architecture** — the module map and the boundaries that matter.
4. **Common mistakes** — what goes wrong here, stated as a rule.

**Keep it under a page.** It is read in full at every session start, so every
line competes for attention with every other. Delete anything that is generic
good practice; keep only what is true of *this* repo.

### 3. Write REVIEW.md

Copy `${CLAUDE_PLUGIN_ROOT}/templates/REVIEW.md`. Define the review passes this
repo requires and the severity threshold that blocks a merge. Ask which
compliance or domain passes apply — do not assume.

### 4. Install hooks and settings

Copy `${CLAUDE_PLUGIN_ROOT}/templates/hooks/scripts/` into
`.claude/hooks/scripts/` and `chmod +x` them. Then install the hook
configuration from `${CLAUDE_PLUGIN_ROOT}/templates/hooks.json` — either merge
its `hooks` key into `.claude/settings.json`, or keep it as
`.claude/hooks/hooks.json` with the same `{"hooks": {...}}` wrapper.

Copy `${CLAUDE_PLUGIN_ROOT}/templates/settings.json` into `.claude/`. It ships
with valid entries only: a malformed permission rule is skipped with a warning
rather than failing loudly, so placeholders inside it would silently do
nothing. The decisions still to make are listed in
`${CLAUDE_PLUGIN_ROOT}/templates/SETTINGS.md` — walk them with the user and add
real rules.

| Guard | What it does |
|---|---|
| Protected paths | Denies edits to migrations, generated files, infrastructure, the guardrail files |
| Test protection | Denies edits to test files while a bug fix is in progress |
| Credential blocking | Denies commands that read `.env`, key material, credential paths |
| Formatting | Formats each written file, so style never reaches review |
| Release authorization | Denies production deploys without a named human authorization |

Prove each hook by triggering it once — `templates/hooks/README.md` has a
one-line stdin test for each. An untested hook is a comment.

### 5. Scaffold the evals

Copy `${CLAUDE_PLUGIN_ROOT}/templates/evals/` into the repo. The three example
cases use the standard `claude plugin eval` format: a case directory holding
`prompt.md` and one file per grader. Replace their `TODO:` paths with real ones,
seed 5–10 cases from real past work, and grow toward 20–50.

Wire `claude plugin eval .` into CI so any PR touching `CLAUDE.md`, skills,
hooks, settings, or `REVIEW.md` runs it and blocks on a regression. Add
`evals/results/` to `.gitignore`. See the `sdlc-test-verify` skill's evals
reference for the grader types and what they can assert.

### 6. Report the open TODOs

Grep the installed files for `TODO:` and list every one to the user, grouped by
file, with the decision each needs:

```bash
grep -rn "TODO:" CLAUDE.md REVIEW.md .claude/ evals/ .sdlc/TEMPLATES/
```

Ask for the answers you can get now; leave the rest visible for later. Do not
silently invent values for organizational decisions — who authorizes releases,
which compliance regimes apply, what the source of truth is.

### 7. Commit

One commit: `chore(sdlc): install lifecycle guardrails`. From here, changes to
any of these files are configuration changes and run the eval suite.

## Settings, in short

Deny reading credential paths. Allow the specific commands the workflow needs
rather than a blanket shell allowance — anything unlisted still works, it just
asks first. Keep the sandbox on with `allowUnsandboxedCommands: false`, and add
your internal registries to `sandbox.network.allowedDomains`. Restrict which
plugins and skills a session may load so nobody pulls in unreviewed tooling.
`templates/SETTINGS.md` lists each decision and where it goes.

<!-- TODO: Decide whether these settings are managed centrally by the
     organization or held per-repo, and record which. -->
