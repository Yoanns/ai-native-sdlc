<!-- sdlc:begin — managed by agent-native-sdlc {{version}}. Re-running the installer
     replaces everything between these markers; edit the rest of this file freely. -->
## Lifecycle

All work in this repository runs through five stages. Each stage reads the
artifact the previous stage committed and commits its own; together they are
the audit trail. A human decides at every gate.

| # | Stage | Read before starting | Produces | Gate — decided by |
|---|---|---|---|---|
{{stage_table}}

**Which stage am I in?** Look in `.sdlc/<work-item-slug>/` and read the
`status:` in each artifact's front matter. No spec yet → stage 1. Spec
approved → stage 2. Plan approved and code written → stage 3. Green → stage 4.
Released → stage 5. `.sdlc/playbook/README.md` has the full routing.

**Before you act in any stage, read its playbook file and follow it.** Say out
loud which stage you are in, what you are producing, and who owns the gate.

### Rules that do not bend

- **No code without an approved spec and an accepted plan.** Both carry
  `status: approved` in their front matter. CI enforces this
  (`.sdlc/enforcement/spec_gate.py`); do not try to get around it.
- **Stop at every gate.** Present what you produced, name the decision, and
  wait. Never approve on a human's behalf, and never start the next stage in
  the same turn as the request for approval.
- **Never approve your own work.** You write; you review other people's
  changes; a human approves.
- **Production needs a named human authorization.** You cannot authorize your
  own deploy.
- **Never weaken a test to make it pass.** Bugs are fixed test-first: the
  failing test is committed on its own, then the fix, without touching it.
- **Findings loop back as specs**, never as silent patches.

### Recording a gate decision

```yaml
---
status: approved          # draft | in-review | approved | rejected
approved_by: <name>       # the human who owns this gate
approved_at: <YYYY-MM-DD>
---
```

Review passes for stage 4 are in `.sdlc/playbook/review-passes/`. Setting up
or changing the guardrails: `.sdlc/playbook/setup.md`.
<!-- sdlc:end -->
