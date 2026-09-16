---
name: sdlc-build-plan
description: >
  This skill should be used when an approved spec is ready to be implemented,
  or when the user says "let's build this", "write the implementation plan",
  "plan this out before coding", "start on the spec", or asks for code on a
  work item that has a spec.md. Produces a committed plan.md naming the files
  that change, the order of the work, and the tests that prove it, and only
  then writes code.
metadata:
  version: "0.1.0"
---

# Stage 2 — Build

Work starts with a written plan, not with code. The plan is the design review;
it happens before generation, not after.

## Preconditions

Refuse to start until `.sdlc/<slug>/spec.md` exists with `status: approved`.
If it does not, hand back to `sdlc-design-spec`.

## Procedure

### 1. Enter plan mode

Go read-only. Do not edit a single file until the plan is accepted. This is
not a formality — it is what makes the design review possible while it is
still cheap.

Read, in this order:

1. `CLAUDE.md` — commands, conventions, architecture, common mistakes.
2. `.sdlc/<slug>/spec.md` — including flagged concerns and their resolutions.
3. The actual code the change touches, plus its tests.

### 2. Write the plan

Copy `${CLAUDE_PLUGIN_ROOT}/templates/plan.md` to `.sdlc/<slug>/plan.md`.

A plan names three things and is not finished without all three:

- **The files that change** — every path, with one line on what changes in it, and which are new.
- **The order of the work** — numbered steps that each leave the repo in a working state.
- **The tests that prove it** — for each requirement in the spec, the test that demonstrates it, named and located.

Add:

- **Interfaces touched** — public APIs, schemas, migrations, config, feature flags.
- **Risks and rollback** — what could go wrong, and how a deploy is undone.
- **Out of scope** — carried forward from the spec, plus anything discovered while reading the code.

### 3. Invite interrogation

Present the plan and ask the engineer to attack it. Prompt specifically:

- Is the sequencing right, or does step N break the build?
- Is there an existing helper or pattern this ignores?
- Are the named tests the ones that would actually catch a regression?
- What did the plan miss because it did not read far enough?

Iterate until the engineer accepts it. A rejected plan is cheap; a rejected
diff is not.

### 4. Record the gate, then implement

Set `status: approved` in the plan's front matter and commit it. Only then
leave plan mode.

While implementing:

- Follow the plan's order. If reality forces a change of course, stop, say so,
  update `plan.md`, and continue — never let the plan and the diff drift apart.
- Run the repo's own verification loop continuously: build, tests, lint. See
  `sdlc-test-verify` for what a good loop looks like.
- Auto mode is appropriate for routine, well-specified work behind hooks that
  protect what must not change. Step through manually when touching a protected
  path, a migration, or anything the spec flagged.

### 5. Keep the artifacts in sync

Before opening a PR, the branch must contain `spec.md` and `plan.md` matching
what was actually built. Stage 4's review passes read them as the definition of
correct.

Commit message: `feat(<slug>): <one-line outcome>` (or `fix`, `chore`, per the
repo's convention).

<!-- TODO: Replace with your repo's commit convention and branch naming rules. -->

## Working in parallel

For independent work items, use one git worktree per item and one session per
worktree. Never run two work items in one session: their contexts contaminate
each other and their artifact chains tangle.

## Subagents

Delegate recurring, scoped jobs to subagents with narrow tool access:

- **Verification** — run the build and tests, report failures with the smallest reproducing case.
- **Exploration** — locate every call site of a symbol across a large codebase.
- **Migration sweeps** — apply one mechanical change across many files, reporting anything that did not fit the pattern.

Give each subagent the plan step it serves and nothing more of the context.

## Quality bar

Do not report the build done until: the plan's steps are all complete or
explicitly deferred in writing, the named tests exist and pass, the build
succeeds, and the linter is clean.
