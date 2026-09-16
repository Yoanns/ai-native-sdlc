---
slug: <work-item-slug>
title: <one line, plain language>
author: <who asked for this>
created: <YYYY-MM-DD>
status: draft            # draft | in-review | approved | rejected
approved_by:
approved_at:
source: <chat | ticket #123 | incident YYYY-MM-DD | review finding on PR #45>
---

# <Title>

## Problem

What is wrong or missing today, in the requester's own words. No solution here.

## Outcome

What is true once this ships. Observable statements, not adjectives.

## Users

Who touches this, and how often.

## Requirements

<!-- Number them. Stage 2 names a test for each, Stage 4 reviews the diff
     against them. A requirement no test can prove is not a requirement yet. -->

1.
2.
3.

## Design

Behaviour, contracts, and data — not line-level implementation.

### Interfaces

APIs, schemas, events, config, feature flags this introduces or changes.

### Data

What is stored, where, for how long, and its classification.

### Failure modes

What happens when a dependency is down, input is malformed, the user is
unauthorized, the operation is retried.

<!-- For UI work: link the mock here. Stage 3 verifies the built screen
     against it. -->

## Out of scope

What this deliberately does not do.

## Flagged concerns

<!-- Anything touching security, privacy, data classification, licensing,
     pricing, accessibility, regulation, or an irreversible migration.
     Flag it with an owner; do not resolve it alone.
     Every row must be resolved or accepted before status: approved. -->

| Concern | Standard or policy | Owner | Status |
|---|---|---|---|
|  |  |  | open |

## Open questions

| Question | Who can answer | Blocking? |
|---|---|---|
|  |  |  |

## Success criteria

How anyone can tell, after release, whether this worked. Name the metric or
the observable behaviour.

## Evidence

<!-- For findings promoted from Stage 5: logs, metric snapshots, the
     correlating change, the reproduction. Delete this section otherwise. -->
