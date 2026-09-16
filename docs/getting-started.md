# Getting started

From install to a first work item through all five stages.

## 1. Install

```
/plugin marketplace add yoanns/ai-native-sdlc
/plugin install ai-native-sdlc@ai-native-sdlc
```

Confirm it loaded: the seven `sdlc-*` skills appear in `/plugin`, and the
three review agents in the agent list.

## 2. Set up one repository

Open Claude Code in the repository and say:

> set up the SDLC guardrails

### What it does

It reads the repo before writing anything — `Makefile`, `package.json`, CI
workflows, the directory layout, the conventions visible in the code, and the
review comments that recur in git history. Then it writes:

| File | Built from |
|---|---|
| `CLAUDE.md` | The commands it found and verified, the conventions it observed, the module boundaries, the mistakes that recur |
| `REVIEW.md` | The three default passes, plus whatever you tell it your domain needs |
| `.claude/hooks/scripts/*.sh` | The templates, with your protected paths and deploy commands |
| `.claude/settings.json` | Permissions, sandbox, network allowlist |
| `evals/` | Three example cases to adapt |
| `.sdlc/TEMPLATES/` | The spec and plan shapes |

### What it will ask you

Anything it cannot read off the repo. Expect questions about:

- **Who authorizes a production release**, and how that is recorded.
- **Which review passes your domain needs** beyond bugs, security and spec
  conformance — compliance, data classification, accessibility, licensing.
- **What counts as a protected path** here.
- **Where specs live**: in the repo, in a tracker, or mirrored between them.
  Name one source of truth.

It will not invent answers to these. Unanswered ones stay visible as `TODO:`
markers, listed back to you at the end.

### Before you trust the hooks

Trigger each one once. `templates/hooks/README.md` has a one-line test per
hook; each should print a `deny` decision with a readable reason. An untested
hook is a comment.

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"cat .env"}}' \
  | .claude/hooks/scripts/block-credentials.sh
```

### Commit it

One commit. From here, changes to any of these files are configuration
changes and run the eval suite.

## 3. Run a work item

### Stage 1 — Spec

> Customers keep asking for their invoices as a single PDF instead of one per
> order. Can we add that?

Claude asks what it cannot infer — who uses this, which systems it touches,
what is out of scope, how you will know it worked — writes
`.sdlc/invoice-pdf-bundle/spec.md`, and stops.

**Your move:** read the spec, resolve any flagged concerns with their owners,
say it is approved. Claude records the approval in the front matter and
commits.

### Stage 2 — Build

> let's build it

Claude goes read-only, reads the spec and the code it touches, and produces a
plan: the files that change, the order of the work, the test that proves each
requirement.

**Your move:** attack the plan. Is the sequencing right? Does it ignore an
existing helper? Are those the tests that would actually catch a regression?
Iterate until it is right, then accept — a rejected plan is cheap, a rejected
diff is not.

Claude then implements, updating `plan.md` if reality forces a change of
course.

### Stage 3 — Test

Verification runs as part of building: tests, build, lint, and for UI work a
screenshot against the mock. Claude reports what it ran and what the output
was, not a claim that it passed.

If you are fixing a bug rather than adding a feature, the order is fixed:
failing test first, confirmed to fail for the right reason, committed on its
own, then the fix — without touching the test.

### Stage 4 — Deploy

> review this PR

Three passes run in parallel and their findings land in `review.md` and on the
PR, ranked by severity.

**Your move:** approve, or send it back. Claude cannot approve its own work,
and the release hook will refuse a production deploy that carries no named
authorization.

### Stage 5 — Maintain

After release, signals come back: a metric outside its band, a scheduled scan,
an incident. Claude diagnoses within the tier the signal earns and writes the
finding up as a new spec.

**Your move:** triage. Real, or noise? A dismissal is data — tune the band so
that signal does not fire again.

## 4. Grow the guardrails

Every loop should leave the configuration better than it found it:

| What happened | Where it goes |
|---|---|
| Claude got a convention wrong twice | `CLAUDE.md` → Common mistakes |
| A policy was applied inconsistently | A skill |
| A policy must never be violated | A hook |
| A review pass missed a defect class | `REVIEW.md` |
| Something reached production | A permanent eval case |

Changes to any of those run `claude plugin eval` before merging, because they
change behaviour with no diff to review.

## Troubleshooting

**The skills do not trigger on my phrasing.** Run
`claude plugin eval . --case spec-request --runs 1 --ablation none` and look
at the `tool_used: Skill` grader. If it fails, the skill description is the
thing to fix.

**A hook is not firing.** Check it is installed where Claude Code reads it —
either merged into `.claude/settings.json` under the `hooks` key, or at
`.claude/hooks/hooks.json` with the same `{"hooks": {...}}` wrapper — and that
the scripts are executable.

**A permission rule seems ignored.** A malformed rule is skipped with a
warning rather than failing the file. Check the syntax: `Tool(pattern)`, with
`:*` for prefix matching.

**Claude skipped a gate.** Check the artifact's front matter actually says
`status: approved`. The orchestrator routes on that field.
