# Continuous evals

Agent configuration — `AGENTS.md`, the playbook, rules, hooks, settings —
steers every session that follows it. A change to it is a behavioural change
with no diff to review. Evals are the regression tests for that.

## What the suite is

20–50 real tasks drawn from work this repo actually does, each with a check
that decides pass or fail. Not synthetic puzzles: past tickets, past bugs,
past reviews. Start with 5–10.

## Anatomy of a case

Whatever runner you use, a case has the same four parts:

| Part | Example |
|---|---|
| **Starting state** | A fixture: a copy of the repo at a commit, with a failing test in place |
| **Prompt** | "The test at `src/auth/refresh.test.ts` is failing. Fix the code so it passes." |
| **Checks** | The tests pass; the test file is unchanged; no test was skipped |
| **Origin** | The incident, review or ticket the case came from |

Checks that hold up are ones a script can decide without reading the reply:

| Check | How |
|---|---|
| The change works | Run the test command; check the exit code |
| A file was not touched | `git diff --quiet -- <path>` |
| Nothing was disabled | `grep` the diff for `.skip(`, `.only(`, `@pytest.mark.skip` |
| The lifecycle held | `python3 .sdlc/enforcement/spec_gate.py` against the result |
| A guard still fires | Pipe a sample event to the guard with `--format exit`; expect exit 2 |

Use a judge model only for outcomes no script can express, and treat its
verdict as noisier than the rest.

## Running

This playbook does not ship a runner, because there is no cross-agent
standard for one. The shape that works with any agent that has a
non-interactive mode:

1. Copy the fixture to a scratch directory.
2. Run your agent headless in it with the case's prompt.
3. Run the checks against the resulting working tree.
4. Record pass or fail per case, and the overall pass rate.

Run it on any pull request that touches `AGENTS.md`, `REVIEW.md`,
`.sdlc/playbook/`, `.sdlc/guards/`, or your agent's rule and hook directories,
and gate the merge on the result: a configuration change that lowers the pass
rate does not merge, the same as a code change that breaks a test.

## Growing the suite

| Trigger | Case to add |
|---|---|
| Production incident | The scenario that caused it, expecting the corrected behaviour |
| Review finding a pass should have caught | A case asserting the pass catches it |
| The agent repeatedly getting a convention wrong | A case asserting the convention, alongside the `AGENTS.md` entry |
| A guard that fired correctly in anger | A case asserting it still fires |

Never delete a case to make the suite green. Fix the configuration, or record
explicitly why the expectation changed.
