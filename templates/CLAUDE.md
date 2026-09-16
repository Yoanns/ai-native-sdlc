<!--
  Keep this under one page. It is read in full at the start of every session,
  so every line competes with every other for attention.
  Delete anything that is generic good practice. Keep only what is true of
  THIS repository. Changes here are configuration changes: run the eval suite.
-->

# <Repo name>

<One sentence: what this service or application does.>

## Commands

<!-- TODO: Replace with the real, verified invocations. Run each one before
     writing it down. -->

| Task | Command |
|---|---|
| Install | `TODO:` |
| Build | `TODO:` |
| Test (all) | `TODO:` |
| Test (single file) | `TODO:` |
| Lint | `TODO:` |
| Format | `TODO:` |
| Typecheck | `TODO:` |
| Run locally | `TODO:` |

## Conventions

<!-- TODO: Only what differs from the language's default. Examples of the
     shape to aim for — replace all of these. -->

- Errors: `TODO: how errors are constructed, wrapped, and surfaced`
- Logging: `TODO: logger, levels, what must never be logged`
- Imports: `TODO: ordering, absolute vs relative, forbidden imports`
- Tests: `TODO: framework, file placement, naming, fixtures`
- Commits: `TODO: message format and branch naming`
- Types: `TODO: strictness rules, banned constructs`

## Architecture

<!-- TODO: The module map and the boundaries that matter. Name the rule that
     must not be broken, not just the folder list. -->

```
TODO: src/
        api/        ...
        domain/     ...
        infra/      ...
```

- `TODO: which layer may import which`
- `TODO: where business logic must live`
- `TODO: what talks to the database`

## Protected paths

Do not edit without explicit human instruction. Backed by hooks in
`.claude/hooks/`:

- `TODO: db/migrations/**`
- `TODO: **/generated/**`
- `TODO: infra/**`
- `TODO: **/*.test.* during a bug fix`

## Common mistakes

<!-- TODO: Harvest these from repeated review comments in git history.
     State each as a rule, with the reason. -->

- `TODO: mistake -> rule -> why`
- `TODO:`
- `TODO:`

## Lifecycle

Work runs through the SDLC stages: spec -> build -> test -> deploy -> maintain.
Artifacts live in `.sdlc/<work-item-slug>/`. Review passes and severity
thresholds are in `REVIEW.md`. Do not start implementing without an approved
`spec.md` and an accepted `plan.md`.
