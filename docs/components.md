# Components

Every file the plugin ships, what it does, and when it fires.

## Skills

Skills load on demand: Claude reads the description of each, and pulls in the
body when the work matches. All seven can also be invoked by name.

### `sdlc-orchestrator`

The router. Works out which stage a work item is in by inspecting which
artifacts exist and whether they carry an approval, then hands off to the
stage skill. Refuses to skip a gate, and never starts the next stage in the
same turn as the request for approval.

Fires on: *"run the SDLC"*, *"what stage is this in"*, *"what's next"*,
*"start a new feature"*, or any mention of a spec, plan or review artifact
without naming a stage.

References:

- `references/stage-map.md` — per stage: inputs, outputs, who does what, the gate, the handoff trigger.
- `references/loop.md` — how findings re-enter, which findings go to configuration rather than code, and how to pick a source of truth per artifact.

### `sdlc-design-spec` — Stage 1

Interviews the requester, reads the standing constraints (`CLAUDE.md`, any
standards skills, neighbouring code), and writes `.sdlc/<slug>/spec.md`. Flags
concerns rather than resolving them: anything touching security, privacy, data
classification, licensing, pricing, accessibility, regulation or an
irreversible migration gets a row and a named owner.

Refuses to write code or name files to change — that is Stage 2's job.

Fires on: *"write a spec"*, *"spec this out"*, *"here's what we need to
build"*, or a ticket handed over with no spec.

### `sdlc-build-plan` — Stage 2

Refuses to start without an approved spec. Enters plan mode (read-only),
reads the spec and the code it touches, and writes `.sdlc/<slug>/plan.md`
naming the files that change, the order of the work, and the tests that prove
each requirement. Invites the engineer to attack the plan, then implements
only after acceptance — keeping `plan.md` in sync when reality forces a change
of course.

Also covers parallel work (one worktree and one session per work item) and
delegating scoped jobs to subagents.

Fires on: *"let's build this"*, *"write the implementation plan"*, *"plan this
out before coding"*.

### `sdlc-test-verify` — Stage 3

Five rules: always have a feedback loop; fix bugs test-first; let hooks protect
the tests; give visual work visual proof; run the evals when configuration
changes. Ends with a definition of done that must be satisfied before
reporting done, and a list of the anti-patterns that fake it.

References `references/evals.md` — the eval case format, the grader types and
what each can assert, when to run the suite and how to grow it.

Fires on: *"write tests for this"*, *"verify before I look"*, *"the tests are
failing"*, or a change to `CLAUDE.md`, a skill or a hook.

### `sdlc-deploy-review` — Stage 4

Checks the branch carries its spec and plan, launches the review passes in
parallel, merges their findings into `.sdlc/<slug>/review.md` ranked by
severity, and posts them to the PR. Addresses findings on Claude's own PRs.
Enforces the rule that does not bend: Claude never approves its own work and
never authorizes production.

Also covers running Claude non-interactively in CI for judgement steps, with
sandboxed execution, scoped credentials and deploy actions exposed as typed
tools rather than free shell.

Fires on: *"review this PR"*, *"ready to merge"*, *"ship it"*, *"deploy this"*.

### `sdlc-maintain-monitor` — Stage 5

Diagnoses within the tier the signal earns — read-only at 2σ, act-permitted at
3σ — and writes findings up as a new spec seeded with evidence. Covers
recurring scans, incident channels, and post-mortems that must produce at
least one of: an eval case, a `CLAUDE.md` entry, a hook, or a review pass.

References `references/control-bands.md` — choosing metrics, computing
baselines, the guards a watcher needs (cooldown, deduplication, kill switch,
invocation budget), and what a pre-approved runbook may contain.

Fires on: *"triage this alert"*, *"why did this metric move"*, *"write the
post-mortem"*, *"set up monitoring"*.

### `sdlc-setup-guardrails` — once per repository

Reads the repo and installs the standing configuration: `CLAUDE.md` built from
what it actually finds (commands verified to run, conventions visible in the
code, mistakes harvested from repeated review comments), `REVIEW.md`, the hook
scripts and configuration, settings, and the eval scaffold. Ends by listing
every open `TODO:` with the decision it needs.

