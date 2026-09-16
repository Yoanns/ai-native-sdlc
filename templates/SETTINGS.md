# Settings

`settings.json` in this directory is a starting point for the repo's
`.claude/settings.json`. It contains only valid entries, because a malformed
permission rule is skipped with a warning rather than failing loudly — a
placeholder left in an `allow` array silently does nothing.

So the decisions below are listed here rather than as `TODO:` strings inside
the JSON. Add each one as a real rule once you have decided it.

## Permissions

The rule format is `Tool(pattern)`; a trailing `:*` matches by command prefix.

| Decide | Add to | Example |
|---|---|---|
| Build, test, lint commands the workflow runs constantly | `allow` | `Bash(make test:*)`, `Bash(npm run lint:*)` |
| Commands that reach a shared environment | `ask` | `Bash(kubectl:*)` |
| Credential paths beyond the common defaults | `deny` | `Read(./config/secrets/**)` |
| Directories outside the repo that sessions legitimately need | `permissions.additionalDirectories` | `../shared-schemas` |

Prefer allowing the specific commands the workflow needs over a blanket shell
allowance. Anything not listed still works — it just asks first.

## Sandbox

`sandbox.network.allowedDomains` starts with the public package registries.
Add your internal registry, artifact store, and any API the test suite talks
to. `allowUnsandboxedCommands: false` means a blocked command fails loudly
instead of quietly escaping the sandbox — leave it false.

## Hooks

Hooks can live in this same file under a `hooks` key, or in
`.claude/hooks/hooks.json`. See `hooks/README.md` in this directory for the
configuration and what each hook enforces.

## Plugins and skills

To restrict which plugins and skills a session may load, set `enabledPlugins`
(and, per scope, skill settings) in the repo's settings or in your
organization's managed settings, so a session cannot pull in tooling nobody
reviewed. Check the current key names in the settings reference before
writing them — this is the kind of setting most worth getting exactly right.

## Scope

| File | Applies to |
|---|---|
| `.claude/settings.json` | Everyone who clones the repo — commit it |
| `.claude/settings.local.json` | Just you, this repo — git-ignore it |
| Managed settings | Enforced by your organization, overrides the rest |

Decide whether these guardrails are managed centrally or held per-repo, and
record the answer in `CLAUDE.md`.
