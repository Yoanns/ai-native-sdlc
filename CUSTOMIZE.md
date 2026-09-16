# Customization

This plugin ships generic. Every organization-specific decision is marked
`TODO:` in the file that needs it. Find them all at any time with:

```bash
grep -rn "TODO:" .
```

Nothing here is guessed on your behalf, because a wrong guess about who
authorizes a release or which compliance regime applies is worse than a blank.

## Decisions, in the order they matter

### 1. Before the first work item — repository facts

*Where:* `templates/CLAUDE.md` (29 markers)

The build, test, lint, format, typecheck and run commands; the conventions
this repo follows that a default would get wrong; the module map and its
import boundaries; the protected paths; the mistakes that recur in review.

The `sdlc-setup-guardrails` skill fills most of this by reading the repo — it
verifies each command actually runs before writing it down. Review what it
produces; keep the file under one page.

### 2. Governance — who decides what

*Where:* `skills/sdlc-orchestrator/SKILL.md`, `templates/REVIEW.md`,
`skills/sdlc-deploy-review/SKILL.md`

| Decision | Default shipped |
|---|---|
| Gate owner per stage | Generic roles: requester, engineer, code owner, release manager, on-call |
| Review passes required | Bugs/logic, security, spec conformance |
| Severity threshold that blocks a merge | Blocker and Major |
| Who may authorize a production release | Unset — the hook blocks until you decide |
| Branch protection rules | Unset |

Add the passes your domain needs — compliance, data classification,
accessibility, performance budget, licensing. Each new pass needs a subagent
in `agents/` and a row in `REVIEW.md`.

### 3. Source of truth per artifact

*Where:* `skills/sdlc-orchestrator/references/loop.md`

For `spec.md`, `plan.md` and `review.md`, pick exactly one: the repository, an
external system (tracker, doc tool), or linked with mirroring. Ambiguity here
is what produces two specs that disagree.

### 4. Enforcement — hooks and settings

*Where:* `templates/hooks.json`, `templates/hooks/scripts/*.sh`,
`templates/hooks/README.md`, `templates/settings.json`, `templates/SETTINGS.md`

`settings.json` carries no `TODO:` markers on purpose: an invalid permission
rule is skipped with a warning rather than failing loudly, so a placeholder
left inside it would quietly do nothing. Its open decisions are written out in
`templates/SETTINGS.md` instead.

| Decision | Notes |
|---|---|
| Protected paths | Migrations, generated code, infrastructure, vendored code, `.claude/` itself |
| Test-file pattern | So the bug-fix protection knows what a test is |
| Formatter command | Runs after every write |
| Credential locations | Beyond the common defaults already listed |
| Deploy commands | The commands that actually reach production in your setup |
| Release authorization source | An env var is the placeholder; a signed release ticket or CI approval step is better |
| Allowed commands | Allow what the workflow needs; avoid a blanket shell allowance |
| Network allowlist | Package registries and internal services the sandbox may reach |
| Approved MCP servers and skills | So a session cannot pull in unreviewed tooling |

Trigger every hook once before trusting it. An untested hook is a comment.

### 5. Evals

*Where:* `templates/evals/` — three example cases in the standard
`claude plugin eval` format (`<case>/prompt.md` plus `<case>/graders/*.md`)

Replace the `TODO:` paths in the prompts and graders with real ones from your
repo. The runner is the CLI — `claude plugin eval .` — so there is nothing to
implement. Seed 5–10 cases from real past work and grow toward 20–50. Decide
the merge-blocking threshold; the usual choice is "no regression against
main's last run", and add `evals/results/` to `.gitignore`.

### 6. Monitoring

*Where:* `templates/monitor/watch-metrics.sh`,
`skills/sdlc-maintain-monitor/references/control-bands.md`

Which metrics, read from where, over what window. The response tiers (1σ log,
2σ diagnose read-only, 3σ may act) ship as defaults. Start with zero
pre-approved runbooks and add only what has been rehearsed — including the
rollback.

## Adapting the plugin itself

Ask Claude to "customize the ai-native-sdlc plugin". It will walk the markers
with you and repackage the plugin with your answers baked in. Renaming skills
or stages is fine — update `README.md` and the orchestrator's routing table so
they still agree.

## What was deliberately left out

The upstream playbook opens with an intake stage: an `intent.md` capturing a
proto-spec, gated by a product owner deciding whether the work is worth doing.
That gate is removed here — in this context a request that arrives is a request
that gets built. The parts of intent worth keeping (problem, outcome,
constraints, open questions) are the opening sections of `spec.md`.

To restore it: add an `sdlc-plan-intent` skill producing `.sdlc/<slug>/intent.md`,
insert it ahead of Spec in the orchestrator's routing table and stage map, and
point Stage 5 findings at it instead of at the spec.
