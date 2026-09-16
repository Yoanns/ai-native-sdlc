# AI-Native SDLC

A Claude Code plugin that runs software work through a looped, artifact-driven
lifecycle. Each stage reads the artifact the previous stage committed and
commits its own; together they are the audit trail. Humans sit at the gates
between stages, not inside every step.

```
request ──▶ 1 SPEC ──▶ 2 BUILD ──▶ 3 TEST ──▶ 4 DEPLOY ──▶ 5 MAINTAIN ──┐
             spec.md    plan.md     green      review.md     finding     │
             ▲                                                            │
             └────────────────────── new spec ◀───────────────────────────┘
```

Adapted from Anthropic's *AI-native SDLC playbook*. Every claim about file
formats here was checked against the Claude Code documentation — see
[SOURCES.md](SOURCES.md) for what was read and what each source contributed.

---

## Install

```
/plugin marketplace add yoanns/ai-native-sdlc
/plugin install ai-native-sdlc@ai-native-sdlc
```

The repository is its own marketplace, so those two lines are the whole
installation. To update later:

```
/plugin marketplace update ai-native-sdlc
```

<details>
<summary>Install from a local clone instead</summary>

```bash
git clone https://github.com/yoanns/ai-native-sdlc.git
```

```
/plugin marketplace add ./ai-native-sdlc
/plugin install ai-native-sdlc@ai-native-sdlc
```
</details>

**Requirements:** Claude Code (or Cowork). No MCP servers, no API keys, no
runtime dependencies. The optional eval suite uses `claude plugin eval`, which
ships with the CLI.

---

## Quick start

**Once per repository**, before the first work item:

> set up the SDLC guardrails

This reads the repo, writes `CLAUDE.md`, `REVIEW.md`, the hooks and settings,
and the eval scaffold, then lists every decision still open. See
[docs/getting-started.md](docs/getting-started.md) for what it asks and why.

**Then, per piece of work:**

> here's what we need: customers want their invoices as a single PDF

Claude writes the spec, stops for your approval, and only then plans. At any
point, *"what stage is this in?"* tells you where the work item stands.

---

## The five stages

| # | Stage | Skill | Produces | Gate owner |
|---|---|---|---|---|
| 1 | Spec | `sdlc-design-spec` | `spec.md` | Requester (+ tech lead if risky) |
| 2 | Build | `sdlc-build-plan` | `plan.md`, then code | Engineer |
| 3 | Test | `sdlc-test-verify` | Green tests, build, lint, evals | Engineer |
| 4 | Deploy | `sdlc-deploy-review` | `review.md`, merged PR, release | Code owner; release manager |
| 5 | Maintain | `sdlc-maintain-monitor` | A finding, promoted to a new spec | On-call engineer |

`sdlc-orchestrator` sits above all five: it works out which stage a work item
is in from the artifacts on disk, routes to the right skill, and refuses to
skip a gate. `sdlc-setup-guardrails` runs once per repository.

Artifacts live together per work item:

```
.sdlc/<work-item-slug>/
├── spec.md      problem, requirements, design, flagged concerns
├── plan.md      files that change, order of work, tests that prove it
└── review.md    findings from the review passes, ranked by severity
```

[docs/components.md](docs/components.md) documents every skill, agent and
template file in detail.

---

## What it actually changes

Without the plugin, a request becomes code immediately and review happens
after the fact. With it:

- **Design review moves before generation.** Plan mode is read-only, so the
  plan is argued over while changing it is still cheap.
- **Review runs as defined passes, in parallel.** Three subagents — bugs and
  logic, security, spec conformance — rather than one freeform read.
- **The spec becomes enforceable.** A review pass checks the diff against it:
  every requirement met, nothing built that nobody asked for.
- **Policy that must always hold is deterministic.** Skills advise; hooks
  block. Both ship here.
