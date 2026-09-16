---
slug: <work-item-slug>
spec: ./spec.md
engineer: <who owns this build>
created: <YYYY-MM-DD>
status: draft            # draft | in-review | approved | superseded
approved_by:
approved_at:
---

# Implementation plan — <title>

## Approach

Two or three sentences: the shape of the change and why this way rather than
the obvious alternative.

## Files that change

| Path | New? | Change |
|---|---|---|
|  | no |  |
|  | yes |  |

## Order of work

<!-- Each step leaves the repo building and green. If a step cannot, say so
     and name the step that restores it. -->

1.
2.
3.

## Tests that prove it

<!-- One row per requirement in the spec. A requirement with no test is not
     planned yet. -->

| Spec requirement | Test | Location | Kind |
|---|---|---|---|
| 1 |  |  | unit / integration / e2e / visual |
| 2 |  |  |  |

## Interfaces touched

Public APIs, schemas, migrations, config keys, feature flags, events.

## Risks and rollback

| Risk | Likelihood | Mitigation |
|---|---|---|
|  |  |  |

**Rollback:** how a released version of this is undone, and whether it has
been rehearsed.

## Out of scope

Carried from the spec, plus anything discovered while reading the code.

## Deviations

<!-- Filled in during implementation. If reality forces a change of course,
     record it here rather than letting the plan and the diff drift apart. -->

| Step | What changed | Why |
|---|---|---|
