---
name: sdlc-maintain-monitor
description: >
  This skill should be used after a release, when investigating production
  signals, or when the user says "why did this metric move", "triage this
  alert", "run the security scan", "write the post-mortem", "set up
  monitoring", or when a monitoring job wakes Claude with a metric outside its
  control band. Diagnoses within the tier the signal earns and promotes real
  findings into a new spec.
metadata:
  version: "0.1.0"
---

# Stage 5 — Maintain

Monitoring triggers the agent without a human having to notice first. Findings
loop back to Stage 1 as a spec, so maintenance work travels the same gated path
as feature work.

## Response tiers

A deterministic script watches metrics against a rolling baseline and control
bands. What Claude is allowed to do depends on how far out the signal is:

| Deviation | Response | Tools |
|---|---|---|
| 1σ | Log only. No agent invocation. | — |
| 2σ | Claude diagnoses. | Read-only: logs, metrics, code, git history |
| 3σ | Claude may act. | Open a PR, or trigger a pre-approved runbook |

At 3σ, "act" still means proposing through the normal gates. Opening a PR is
acting; merging it is not Claude's to do.

<!-- TODO: Confirm the metrics watched and their bands, e.g.
     test failure rate, post-deploy 5xx rate, PR cycle time, p95 latency,
     error budget burn. Set the window and baseline per metric. -->

## Diagnosing (2σ)

Stay read-only. Work the evidence in this order:

1. **Bound it.** When did it start, which environment, which surface, how many users.
2. **Correlate.** What deployed, merged, or changed in configuration in that window.
3. **Reproduce.** Find the smallest input that shows the behaviour, if one exists.
4. **Separate cause from symptom.** Say which one you have. Do not present a correlation as a cause.

State confidence honestly. "The 5xx rate rose 40 minutes after deploy abc123,
which touched the same endpoint" is useful. "Deploy abc123 caused the outage"
without a reproduction is a guess wearing a suit.

## Writing the finding

Every finding, whatever its source, is written up as a new spec seeded with
evidence. Use `${CLAUDE_PLUGIN_ROOT}/templates/spec.md` and fill:

- **Problem** — the signal, the window, the magnitude, the affected users.
- **Evidence** — logs, metric snapshots, the correlating change, the reproduction.
- **Proposed outcome** — what should be true once fixed.
- **Affected systems** — services, jobs, data.
- **Open questions** — what could not be determined read-only.

Then hand to the on-call engineer for triage. They decide: real or noise.

## Triage tunes the bands

A dismissal is data. When a finding is dismissed, adjust the band, the window,
or the metric so that signal does not fire again. Monitoring that cries wolf
gets muted, and muted monitoring is worse than none.

Record each dismissal and what was tuned, so the tuning itself is reviewable.

## Recurring scans

Run security and dependency scans on a schedule against the repository. For
each finding: validate it before reporting — an unvalidated scanner finding is
noise with a CVE number attached. Small, clearly-scoped fixes go out as a PR
through the normal review gate. Anything structural becomes a spec.

## Incidents and chat

When Claude is present in the team's incident or support channel:

- Answer with evidence gathered through read-only tools.
- Verify a claimed fix rather than accepting it — check the metric, not the
  message saying it is fixed.
- Write the post-mortem into a version-controlled lessons file, not only into
  the thread. Chat scrolls away; the repo does not.

Every post-mortem produces at least one of: an eval case, a `CLAUDE.md` entry,
a hook, or a new review pass. An incident that changes nothing will recur.

<!-- TODO: Name the incident channel, the on-call rotation, the lessons file
     path (e.g. docs/lessons/), and the scan schedule. -->

## Reference

- `references/control-bands.md` — choosing metrics, computing baselines, setting bands, and wiring the watcher.
