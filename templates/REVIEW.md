# Review policy

Defines the passes every pull request is reviewed against, the severity scale,
and what blocks a merge. Read by the `sdlc-deploy-review` skill; changes here
are configuration changes and run the eval suite.

## Separation of duties

- Claude may review any pull request, including ones a human wrote.
- Claude may **not** approve a pull request it authored.
- Merge requires approval from a human code owner (enforced by branch protection).
- Production release requires a named human authorization (enforced by hook).

## Passes

All passes run in parallel against the diff, with `spec.md` and `plan.md` from
the branch as the definition of correct.

| Pass | Subagent | Scope |
|---|---|---|
| Bugs and logic | `sdlc-review-bugs` | Correctness, edge cases, concurrency, error handling, resource lifecycle |
| Security | `sdlc-review-security` | Authn/authz, input validation, injection, secrets, dependency risk, audit logging |
| Spec conformance | `sdlc-review-spec` | Every spec requirement met; nothing built that the spec did not ask for |

<!-- TODO: Add the passes your organization requires. Common additions:
     | Compliance        | ...  | GDPR/DSGVO, retention, data-subject rights, records |
     | Data classification | ... | Correct handling per class; no class crossing a boundary |
     | Accessibility     | ...  | WCAG 2.1 AA on changed UI |
     | Performance       | ...  | Budget for the changed path; no N+1 introduced |
     | Licensing         | ...  | New dependencies compatible with the project licence |
     Each addition needs a subagent in the plugin's agents/ directory. -->

## Severity scale

| Severity | Definition | Effect on merge |
|---|---|---|
| **Blocker** | Data loss, security vulnerability, a spec requirement not met, a broken public contract | Blocks merge |
| **Major** | Wrong under a realistic input; a stated requirement without a test; a failure mode unhandled | Blocks merge unless deferred in writing by the code owner |
| **Minor** | Naming, style, non-load-bearing duplication, docs | Author's discretion |

<!-- TODO: Confirm the blocking threshold. Default: Blocker and Major block. -->

## Finding format

Each finding states:

1. File and line.
2. What breaks, and the concrete input or state that breaks it.
3. Severity, per the scale above.
4. The smallest correct fix.

Zero findings is reported as zero findings. Do not pad a review with minor
remarks — it trains reviewers to skim.

## Out-of-scope findings

A real finding that does not belong in this PR is promoted to a new work item
with its own spec. It is never dropped and never smuggled into an unrelated
diff.

## Feedback into configuration

| What happened | Where it goes |
|---|---|
| A pass missed a defect class | New or sharpened pass here |
| A convention was violated repeatedly | `CLAUDE.md` → Common mistakes |
| A policy was applied inconsistently | A skill |
| A policy must never be violated | A hook |
| It reached production | A permanent eval case |
