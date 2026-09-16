# Sources

Everything read to build this plugin, what each source contributed, and what
was deliberately changed. Retrieved September 2026.

## The design source

### The AI-native SDLC playbook — Anthropic

<https://claude.com/blog/the-ai-native-sdlc-playbook>

The lifecycle itself comes from here: stages that each commit an artifact the
next stage reads, humans at the gates rather than in the loop, and the loop
closing from monitoring back to intake.

| Taken from the playbook | Where it lives here |
|---|---|
| Stage structure and the artifact chain | `skills/sdlc-orchestrator/` |
| `spec.md` — requirements and design with flagged concerns | `skills/sdlc-design-spec/`, `templates/spec.md` |
| `plan.md` — "names the files that change, the order of the work, and the tests that prove it" | `skills/sdlc-build-plan/`, `templates/plan.md` |
| Plan mode as the design-review gate before code generation | `skills/sdlc-build-plan/` |
| `CLAUDE.md` structure — commands, conventions, architecture, common mistakes; "keep it under a page" | `templates/CLAUDE.md` |
| Skills advisory, hooks deterministic | `skills/sdlc-setup-guardrails/`, `templates/hooks/` |
| Feedback loops: "always give Claude a way to verify its own work" | `skills/sdlc-test-verify/` |
| Test-first bug fixing; a test that existed before the fix is the proof | `skills/sdlc-test-verify/`, the test-protection hook |
| Continuous evals gating configuration changes; incidents become permanent cases | `skills/sdlc-test-verify/references/evals.md`, `templates/evals/` |
| `REVIEW.md`, parallel review passes, severity thresholds | `templates/REVIEW.md`, `agents/*.md`, `skills/sdlc-deploy-review/` |
| Separation of duties — agent writes, agent reviews others, human approves | `skills/sdlc-deploy-review/`, `evals/no-self-approval/` |
| Autonomy tiered by environment: development free, staging controlled, production gated | `skills/sdlc-orchestrator/`, `templates/hooks/scripts/require-release-auth.sh` |
| Monitoring control bands: 1σ log, 2σ diagnose read-only, 3σ may act | `skills/sdlc-maintain-monitor/references/control-bands.md`, `templates/monitor/watch-metrics.sh` |
| Findings written up with evidence and re-entering the pipeline | `skills/sdlc-maintain-monitor/`, `skills/sdlc-orchestrator/references/loop.md` |
| Naming one source of truth per artifact for legacy integration | `skills/sdlc-orchestrator/references/loop.md` |

**What was changed.** The playbook's Stage 1 is intake: an `intent.md`
proto-spec gated by a product owner deciding whether the work is worth doing.
That stage is absent here because in the context this was built for, a request
that arrives is a request that gets built. Its substance — problem, outcome,
constraints, open questions — became the opening sections of `spec.md`.
`CUSTOMIZE.md` records how to restore it.

## The format sources

These are the Claude Code documentation pages the file formats were verified
against. The first build of this plugin was written from a plugin-authoring
guide and got four things wrong; each page below is what corrected one.

| Page | What it settled |
|---|---|
| [Skills](https://code.claude.com/docs/en/skills) | The allowed `SKILL.md` frontmatter keys, that unknown keys are a hard error, that `metadata` is supported, and the 1,536-character description limit |
| [Subagents](https://code.claude.com/docs/en/sub-agents) | Agent frontmatter fields, that `tools` accepts a comma-separated string, that `color` and `model: inherit` are real — and that a multi-line description containing `<example>` blocks must be a YAML literal block scalar (`description: \|`) or the frontmatter does not parse |
| [Hooks](https://code.claude.com/docs/en/hooks) | The hook event names, matcher semantics, the stdin payload field names (`tool_name`, `tool_input.file_path`, `tool_input.command`), and the decision contract: `hookSpecificOutput.permissionDecision` of `allow` or `deny` with `permissionDecisionReason` — not the `{"decision": "block"}` shape assumed at first |
| [Plugins reference](https://code.claude.com/docs/en/plugins-reference) | The `plugin.json` field list and types, the plugin directory layout, and that a plugin's hooks file must wrap its events in a top-level `"hooks"` key |
| [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) | The `marketplace.json` schema and that a single-plugin repository can serve as its own marketplace with `"source": "./"` |
| [Settings](https://code.claude.com/docs/en/settings) | Settings precedence and scope, and that an invalid entry — a malformed permission rule, an unknown hook event — is skipped with a warning rather than failing the file. This is why `templates/settings.json` carries no placeholders and its open decisions live in `templates/SETTINGS.md` |
| [Settings reference](https://code.claude.com/docs/en/settings-reference) | The real key names, including `sandbox.network.allowedDomains` — not the `allowlist` spelling assumed at first |
| [Plugin evals](https://code.claude.com/docs/en/plugin-evals) | The eval case format — a case directory holding `prompt.md` and one file per grader — the grader types and their options, and that there is no exit-code grader, so "the tests pass" is expressed as an `llm` grader over the trace |

The four corrections, in full: invalid YAML in all three agent files; hook
scripts emitting a decision shape the runtime does not read; an invented
sandbox key plus placeholder permission rules that would have been silently
skipped; and a hand-rolled eval format with an unimplemented runner, replaced
by the documented one.

## Tooling used

- **`cowork-plugin` skill** (bundled with Claude Cowork) — the plugin
  scaffolding conventions and the `.plugin` packaging step.
- **`claude plugin validate`** — manifest validation, run against this repo.
- **`claude plugin eval`** — the eval runner the suite in `evals/` targets.

## How to verify any of this

Every format claim above is checkable against the page it cites. If a
documented format changes, `scripts/validate.py` is where the expected key
sets live — update it there first, then the files it checks.
