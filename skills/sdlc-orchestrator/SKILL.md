---
name: sdlc-orchestrator
description: >
  This skill should be used when the user wants to run work through the
  AI-native software lifecycle end to end, or asks "start a new feature",
  "run the SDLC", "what stage is this in", "what's next on this work item",
  "take this from request to PR", or references a spec, plan, or review
  artifact without naming a single stage. Routes to the correct stage skill,
  enforces the approval gate between stages, and never skips ahead.
metadata:
  version: "0.1.0"
---

# SDLC Orchestrator

Run work through five stages: **Spec -> Build -> Test -> Deploy -> Maintain**.
Each stage reads the artifact the previous stage committed and commits its own.
The artifact chain is the audit trail. A stage never starts until the previous
stage's gate has been approved by a human.

There is no separate intake or business-case stage: a request that arrives is a
request that gets built. The problem, outcome, and constraints are captured at
the top of the spec, not in a document of their own.

## Core rules

1. **Never skip a stage.** If an upstream artifact is missing, go back and produce it.
2. **Never approve on the user's behalf.** Gates are human decisions. Ask, wait, record.
3. **Every stage ends with a commit.** Uncommitted work has not passed a gate.
4. **One work item = one directory.** All artifacts for a work item live together.
5. **Findings loop back.** Maintenance and review findings re-enter as a new spec, never as a silent patch.

## Artifact layout

```
.sdlc/<work-item-slug>/
  spec.md        Stage 1 output - problem, requirements, design, flagged concerns
  plan.md        Stage 2 output - files, order of work, tests that prove it
  review.md      Stage 4 output - findings from the agentic review passes
```

Repo-level guardrails live at the repo root: `CLAUDE.md`, `REVIEW.md`,
`.claude/hooks/`, `evals/`. If they are missing, run the
**sdlc-setup-guardrails** skill before the first work item.

<!-- TODO: If the organization uses an external tracker or doc system as the
     source of truth for specs, replace the paths above with links to that
     system and name ONE source of truth per artifact. -->

## Routing procedure

1. **Identify the work item.** Ask for a short slug (kebab-case) if none is
   given. Check `.sdlc/` for existing directories before creating a new one.

2. **Determine current stage** by inspecting which artifacts exist and their
   approval status (see the approval marker below):

   | State found | Current stage | Skill to invoke |
   |---|---|---|
   | A request, ticket, or idea in chat | Spec | `sdlc-design-spec` |
   | `spec.md` approved | Build | `sdlc-build-plan` |
   | `plan.md` approved, code written | Test | `sdlc-test-verify` |
   | Tests and evals green | Deploy | `sdlc-deploy-review` |
   | Merged and released | Maintain | `sdlc-maintain-monitor` |
   | A metric alert or incident, no work item | Maintain -> Spec | `sdlc-maintain-monitor` |

3. **State the stage out loud** before doing anything: which stage, which
   artifact is being produced, and who owns the gate at the end of it.

4. **Invoke the stage skill.** Do not inline its work here.

5. **At the gate**, stop. Present what was produced, name the decision the
   human must make, and wait. Do not begin the next stage in the same turn as
   the request for approval.

## Approval markers

Record each gate decision in the artifact's front matter so the next stage can
read it:

```yaml
---
status: approved          # draft | in-review | approved | rejected
approved_by: <name>       # the human who owns this gate
approved_at: 2026-01-31
---
```

A merged PR or a closed review counts as an approval; record it the same way.

## Gate owners

| Stage | Gate | Owner |
|---|---|---|
| 1 Spec | Spec approved, flagged concerns resolved | Requester (+ tech lead for higher-risk items) |
| 2 Build | Implementation plan interrogated and accepted | Engineer |
| 3 Test | Tests, build, lint, and evals pass | Engineer |
| 4 Deploy | PR approved; production release authorized | Code owner; release manager |
| 5 Maintain | Finding is real and worth acting on | On-call engineer |

<!-- TODO: Replace the role names above with the actual roles or named people
     in your organization, and delete any role you do not staff. -->

## Where humans get asked

Ask the human — do not guess — whenever:

- The requested outcome or its success criteria are ambiguous.
- The spec touches security, privacy, licensing, pricing, or data classification.
- The plan would change a public interface, a schema, or a protected path.
- A test would need to be weakened or deleted to make code pass.
- A review finding is above the severity threshold in `REVIEW.md`.
- A maintenance signal would trigger an action in production.

Batch questions into one round where possible. Carry the answers into the
artifact so the same question is never asked twice.

## Autonomy tiers

Match the level of independence to the blast radius, not to the task's size:

| Environment | Autonomy |
|---|---|
| Local / development | Free — auto mode, parallel sessions |
| Staging / CI | Controlled — scoped credentials, sandboxed, non-interactive |
| Production | Gated — named human authorization required, enforced by hooks |

## Further reference

- `references/stage-map.md` — full stage table: inputs, outputs, gates, handoff triggers.
- `references/loop.md` — how findings re-enter the loop, and legacy-system integration.
