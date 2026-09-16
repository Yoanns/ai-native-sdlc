# Changelog

All notable changes to this plugin are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-09-16

First public release.

### Added

- Five stage skills — `sdlc-design-spec`, `sdlc-build-plan`,
  `sdlc-test-verify`, `sdlc-deploy-review`, `sdlc-maintain-monitor` — each
  producing one committed artifact and stopping at its gate.
- `sdlc-orchestrator`, which routes a work item to the right stage from the
  artifacts on disk and refuses to skip a gate.
- `sdlc-setup-guardrails`, a once-per-repository installer for `CLAUDE.md`,
  `REVIEW.md`, hooks, settings and the eval scaffold.
- Three review-pass subagents — bugs and logic, security, spec conformance —
  run in parallel by Stage 4.
- Guardrail templates: artifact shapes, `CLAUDE.md`, `REVIEW.md`, hook
  configuration with four scripts, settings, a metric watcher, and three eval
  cases in `claude plugin eval` format.
- An eval suite for the plugin itself, covering stage routing and the
  no-self-approval rule.
- `scripts/validate.py`, checking every file against its documented schema,
  run in CI on each push.

### Changed from the upstream playbook

- The intake stage is absent. A request that arrives is a request that gets
  built, so `intent.md` is not a separate gated artifact; its substance is the
  opening sections of `spec.md`. See `CUSTOMIZE.md` to restore it.

### Fixed before release

Four format defects found by checking every file against the Claude Code
documentation rather than against assumption:

- Agent frontmatter was invalid YAML — `<example>` blocks at column zero broke
  the parser, so none of the three agents would have loaded. Now literal block
  scalars.
- Hook scripts emitted `{"decision": "block"}`, which the runtime does not
  read. Now `hookSpecificOutput.permissionDecision` with a reason, verified by
  executing each script against sample payloads.
- `settings.json` used an invented `sandbox.network.allowlist` key and carried
  placeholder permission rules that would have been silently skipped. Now real
  keys only, with the open decisions moved to `templates/SETTINGS.md`.
- The eval suite used a hand-rolled format with an unimplemented runner.
  Replaced with the documented case-directory format and `claude plugin eval`.

[1.0.0]: https://github.com/yoanns/ai-native-sdlc/releases/tag/v1.0.0
