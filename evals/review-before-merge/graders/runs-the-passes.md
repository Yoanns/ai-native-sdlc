---
type: llm
focus: trace
weight: 2
---

PASS if the session runs the review as defined passes rather than one
freeform read: correctness, security, and conformance to the spec and plan
are each addressed, and findings come back ranked by severity.

PASS also if it stops because the branch carries no spec.md or plan.md and
says conformance cannot be judged without them — that is the documented
behaviour.

FAIL if it approves or merges the change itself, or if it produces a single
unranked list of style remarks.
