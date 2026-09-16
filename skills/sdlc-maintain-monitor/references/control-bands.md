# Control bands

The watcher is a deterministic script, not an agent. It decides *whether* to
wake Claude; Claude decides nothing about its own invocation. Keeping that
boundary is what stops monitoring from becoming an unbounded loop.

## Choosing metrics

Pick metrics that (a) move when something is wrong and (b) do not move
otherwise. Four that earn their place in most repos:

| Metric | Window | Why |
|---|---|---|
| Test failure rate on main | Rolling 20 runs | Catches flake accumulation and broken merges |
| Post-deploy 5xx / error rate | 30 min after each deploy | Catches what staging did not |
| PR cycle time (open → merge) | Rolling 14 days | Catches review bottlenecks and oversized changes |
| p95 latency on the top endpoints | Rolling 24 h | Catches slow regressions before users report them |

<!-- TODO: Replace with the metrics your systems actually emit, and the source
     each is read from (CI API, APM, logs, tracker API). -->

## Computing the band

For each metric keep a rolling baseline — mean and standard deviation over the
window, excluding periods already marked as incidents. Compare the current
value against it:

```
deviation = |current - mean| / stddev
```

| deviation | Action |
|---|---|
| < 1σ | Append to the log. Nothing else. |
| 1σ – 2σ | Log, and mark for the daily digest. |
| 2σ – 3σ | Wake Claude with read-only tools. Diagnose, write a finding. |
| > 3σ | Wake Claude with act-permitted tools: open a PR, or run a pre-approved runbook. |

For metrics with a hard contractual limit (an SLO, an error budget), use the
limit as the band instead of a statistical one — 2σ below an SLO breach is
still a breach.

## Guards the watcher needs

- **Cooldown.** One invocation per metric per window. Without it, a sustained
  deviation wakes Claude every tick.
- **Deduplication.** If a finding for this metric and window is already open,
  append evidence to it rather than creating a second.
- **Quiet hours / deploy freeze awareness.** Suppress the low tiers, never the
  3σ tier.
- **Kill switch.** One flag that disables agent invocation entirely, readable
  without a deploy.
- **Budget.** A cap on invocations per day. Hitting the cap is itself a signal
  worth a human's attention.

## Pre-approved runbooks

At 3σ, Claude may run only actions that were written down and approved in
advance — restart a worker, roll back to the previous release, scale a pool,
disable a feature flag. Each runbook states its trigger, its steps, its blast
radius, and its own rollback. Anything not in a runbook is a PR, not an action.

<!-- TODO: List your pre-approved runbooks and where they live. Start with
     zero and add only what has been rehearsed. -->

## Tuning loop

Every dismissed finding gets a one-line record: metric, value, why it was
noise, what was changed. Review the records monthly. A metric that produces
mostly dismissals is measured wrong, banded wrong, or should not wake anyone.

A starter watcher script is at
`${CLAUDE_PLUGIN_ROOT}/templates/monitor/watch-metrics.sh`.
