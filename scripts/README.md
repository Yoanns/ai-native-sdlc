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

## `build_mirror.py`

Builds [agent-native-sdlc](https://github.com/yoanns/agent-native-sdlc), the
version of this lifecycle for agents other than Claude Code, and checks its
own output: it fails on any Claude-specific term left in the mirror, on a
reference to a playbook or template file that does not exist, and on invalid
JSON, front matter, shell or Python.

```bash
python3 scripts/build_mirror.py --out build/mirror
```

The output directory is replaced, except its `.git`. `mirror/README.md`
explains what goes into the mirror and how to change it.

## `test_mirror.py`

Tests what runs outside Claude Code: every guard in every hook dialect (and
the Claude dialect's output unchanged), the spec gate against real git
histories, the mirror build — clean, deterministic, and the leak check
actually failing on a planted leak — and the installer, fresh and re-run.

```bash
python3 scripts/test_mirror.py
python3 scripts/test_mirror.py -k Installer     # one group
```

Standard library only. Needs `bash` and `git`.

