---
name: sdlc-test-verify
description: >
  This skill should be used when code needs verifying before human review, when
  fixing a bug, or when the user says "write tests for this", "make sure this
  works", "verify before I look at it", "the tests are failing", or changes
  CLAUDE.md, a skill, or a hook and needs the eval suite run. Covers feedback
  loops, test-first bug fixing, visual verification, and continuous evals.
metadata:
  version: "0.1.0"
---

# Stage 3 — Test

Verify the work before spending a human's attention on it. A session that
reports "done" without having run anything has not finished; it has stopped.

## Rule 1 — Always have a feedback loop

Never generate code that cannot be checked. Before starting, establish how this
change will be proven:

| Kind of change | Loop |
|---|---|
| Logic, data, API | Unit and integration tests, run after every edit |
| Build or config | The build itself, plus a smoke run |
| UI | Screenshot against the mock from the spec; iterate until they match |
| CLI or script | Execute it against a fixture and diff the output |
| Performance | A benchmark with a recorded baseline number |

Iterate against the loop until it passes. Show the final passing output — not
a claim that it passed.

<!-- TODO: Replace with this repo's real commands, e.g.
     build: make build | test: make test | lint: make lint | e2e: make e2e -->

## Rule 2 — Bugs are fixed test-first

In this exact order, no shortcuts:

1. **Write the failing test.** It must reproduce the reported behaviour.
2. **Run it and read the failure.** Confirm it fails *for the expected reason*,
   not because of a typo or a missing fixture. A test that fails for the wrong
   reason proves nothing.
3. **Commit the test on its own.** This is the proof that the bug existed.
4. **Fix the code without touching the test.** If the test genuinely encodes
   the wrong expectation, stop and say so — do not quietly relax it.
5. **Run the whole suite.** A green target test with a red neighbour is not a fix.

A test that existed before the fix is the evidence the bug is gone. A test
written after the fix only proves the code does what it does.

## Rule 3 — Protect the tests

Hooks should block agent edits to test files during a fix. If an edit is
blocked, that is the guardrail working: explain what the test asserts, why the
code cannot satisfy it, and let a human decide. See
`sdlc-setup-guardrails`.

## Rule 4 — Visual work gets visual proof

For UI changes: take the mock from the spec, render the built screen, compare
them, and iterate. Report the final comparison. Check the states that mocks
usually omit — empty, loading, error, long content, narrow viewport.

## Rule 5 — Configuration changes run the evals

`CLAUDE.md`, skills, hooks, and settings are code that steers every future
session. Changing them without regression testing is changing behaviour blind.

Run the eval suite whenever any of them changes, and gate the merge on the
result. See `references/evals.md` for how to build and run the suite.

Every production incident earns a permanent eval case. The suite only grows.

## Definition of done

Report done only when all of these hold, and say which ones ran:

- [ ] Tests pass — the new ones and the existing ones
- [ ] Build succeeds
- [ ] Linter and formatter clean
- [ ] Evals green, if configuration changed
- [ ] The plan's named tests all exist
- [ ] Coverage of the risky paths named in the spec, not just the happy path

If something is failing and cannot be fixed, say exactly what fails and why.
Never report done with a known red check.

## Anti-patterns

- Deleting or skipping a failing test to get green.
- Loosening an assertion (`toBeGreaterThan(0)` where a value was specified).
- Mocking the very thing under test.
- Testing implementation detail rather than the behaviour the spec asked for.
- Asserting only the happy path when the spec names failure modes.
