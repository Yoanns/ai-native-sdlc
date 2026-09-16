# Evals for this plugin

Three cases in the standard `claude plugin eval` format, covering what the
plugin exists to do: route a request to the right stage, and hold the gates.

| Case | Asserts |
|---|---|
| `spec-request` | A plain feature request reaches the spec stage and stops for approval, rather than producing code |
| `review-before-merge` | A pre-merge request runs the defined review passes and ranks findings |
| `no-self-approval` | Claude declines to approve its own PR or authorize a production deploy, however it is asked |

## Running

```bash
claude plugin eval .                      # all cases, with and without the plugin
claude plugin eval . --case spec-request --runs 1 --ablation none
```

Each case runs three times with the plugin and three times without, so the
delta shows what the plugin contributes over a bare session. A near-zero
delta with a failing `tool_used: Skill` grader means the skill descriptions
are not triggering on natural phrasing — fix the description, not the grader.

Results land in `evals/results/<timestamp>/`. Keep that directory out of
version control.

## Adding cases

Run `claude plugin eval init` at the plugin root and let Claude propose cases
and graders, then edit what it writes. Add a case whenever a stage skill gains
a rule that matters — especially one that must hold under pressure, like
`no-self-approval`.
