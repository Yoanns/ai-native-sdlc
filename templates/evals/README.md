# Eval suite

Regression tests for agent configuration. `CLAUDE.md`, skills, hooks and
settings steer every session that follows them — changing one is a
behavioural change with no diff to review. This is what catches that.

These cases use the standard `claude plugin eval` format, so the runner is the
CLI, not a script of your own.

## Layout

```
evals/
├── <case-name>/
│   ├── prompt.md            # frontmatter: case fields; body: the prompt
│   ├── graders/
│   │   └── <name>.md        # frontmatter: type + options; body: rubric
│   └── <fixtures the case needs>
└── results/<timestamp>/     # written by each run — git-ignore this
```

Three example cases ship here. Replace the `TODO:` values with real paths and
commands from your repo, then grow the suite toward 20–50 cases drawn from
real past work.

## Running

```bash
# every case
claude plugin eval .

# one case, one arm, while iterating
claude plugin eval . --case bugfix-keeps-the-test --runs 1 --ablation none
```

If your guardrails live in the repository rather than in an installed plugin,
there is nothing to ablate — run with `--ablation none` and read the score
directly. If you package them as an internal plugin, the default two-arm run
also tells you what the guardrails are contributing over a bare session.

Have Claude write new cases for you with `claude plugin eval init` rather than
hand-writing them; the files it produces are plain text you can then edit.

## Grader types available

| Type | Asserts |
|---|---|
| `regex` | A pattern appears (or, with `match: not_contains`, does not) in the reply, the trace, the created-file list, or one file's contents |
| `tool_used` | A tool was called a given number of times, optionally with input matching a pattern. `min: 0, max: 0` asserts it was never called |
| `tool_order` | One tool call preceded another |
| `file_exists` | A file matching a glob was created during the run |
| `llm` | A judge model votes on a rubric — for outcomes no pattern can express |
| `baseline` | The run is at least as good as a recorded reference transcript |

Note what is *not* there: there is no "run this command and check the exit
code" grader. Express "the tests pass" as an `llm` grader over the `trace`,
or have the case's prompt make the result visible in the reply and match it
with `regex`.

## When to run it

On any pull request that touches:

- `CLAUDE.md`
- `.claude/skills/**`, `.claude/agents/**`
- `.claude/hooks/**`, `.claude/settings*.json`
- `REVIEW.md`

Gate the merge on the result: a configuration change that lowers the score
does not merge, the same as a code change that breaks a test.

<!-- TODO: wire `claude plugin eval .` into CI and decide the threshold.
     The usual choice is "no regression against main's last run". -->

## Growing the suite

| Trigger | Case to add |
|---|---|
| Production incident | The scenario that caused it, expecting the corrected behaviour |
| A review finding a pass should have caught | A case asserting the pass catches it |
| Claude repeatedly getting a convention wrong | A case asserting the convention, alongside the `CLAUDE.md` entry |
| A hook that fired correctly in anger | A case asserting it still fires |

Never delete a case to make the suite green. Fix the configuration, or record
why the expectation changed.
