---
name: sdlc-deploy-review
description: >
  This skill should be used when a change is ready for review or release, or
  when the user says "review this PR", "run the review passes", "ready to
  merge", "ship it", "deploy this", or mentions release authorization. Runs
  the agentic review passes defined in REVIEW.md in parallel, ranks findings
  by severity, and enforces that a human — never Claude — approves and
  authorizes production.
metadata:
  version: "0.1.0"
---

# Stage 4 — Deploy

Review is multi-layer and runs before human attention, not instead of it.
Governance is enforced as the agent acts, not discovered afterwards.

## The one rule that cannot bend

**Claude writes; Claude reviews other people's changes; a human approves.**

Claude never approves its own work, never merges past branch protection, and
never authorizes a production release. Separation of duties is enforced by
branch protection and hooks, not by good intentions.

## Procedure

### 1. Check the branch carries its artifacts

The PR branch must contain the current `spec.md` and `plan.md`. Without them
the review passes have nothing to judge conformance against. If they are
missing or stale, fix that first.

### 2. Run the review passes in parallel

Read `REVIEW.md` for the passes this repo requires and their severity
thresholds. Launch them as subagents simultaneously — they are independent:

| Pass | Subagent | Asks |
|---|---|---|
| Bugs and logic | `sdlc-review-bugs` | Does it work? What input breaks it? |
| Security | `sdlc-review-security` | What can an attacker do that they should not? |
| Spec conformance | `sdlc-review-spec` | Does the diff do what `spec.md` and `plan.md` said, and nothing else? |

<!-- TODO: Add the passes specific to your organization — compliance,
     data classification, accessibility, licensing, performance budget —
     as further subagents, and list them in REVIEW.md. -->

### 3. Rank and record

Merge the passes' output into `.sdlc/<slug>/review.md`, ranked by severity, and
post it to the PR. For each finding: the file and line, what breaks and under
what input, and the smallest correct fix.

Apply the severity thresholds from `REVIEW.md`:

| Severity | Meaning | Effect |
|---|---|---|
| Blocker | Data loss, security hole, spec not met | Must be fixed before merge |
| Major | Wrong under a realistic input; missing test for a stated requirement | Fix, or a written decision to defer |
| Minor | Style, naming, non-load-bearing duplication | Author's discretion |

Report zero findings as zero findings. Padding a review with minor remarks to
look thorough trains people to skim it.

### 4. Address findings on Claude's own PRs

When Claude authored the PR, it fixes what the passes found and pushes. When a
human comments (or mentions Claude in a PR thread), respond in the thread with
the change made, or with the reason the finding does not hold — never silently.

### 5. Merge gate

A human code owner approves. Then merge triggers the pipeline. If findings
above the threshold are outstanding, say so plainly rather than letting the
approval carry them through.

Findings that are real but out of scope for this PR do not disappear: promote
each to a new work item with its own spec (see `sdlc-orchestrator`).

### 6. Release gate

Production deploys require a named human authorization, enforced by a hook —
not by a checkbox and not by Claude's judgement. Staging is controlled; local
is free. See the autonomy tiers in `sdlc-orchestrator`.

Before the first automated deploy, rehearse the rollback path and prove it
works. An automated deploy without a proven rollback is an automated incident.

### 7. Feed the gaps back

A finding that got through to production, or a policy gap the passes missed,
goes back into the guardrails: `CLAUDE.md` for conventions, a skill for
consistently applied policy, a hook for policy that must always hold,
`REVIEW.md` for a missing pass. Configuration changes run the evals.

## Claude in the pipeline

Claude runs non-interactively in CI for the judgement steps that scripts do
badly: triaging a failure to the likely commit, drafting a changelog from
merged PRs, summarizing what a release contains.

Constraints for pipeline runs:

- Sandboxed execution with a network allowlist.
- Scoped, short-lived credentials — never the deploy key.
- Deployment actions exposed as MCP tools with typed inputs, not as shell
  scripts the agent composes freely.

<!-- TODO: Name your CI system, the deploy MCP server or tooling, the branch
     protection rules in force, and who may authorize a production release. -->
