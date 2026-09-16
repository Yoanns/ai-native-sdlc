---
type: llm
focus: last_message
weight: 2
---

PASS if the response does the spec stage's job: captures the problem and the
intended outcome, asks the requester the questions it cannot answer itself
(users, affected systems, constraints, success criteria), and says the spec
needs approval before build planning starts.

FAIL if it jumps to an implementation plan, writes code, or answers with
generic advice that produces no spec.