Fires on: *"set up the SDLC"*, *"install the guardrails"*, *"write a CLAUDE.md
for this repo"*.

## Agents

The review passes. Independent, so Stage 4 runs them simultaneously. Each is
read-only plus Bash, and reports findings ranked by severity with file, line,
the input that triggers the problem, and the smallest correct fix.

| Agent | Asks | Blocker means |
|---|---|---|
| `sdlc-review-bugs` | Does it work? What input breaks it? | Data loss, a crash on realistic input, a broken public contract |
| `sdlc-review-security` | What can an attacker do that they should not? | Unauthenticated access, authorization bypass, injection, secret exposure, PII leak |
| `sdlc-review-spec` | Does the diff do what the spec asked, and nothing else? | A requirement unmet, a flagged concern resolved on paper but not in code |

`sdlc-review-spec` also reports scope creep and plan drift — changes nobody
asked for, and files changed that the plan never named. Both are how risk
enters a PR unreviewed.

Add a pass by writing another agent file and listing it in `REVIEW.md`.
Compliance, data classification, accessibility, performance budget and
licensing are the usual additions.

## Templates

What `sdlc-setup-guardrails` installs into a repository.

| File | Becomes | Purpose |
|---|---|---|
| `spec.md` | `.sdlc/<slug>/spec.md` | Problem, outcome, requirements, design, flagged concerns, open questions, success criteria |
| `plan.md` | `.sdlc/<slug>/plan.md` | Files, order, tests, interfaces, risks and rollback, deviations |
| `CLAUDE.md` | `CLAUDE.md` | Commands, conventions, architecture, protected paths, common mistakes — under a page |
| `REVIEW.md` | `REVIEW.md` | Review passes, severity scale, what blocks a merge, how findings feed back into configuration |
| `hooks.json` | `.claude/settings.json` (merged) or `.claude/hooks/hooks.json` | The hook configuration, wrapped in its top-level `hooks` key |
| `hooks/scripts/protect-paths.sh` | `.claude/hooks/scripts/` | Denies edits to migrations, generated code, infrastructure, the guardrail files |
| `hooks/scripts/block-credentials.sh` | `.claude/hooks/scripts/` | Denies commands that read credential material |
| `hooks/scripts/require-release-auth.sh` | `.claude/hooks/scripts/` | Denies production deploys without a named human authorization |
| `hooks/scripts/format-file.sh` | `.claude/hooks/scripts/` | Formats each written file, so style never reaches review |
| `hooks/README.md` | — | What each hook does, the stdin/stdout contract, and a one-line test for each |
| `settings.json` | `.claude/settings.json` | Permissions, sandbox, network allowlist |
| `SETTINGS.md` | — | The settings decisions that cannot be placeholders |
| `monitor/watch-metrics.sh` | wherever the scheduler runs it | Deterministic metric watcher: decides whether to wake Claude, never what Claude concludes |
| `evals/` | `evals/` | Three example cases in `claude plugin eval` format |

### Why two prompt hooks and four scripts

Deterministic checks — is this path protected, does this command read a
secret, is this a production deploy — are scripts, because they must give the
same answer every time. Judgement calls — is this edit weakening a test during
a bug fix, was the definition of done actually met — are prompt hooks, because
no pattern expresses them. Both kinds block; only the scripts are predictable
enough to trust blindly.

## Evals

Three cases for the plugin itself, in `evals/`:

| Case | Asserts |
|---|---|
| `spec-request` | A plain feature request reaches the spec stage and stops for approval, rather than producing code |
| `review-before-merge` | A pre-merge request runs the defined passes and ranks findings |
| `no-self-approval` | Claude declines to approve its own PR or authorize a deploy, however it is asked |

Each runs three times with the plugin and three times without, so the delta
shows what the plugin contributes. A near-zero delta with a failing
`tool_used: Skill` grader means a skill description is not triggering on
natural phrasing — fix the description, not the grader.

```bash
claude plugin eval .
claude plugin eval . --case no-self-approval --runs 1 --ablation none
```
