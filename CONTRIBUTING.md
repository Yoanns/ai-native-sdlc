# Contributing

## Before you open a PR

```bash
claude plugin validate .claude-plugin/plugin.json   # manifest
python3 scripts/validate.py                         # every file against its schema
claude plugin eval .                                # behaviour, with and without the plugin
```

Then, if you touched a skill, an agent, a guard, the templates or `mirror/`:

```bash
python3 scripts/test_mirror.py                      # guards, spec gate, mirror build, installer
```

The validator and the tests run in CI on every push. The eval run costs model calls, so it
is not automated here — run it locally when you change a skill description, a
stage's rules, or anything the three eval cases assert.

## Changing a skill

Skill frontmatter accepts a fixed set of keys and **rejects unknown ones with
an error**. Keep to `name`, `description` and `metadata` unless you have
checked the [skills reference](https://code.claude.com/docs/en/skills).

A skill's `description` is what decides whether it triggers. If you change how
a stage is invoked, run the matching eval case and check the
`tool_used: Skill` grader before and after.

Keep bodies under about 1,500 words. Detail belongs in `references/`, which
loads only when needed.

## Changing an agent

The `description` must be a YAML literal block scalar (`description: |`) with
the `<example>` blocks indented under it. Written flat, the frontmatter does
not parse and the agent silently fails to load — this was a real defect here,
so `scripts/validate.py` checks it.

## Changing a hook

Hook scripts read the event JSON on stdin and print a decision on stdout:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse",
 "permissionDecision":"deny",
 "permissionDecisionReason":"why, in a sentence the user can act on"}}
```

Test it by piping a sample payload in — `templates/hooks/README.md` has one
per hook — and confirm it denies what it should and allows what it should.
Never ship a hook you have not triggered.

## Adding a review pass

1. Write `agents/sdlc-review-<name>.md` with a literal-block description.
2. Add a row to `templates/REVIEW.md` so Stage 4 knows to run it.
3. Add a row to the table in `skills/sdlc-deploy-review/SKILL.md`.
4. Add an eval case if the pass encodes a rule that must hold under pressure.

## The mirror

agent-native-sdlc is generated from this repository; never edit it directly.
Every change here reaches it on the next push to `main`, so check the build
before opening a PR:

```bash
python3 scripts/build_mirror.py --out build/mirror
python3 scripts/test_mirror.py
```

The build rewrites Claude Code vocabulary for other agents and then **fails on
any Claude-specific term left over** — "Claude", `CLAUDE.md`, `.claude/`,
"plan mode", a skill or agent name. If you add one to a skill:

- If it has a meaning for any agent, add a rule to `PHRASES` in
  `scripts/build_mirror.py` that says the same thing agent-neutrally.
- If the line is legitimately about Claude Code, allow it for that file in
  `ALLOWED`.

Changes to the guard scripts must keep the Claude dialect's output unchanged —
`test_mirror.py` checks it. Mirror-only content (its README, setup guide,
adapter configs, installer) lives in `mirror/overlay/`. See
[mirror/README.md](mirror/README.md).

## Documentation

Any claim about a Claude Code file format needs a citation in
[SOURCES.md](SOURCES.md). If you find one of these claims is now wrong, fix
`scripts/validate.py` first — the expected key sets live there — then the
files it checks, then the citation.

## Style

Skill bodies are instructions for Claude: imperative, verb-first, specific.
Documentation is for humans: say what a thing does and when it fires, not that
it is powerful or comprehensive.
