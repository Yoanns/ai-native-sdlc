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
| [Install and manage plugins](https://code.claude.com/docs/en/discover-plugins) | The one-step install, `/plugin install <name> --marketplace <owner>/<repo>` (Claude Code 2.1.275+), and that removing a marketplace also uninstalls its plugins |
| `claude plugin validate` (CLI) | That a third-party plugin name may not start with `claude-` — which is why this plugin kept its name when a rename was considered |
| [Plugin evals](https://code.claude.com/docs/en/plugin-evals) | The eval case format — a case directory holding `prompt.md` and one file per grader — the grader types and their options, and that there is no exit-code grader, so "the tests pass" is expressed as an `llm` grader over the trace |

The four corrections, in full: invalid YAML in all three agent files; hook
scripts emitting a decision shape the runtime does not read; an invented
sandbox key plus placeholder permission rules that would have been silently
skipped; and a hand-rolled eval format with an unimplemented runner, replaced
by the documented one.

## Sources for the agent-agnostic mirror

[agent-native-sdlc](https://github.com/yoanns/agent-native-sdlc) is generated
from this repository for agents other than Claude Code. Its adapters were
checked against these pages, retrieved October 2026.

| Page | What it settled |
|---|---|
| [AGENTS.md](https://agents.md) | The file is `AGENTS.md` at the repository root, plain markdown with no schema, nearest file wins when nested; the list of agents that read it; and the two that need a setting — Aider (`read: AGENTS.md` in `.aider.conf.yml`) and Gemini CLI |
| [Claude Code — memory](https://code.claude.com/docs/en/memory) | Claude Code reads `AGENTS.md` natively (v2.1.277+), but only when no `CLAUDE.md` is present; a `CLAUDE.md` can import it with `@AGENTS.md`. The installer warns about this |
| [Cursor — rules](https://cursor.com/docs/context/rules) | `.cursor/rules/*.mdc` with `description`, `globs` and `alwaysApply`; a rule with only a description is applied when the agent judges it relevant — the closest equivalent to a skill — and plain `.md` files there are ignored |
| [Cursor — hooks](https://cursor.com/docs/agent/hooks) | `.cursor/hooks.json` (`version: 1`), the `preToolUse` and `afterFileEdit` events, matcher values `Shell`, `Write`, `Delete`, the input fields `tool_name` and `tool_input.command`, the output `{"permission", "user_message", "agent_message"}`, that exit 2 denies, and that invalid JSON from a permission hook blocks the action |
| [VS Code — custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions) | `.github/instructions/*.instructions.md` with `name`, `description` and `applyTo`; a description alone makes the file load on demand; Copilot reads `AGENTS.md` |
| [VS Code — hooks](https://code.visualstudio.com/docs/copilot/customization/hooks) and [hooks reference](https://code.visualstudio.com/docs/agents/reference/hooks-reference) | Workspace hooks in `.github/hooks/*.json`; the input fields `tool_name` and `tool_input`; `permissionDecision` of `allow`, `deny` or `ask`; exit 2 blocks with stderr given to the model; and that tool names differ between harnesses |
| [GitHub Copilot — hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference) | The format the Copilot CLI and cloud agent read: `version: 1`, camelCase `preToolUse`, entries with `bash` and `timeoutSec`, input `toolName` and `toolArgs`, output `permissionDecision` with `permissionDecisionReason`, exit 2 as a deny, and that `preToolUse` fails closed |
| [Gemini CLI — configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md) | `.gemini/settings.json` at the project root, and that `context.fileName` takes a string or an array — so `AGENTS.md` can be added without dropping `GEMINI.md` |

**One contract all of them share.** Every agent above that has a pre-tool hook
treats exit code 2 as a deny. The guard scripts rely on that for Copilot, and
emit each agent's richer JSON where its documentation promises the message
reaches the agent.

**What the documentation does not say**, so the mirror is written to cope:

- Cursor documents no `tool_input` example for `Write`, so the key carrying the
  file path is unknown. The path guard accepts `file_path`, `path`, `filePath`,
  `target_file` and similar.
- Copilot's tool names are not documented and vary between VS Code, the CLI
  and the cloud agent, and its hook config cannot filter by tool. The path
  guard therefore recognizes write tools by name (`edit`, `write`, `create`,
  `replace`, `delete`, `patch`, …) and lets everything else through.
- Neither says whether the first live call matches these assumptions, which
  is why the setup guide asks for one deliberate test through the agent itself.

## Tooling used

- **`cowork-plugin` skill** (bundled with Claude Cowork) — the plugin
  scaffolding conventions and the `.plugin` packaging step.
- **`claude plugin validate`** — manifest validation, run against this repo.
- **`claude plugin eval`** — the eval runner the suite in `evals/` targets.
- **`scripts/build_mirror.py`** and **`scripts/test_mirror.py`** — generate the
  mirror and test the guards, the spec gate and the installer.

## How to verify any of this

Every format claim above is checkable against the page it cites. If a
documented format changes, `scripts/validate.py` is where the expected key
sets live for the plugin, and `templates/hooks/scripts/hookio.py` and
`mirror/overlay/` for the other agents — update those first, then the files
they produce.