- **Configuration is tested.** Changing `CLAUDE.md`, a skill or a hook runs an
  eval suite, because it changes behaviour with no diff to review.

---

## Everyday phrases

| Say | What runs |
|---|---|
| "Spec this out" / "here's what we need" | Stage 1 |
| "What stage is this in?" / "what's next?" | Orchestrator |
| "Plan this before you code" / "let's build it" | Stage 2 |
| "Verify before I look" / "the tests are failing" | Stage 3 |
| "Review this PR" / "ready to merge" | Stage 4 |
| "Triage this alert" / "why did this metric move?" | Stage 5 |
| "Set up the SDLC" / "write a CLAUDE.md" | Guardrail setup |

---

## The rules that do not bend

- **Nothing is built without an approved spec.** Nothing is coded without an
  accepted plan.
- **Claude never approves its own work.** It writes, it reviews other changes,
  a human approves.
- **Production requires a named human authorization**, enforced by a hook.
- **Tests are never weakened to go green.** For bugs: failing test first,
  committed on its own, then the fix.
- **Configuration is code.** Changing `CLAUDE.md`, a skill, or a hook runs the
  eval suite.
- **Findings loop back as specs**, never as silent patches.

---

## What ships

| Component | Count | Purpose |
|---|---|---|
| Skills | 7 | Orchestrator, five stages, one-time guardrail setup |
| Agents | 3 | Parallel review passes: bugs/logic, security, spec conformance |
| Templates | 13 files + 3 eval cases | `spec.md`, `plan.md`, `CLAUDE.md`, `REVIEW.md`, hook config + 4 scripts, settings, metric watcher |
| Evals | 3 cases | `claude plugin eval` suite for the plugin itself |
| MCP servers | 0 | None required |

```
ai-native-sdlc/
├── .claude-plugin/
│   ├── plugin.json           plugin manifest
│   └── marketplace.json      lets the repo serve as its own marketplace
├── skills/                   7 skills, one directory each
├── agents/                   3 review-pass subagents
├── templates/                what sdlc-setup-guardrails installs into a repo
├── evals/                    eval suite for this plugin
├── docs/                     component reference and setup walkthrough
├── scripts/                  validate.py, publish helpers
├── CUSTOMIZE.md              every TODO marker and what it decides
└── SOURCES.md                everything read to build this
```

---

## Customization

The plugin is deliberately generic: it assumes no language, CI system or
deployment target. Every organization-specific decision is marked `TODO:` in
the file that needs it.

```bash
grep -rn "TODO:" .
```

The exception is `templates/settings.json`, where an invalid permission rule
is skipped with a warning rather than failing — a placeholder there would
silently do nothing, so those decisions live in `templates/SETTINGS.md`
instead. [CUSTOMIZE.md](CUSTOMIZE.md) lists them all, grouped by when they
matter.

To adapt the plugin itself, ask Claude to *"customize the ai-native-sdlc
plugin"*.

---

## Validate and test

```bash
claude plugin validate .claude-plugin/plugin.json   # manifest
python3 scripts/validate.py                         # every file against its schema
claude plugin eval .                                # behaviour, with and without the plugin
```

`scripts/validate.py` checks skill and agent frontmatter keys against the
documented sets, the hooks file shape and event names, permission-rule syntax,
eval case and grader schemas, shell syntax, and that every
`${CLAUDE_PLUGIN_ROOT}` reference resolves. CI runs it on every push.

---

## A note on scope

The upstream playbook opens with an intake stage — an `intent.md` proto-spec
gated by a product owner deciding whether the work is worth doing. That gate
is deliberately absent here: in the context this was built for, a request that
arrives is a request that gets built. The parts of intent worth keeping —
problem, outcome, constraints, open questions — are the opening sections of
`spec.md`. [CUSTOMIZE.md](CUSTOMIZE.md) explains how to restore the stage if
your organization needs it.

---

## Licence

MIT — see [LICENSE](LICENSE).
