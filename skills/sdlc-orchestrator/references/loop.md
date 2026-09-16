# The loop

The traditional lifecycle is a line of handoffs. This one is a loop: the last
stage feeds the first, and the transitions fire automatically once their gate
passes.

## Re-entry points

Findings can arrive from four places. All of them re-enter at Stage 1 as a spec:

| Source | Produced by | Enters as |
|---|---|---|
| Metric outside its control band | Monitoring script | Spec seeded with the metric, the window, and the diff since baseline |
| Scheduled security scan | Recurring scan job | Spec seeded with the validated finding and a suggested patch |
| Incident or support thread | On-call, chat channel | Spec seeded with the timeline and the post-mortem lesson |
| Review finding out of scope for the current PR | Stage 4 review pass | Spec seeded with the finding and the PR it came from |

Never let a finding become a direct patch that bypasses the chain. A one-line
fix still gets a spec — a short one — because the spec is what makes the change
reviewable six months later.

## What loops back into configuration, not into code

Some findings are about how the agent works rather than what the code does.
Route these to the guardrails, and gate them on the eval suite:

| Finding | Goes to |
|---|---|
| Claude repeatedly gets a convention wrong | `CLAUDE.md` — add it to Common mistakes |
| A policy was applied inconsistently | A skill — encode it so it applies every time |
| A policy must never be violated, not merely encouraged | A hook — make it deterministic |
| A review pass missed a class of defect | `REVIEW.md` — add or sharpen the pass |
| A production incident occurred | The eval suite — add a permanent regression case |

Every change to `CLAUDE.md`, a skill, or a hook is a configuration change and
runs the eval suite before merging. See `sdlc-test-verify`.

## Legacy and external systems

For each artifact, name exactly one source of truth. Three workable shapes:

1. **Repository as source of truth.** Artifacts live in `.sdlc/`; the tracker
   holds a link. Simplest; best when engineering owns the process end to end.
2. **External system as source of truth.** The spec lives in the tracker or doc
   system; the repo holds a stable link and a short stub. Best when non-engineers
   author and approve specs in a tool they already use.
3. **Linked.** Artifacts live in the repo, and a job mirrors status back to the
   tracker. Most work to maintain; only worth it when both audiences need to
   read the current state without leaving their own tool.

Pick one shape per artifact type and write it into `CLAUDE.md`. Ambiguity here
is what produces two specs that disagree.

<!-- TODO: Record the chosen shape for each artifact:
     spec.md    -> repository | external | linked
     plan.md    -> repository | external | linked
     review.md  -> repository | external | linked
     and name the external system where applicable. -->
