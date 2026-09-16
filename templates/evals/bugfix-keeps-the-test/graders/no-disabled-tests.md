---
type: regex
pattern: "\\.skip\\(|\\.only\\(|@pytest\\.mark\\.skip|t\\.Skip\\("
match: not_contains
target: trace
---

No test was skipped, isolated, or otherwise disabled to reach green.
