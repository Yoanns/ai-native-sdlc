# Stage map

Full reference for the five stages. Each row is a contract: nothing enters a
stage without its input artifact approved, and nothing leaves without its
output artifact committed.

## Stage 1 — Spec

| | |
|---|---|
| **Input** | A request: a chat message, a ticket, an incident finding, a review finding |
| **Skill** | `sdlc-design-spec` |
| **Output** | `.sdlc/<slug>/spec.md` |
| **Claude's job** | Interview the requester, then write the spec constrained by the organization's standards skills (brand, security, compliance, UX). Flag every concern rather than resolving it silently. |
| **Human's job** | Answer the interview questions, resolve flagged concerns with their owners, approve. |
| **Gate** | Flagged concerns closed before engineering starts. Tech lead consulted for higher-risk items. |
| **Handoff trigger** | Committed `spec.md` with `status: approved`. |

## Stage 2 — Build

| | |
|---|---|
| **Input** | Approved `spec.md` |
| **Skill** | `sdlc-build-plan` |
| **Output** | `.sdlc/<slug>/plan.md`, then code and tests |
| **Claude's job** | In plan mode (read-only), produce a plan naming the files that change, the order of the work, and the tests that prove it. Implement only after the plan is accepted. |
| **Human's job** | Interrogate the plan. Iterate until it is right. Accept, then review the resulting diff. |
| **Gate** | Design review happens *before* code generation. Plan mode enforces it. |
| **Handoff trigger** | Code written against an accepted `plan.md`; plan kept in sync with what was actually built. |

## Stage 3 — Test

| | |
|---|---|
| **Input** | Code + `plan.md` |
| **Skill** | `sdlc-test-verify` |
| **Output** | Passing tests, build, lint; green eval run when configuration changed |
| **Claude's job** | Verify its own work before asking for human attention. For bugs: failing test first, then the fix, without touching the test. |
| **Human's job** | Confirm the failing test fails for the right reason. Review coverage of the risky paths. |
| **Gate** | Tests pass, build succeeds, linter clean, evals green — before reporting done. |
| **Handoff trigger** | First-pass CI success. |

## Stage 4 — Deploy

| | |
|---|---|
| **Input** | A PR containing the diff, with `spec.md` and `plan.md` in the branch |
| **Skill** | `sdlc-deploy-review` |
| **Output** | `.sdlc/<slug>/review.md`, PR comments, a merged PR, a release |
| **Claude's job** | Run every review pass in `REVIEW.md` in parallel, rank findings by severity, address comments on its own PRs. Never approve its own work. |
| **Human's job** | Code owner approves the PR, informed by the findings. Release manager authorizes production. |
| **Gate** | Separation of duties enforced by branch protection; production deploy enforced by hook requiring named authorization. |
| **Handoff trigger** | Merged PR triggers the pipeline; authorized release triggers deployment. |

## Stage 5 — Maintain

| | |
|---|---|
| **Input** | Production signals: metrics, alerts, scheduled scans, incidents, support threads |
| **Skill** | `sdlc-maintain-monitor` |
| **Output** | A finding with evidence, promoted to a new `.sdlc/<slug>/spec.md` |
| **Claude's job** | Diagnose within the tier the signal earns. Write findings up with evidence, proposed outcome, affected systems, and open questions. |
| **Human's job** | On-call triages: real or noise. Dismissals tune the thresholds. |
| **Gate** | A finding becomes work only once a human accepts it. |
| **Handoff trigger** | Accepted finding re-enters at Stage 1. |

## Parallelism

Stages are sequential *per work item*, not per engineer. One engineer can hold
several work items at different stages at once — separate git worktrees, one
Claude session each. Keep one work item per session so its artifact chain and
its context stay together.
