# Scripts

## `validate.py`

Checks every file in the plugin against its documented schema:

- `plugin.json` and `marketplace.json` shape
- skill frontmatter — allowed keys only, name matching the directory,
  description within the 1,536-character limit
- agent frontmatter — valid YAML, allowed keys, name matching the filename
- eval cases and graders — allowed keys, known grader types, compilable regexes
- `hooks.json` — the top-level wrapper, known event names, prompt hooks
  carrying `$ARGUMENTS`
- `settings.json` — known keys, well-formed permission rules
- shell syntax, and that every `${CLAUDE_PLUGIN_ROOT}` reference resolves

```bash
python3 scripts/validate.py
```

Requires PyYAML. Runs in CI on every push, alongside a job that executes each
hook script against sample payloads and asserts the decision it returns.

The expected key sets come from the Claude Code documentation cited in
`SOURCES.md`. If a documented format changes, update this file first, then the
files it checks, then the citation.
