# Setup — guardrails

Install the standing configuration the five stages depend on. Do this once per
repository, before the first work item. Everything installed here is
version-controlled and reviewed like code, because it steers every session
that follows.

If you are an agent asked to "set up the SDLC" in a repository, this file is
your procedure.

## What gets installed

`install.py` from the agent-native-sdlc repository writes the files. Run it
from a checkout of that repository:

```bash
python3 install.py /path/to/your/repo            # detects which agents you use
python3 install.py /path/to/your/repo --agents cursor,copilot
python3 install.py /path/to/your/repo --dry-run  # show what would change
```

| File | Purpose | Enforcement |
|---|---|---|
| `AGENTS.md` | Repo knowledge plus the lifecycle, read at every session start | Advisory |
| `REVIEW.md` | Review passes and severity thresholds | Advisory, read by stage 4 |
| `.sdlc/playbook/` | The stage procedures this file belongs to | Advisory |
| `.sdlc/templates/` | `spec.md` and `plan.md` shapes | Advisory |
| `.sdlc/guards/` | Protected paths, credential blocking, release authorization, formatting | **Deterministic**, through your agent's hooks |
| `.sdlc/enforcement/` + `.github/workflows/sdlc-gate.yml` | The spec gate | **Deterministic**, in CI — binds every agent and every person |
| `.cursor/rules/`, `.cursor/hooks.json` | Cursor: stage rules that load on demand, guard hooks | — |
| `.github/instructions/`, `.github/hooks/sdlc.json` | Copilot: the same | — |

Rules and playbook files are advisory: they shape how code is written, and an
agent can reason around them. Hooks and the spec gate are deterministic. Back
every policy that must always hold with one of the two.

## Procedure

### 1. Inspect the repo first

Do not write a generic `AGENTS.md`. Read the repo and extract the real thing:

- Build, test, lint, and run commands — from `Makefile`, `package.json`,
  `pyproject.toml`, CI workflows. Verify each one actually runs.
- Directory layout and the boundaries between modules.
- Conventions visible in the code: naming, error handling, logging, imports,
  test structure.
- Protected paths: migrations, generated code, vendored code, infrastructure,
  secrets, licence headers.
- Git history for repeated review comments — those are the "common mistakes".

### 2. Fill in AGENTS.md

The installer writes `AGENTS.md` with two parts. The part between the
`sdlc:begin` and `sdlc:end` markers is the lifecycle; it is managed by the
installer and replaced on update — leave it alone. Everything above it is
yours to fill from what you found:

1. **Commands** — the exact invocations, verified to work.
2. **Conventions** — what this repo does differently from the default.
3. **Architecture** — the module map and the boundaries that matter.
4. **Common mistakes** — what goes wrong here, stated as a rule.

**Keep it under a page.** It is read in full at every session start, so every
line competes for attention with every other. Delete anything that is generic
good practice; keep only what is true of *this* repo.

If the repository already had an `AGENTS.md`, the installer added the
lifecycle block to it and left the rest untouched.

### 3. Write REVIEW.md

Define the review passes this repo requires and the severity threshold that
blocks a merge. The three default passes live in
`.sdlc/playbook/review-passes/`. Ask which compliance or domain passes apply —
do not assume.

### 4. Tailor the guards

Edit the lists at the top of each script in `.sdlc/guards/`:

| Script | Edit |
|---|---|
| `protect-paths.sh` | `PROTECTED` — the paths only a human may change |
| `block-credentials.sh` | `PATTERNS` — where credential material lives here |
| `require-release-auth.sh` | `DEPLOY_PATTERNS` — the commands that reach production |
| `format-file.sh` | the formatter per file type |

The same scripts serve every agent; each agent's hook configuration passes
`--format` so the decision comes back in the shape that agent reads.

Prove each guard by triggering it once. An untested hook is a comment:

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"db/migrations/001.sql"}}' \
  | bash .sdlc/guards/protect-paths.sh --format exit; echo "exit $?"   # expect 2
echo '{"tool_name":"Shell","tool_input":{"command":"cat .env"}}' \
  | bash .sdlc/guards/block-credentials.sh --format exit; echo "exit $?" # expect 2
```

Then make one deliberate attempt through the agent itself — ask it to edit a
protected file — and confirm it is refused. Hook payloads are not fully
documented for every agent and tool; the first live test is the real one.

### 5. Turn on the spec gate

This is the guarantee the rest depends on, because it does not rely on any
agent cooperating:

1. Commit `.github/workflows/sdlc-gate.yml`.
2. In the repository's branch protection, make the **spec-gate** check
   required for the default branch.
3. Add a `CODEOWNERS` entry for the protected paths, so changes to them need a
   named reviewer whichever tool made them.
4. The installer also placed a `pre-push` git hook, so a missing approval is
   caught before the push rather than in CI.

### 6. Report the open TODOs

```bash
grep -rn "TODO:" AGENTS.md REVIEW.md .sdlc/
```

List every one to the user, grouped by file, with the decision each needs. Ask
for the answers you can get now; leave the rest visible. Do not invent values
for organizational decisions — who authorizes releases, which compliance
regimes apply, what the source of truth is.

### 7. Commit

One commit: `chore(sdlc): install lifecycle guardrails`. From here, changes to
any of these files are configuration changes.

## Notes per agent

| Agent | What to know |
|---|---|
| Cursor | Stage rules in `.cursor/rules/` load when their description matches the work. Guards run through `.cursor/hooks.json` (`preToolUse`). |
| GitHub Copilot | Stage instructions in `.github/instructions/` load on demand. Guards run through `.github/hooks/sdlc.json` in VS Code, the Copilot CLI and the cloud agent. Copilot's hook config cannot filter by tool, so the path guard recognizes write tools by name — confirm with one live test. |
| Gemini CLI | Reads `AGENTS.md` only with `context.fileName` set in `.gemini/settings.json`; the installer merges it. No hooks are installed. |
| Aider | Reads `AGENTS.md` only with `read: AGENTS.md` in `.aider.conf.yml`; the installer adds it. No hooks are installed. |
| Codex, Jules, Zed, Windsurf, Devin, Amp, Junie and other agents that read `AGENTS.md` | Nothing extra to install. The rules and gates come from `AGENTS.md`; the spec gate in CI holds regardless. |
| Claude Code | Use [ai-native-sdlc](https://github.com/yoanns/ai-native-sdlc) instead — the same lifecycle with skills that load on demand, parallel review subagents and its own hooks. Claude Code reads `AGENTS.md` only when the repository has no `CLAUDE.md`. |

The guards are bash scripts. On Windows they need `bash` on the path, which
Git for Windows provides.

## What the other agents do not get

Being explicit, so nobody assumes coverage that is not there:

- **Two guards are judgement calls, not patterns** — blocking a test edit
  during a bug fix, and checking the definition of done before a session ends.
  They need a hook that can ask a model; outside Claude Code they are rules in
  the playbook, not enforcement.
- **No permission or sandbox settings are installed.** Each agent configures
  these its own way; set them in your agent's settings.
- **No eval runner is shipped.** See `.sdlc/playbook/reference/evals.md`.
