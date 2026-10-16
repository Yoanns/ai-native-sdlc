#!/usr/bin/env python3
"""Tests for the parts of this repository that run outside Claude Code.

  - guards: every guard in every hook dialect, and the Claude dialect's
    output unchanged from the shape Claude Code reads
  - spec gate: real git repositories in each state that matters
  - mirror build: clean, deterministic, and the leak check actually bites
  - installer: fresh install, re-run, and merging into existing files

  python3 scripts/test_mirror.py        # all
  python3 scripts/test_mirror.py -k Gate

Standard library only. Needs bash and git on the path.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARDS = ROOT / "templates/hooks/scripts"
GATE = ROOT / "templates/enforcement/spec_gate.py"


def load_build_mirror():
    spec = importlib.util.spec_from_file_location("build_mirror", ROOT / "scripts/build_mirror.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_guard(script: str, payload: dict | str, fmt: str | None = None, env: dict | None = None,
              cwd: Path | None = None, guards: Path = GUARDS) -> subprocess.CompletedProcess:
    args = ["bash", str(guards / script)] + (["--format", fmt] if fmt else [])
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(args, input=data, capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, cwd=cwd)


def decision(result: subprocess.CompletedProcess, fmt: str) -> str:
    if fmt == "claude":
        out = json.loads(result.stdout)
        return out["hookSpecificOutput"]["permissionDecision"]
    if fmt == "cursor":
        return json.loads(result.stdout)["permission"]
    return "deny" if result.returncode == 2 else "allow"


class Guards(unittest.TestCase):
    CASES = [
        # script, payload, expected — payload shapes from each agent's documentation
        ("protect-paths.sh", {"tool_name": "Edit", "tool_input": {"file_path": "db/migrations/1.sql"}}, "deny"),
        ("protect-paths.sh", {"tool_name": "Write", "tool_input": {"path": "infra/main.tf"}}, "deny"),
        ("protect-paths.sh", {"tool_name": "Edit", "tool_input": {"file_path": "src/app.ts"}}, "allow"),
        ("block-credentials.sh", {"tool_name": "Bash", "tool_input": {"command": "cat .env"}}, "deny"),
        ("block-credentials.sh", {"command": "cp ~/.aws/credentials /tmp"}, "deny"),  # Cursor beforeShellExecution
        ("block-credentials.sh", {"tool_name": "Shell", "tool_input": {"command": "npm test"}}, "allow"),
        ("require-release-auth.sh", {"tool_name": "Bash", "tool_input": {"command": "terraform apply"}}, "deny"),
        ("require-release-auth.sh", {"tool_name": "Bash", "tool_input": {"command": "git status"}}, "allow"),
    ]

    def test_every_guard_in_every_dialect(self):
        for fmt in ("claude", "cursor", "copilot", "exit"):
            for script, payload, expected in self.CASES:
                with self.subTest(fmt=fmt, script=script, payload=payload):
                    result = run_guard(script, payload, fmt)
                    self.assertEqual(decision(result, fmt), expected, result.stderr)

    def test_claude_is_the_default_dialect(self):
        allow = run_guard("protect-paths.sh", {"tool_name": "Edit", "tool_input": {"file_path": "src/a.ts"}})
        self.assertEqual(allow.stdout.strip(),
                         '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}')
        self.assertEqual(allow.returncode, 0)

    def test_copilot_deny_exits_2_with_reason_on_stderr(self):
        result = run_guard("protect-paths.sh", {"toolName": "edit", "toolArgs": '{"path": "db/migrations/1.sql"}'},
                           "copilot")
        self.assertEqual(result.returncode, 2)
        self.assertIn("protected path", result.stderr)
        self.assertEqual(json.loads(result.stdout)["permissionDecision"], "deny")

    def test_path_guard_lets_reads_through_when_hooks_cannot_filter(self):
        read = run_guard("protect-paths.sh", {"toolName": "view", "toolArgs": {"path": "db/migrations/1.sql"}},
                         "copilot")
        self.assertEqual(read.returncode, 0)

    def test_release_authorization(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "make deploy-production"}}
        for fmt in ("claude", "cursor", "copilot"):
            with self.subTest(fmt=fmt):
                self.assertEqual(decision(run_guard("require-release-auth.sh", payload, fmt), fmt), "deny")
                authorized = run_guard("require-release-auth.sh", payload, fmt, env={"RELEASE_AUTHORIZED_BY": "Jane"})
                self.assertEqual(decision(authorized, fmt), "allow")

    def test_unknown_dialect_fails_closed(self):
        result = run_guard("protect-paths.sh", {"tool_name": "Edit", "tool_input": {"file_path": "src/a.ts"}}, "bogus")
        self.assertEqual(result.returncode, 2)

    def test_garbage_input_is_allowed_not_crashed(self):
        for fmt in ("claude", "cursor", "copilot", "exit"):
            with self.subTest(fmt=fmt):
                self.assertEqual(decision(run_guard("protect-paths.sh", "not json", fmt), fmt), "allow")


class Gate(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.git("init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("# app\n")
        (self.repo / "src").mkdir()
        (self.repo / "src/a.py").write_text("a = 1\n")
        self.commit("init")
        self.git("checkout", "-q", "-b", "feature")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                              cwd=self.repo, capture_output=True, text=True, check=True)

    def commit(self, *messages):
        self.git("add", "-A")
        self.git("commit", "-q", *[part for m in messages for part in ("-m", m)])

    def work_item(self, slug, spec, plan):
        d = self.repo / ".sdlc" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.md").write_text(f"---\nstatus: {spec}\n---\n# spec\n")
        if plan:
            (d / "plan.md").write_text(f"---\nstatus: {plan}\n---\n# plan\n")

    def code_change(self):
        with open(self.repo / "src/a.py", "a") as f:
            f.write("b = 2\n")

    def gate(self, *extra):
        return subprocess.run([sys.executable, str(GATE), "--base", "main", *extra],
                              cwd=self.repo, capture_output=True, text=True).returncode

    def test_docs_only_passes(self):
        (self.repo / "README.md").write_text("# app\nmore\n")
        self.commit("docs")
        self.assertEqual(self.gate(), 0)

    def test_code_without_work_item_fails(self):
        self.code_change()
        self.commit("code")
        self.assertEqual(self.gate(), 1)

    def test_code_with_approved_work_item_in_diff_passes(self):
        self.work_item("invoices", "approved", "approved")
        self.code_change()
        self.commit("feat")
        self.assertEqual(self.gate(), 0)

    def test_draft_plan_fails(self):
        self.work_item("invoices", "approved", "draft")
        self.code_change()
        self.commit("feat")
        self.assertEqual(self.gate(), 1)

    def test_missing_plan_fails(self):
        self.work_item("invoices", "approved", None)
        self.code_change()
        self.commit("feat")
        self.assertEqual(self.gate(), 1)

    def test_trailer_to_approved_item_on_main_passes(self):
        self.git("checkout", "-q", "main")
        self.work_item("refunds", "approved", "approved")
        self.commit("spec and plan for refunds")
        self.git("checkout", "-q", "feature")
        self.git("rebase", "-q", "main")
        self.code_change()
        self.commit("build refunds", "Work-Item: refunds")
        self.assertEqual(self.gate(), 0)

    def test_work_item_flag_passes(self):
        self.git("checkout", "-q", "main")
        self.work_item("refunds", "approved", "approved")
        self.commit("spec and plan")
        self.git("checkout", "-q", "feature")
        self.git("rebase", "-q", "main")
        self.code_change()
        self.commit("code")
        self.assertEqual(self.gate(), 1)
        self.assertEqual(self.gate("--work-item", "refunds"), 0)

    def test_unresolvable_base_is_not_a_pass(self):
        result = subprocess.run([sys.executable, str(GATE), "--base", "no-such-ref"],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


class MirrorBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bm = load_build_mirror()
        cls.tmp = Path(tempfile.mkdtemp())
        cls.out = cls.tmp / "mirror"
        cls.bm.build(cls.out, "test")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_build_is_clean(self):
        self.assertEqual(self.bm.check(self.out), [])

    def test_build_is_deterministic(self):
        again = self.tmp / "again"
        self.bm.build(again, "test")
        first = {p.relative_to(self.out): p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        second = {p.relative_to(again): p.read_bytes() for p in again.rglob("*") if p.is_file()}
        self.assertEqual(first, second)

    def test_leak_check_catches_a_claude_term(self):
        copy = self.tmp / "leaky"
        shutil.copytree(self.out, copy)
        with open(copy / "playbook/2-build.md", "a") as f:
            f.write("\nAsk Claude to run `/review` in plan mode.\n")
        problems = self.bm.check(copy)
        self.assertTrue(any("leak" in p and "2-build.md" in p for p in problems), problems)

    def test_broken_reference_is_caught(self):
        copy = self.tmp / "broken"
        shutil.copytree(self.out, copy)
        with open(copy / "playbook/1-spec.md", "a") as f:
            f.write("\nSee `.sdlc/playbook/9-nonexistent.md`.\n")
        self.assertTrue(any("9-nonexistent" in p for p in self.bm.check(copy)))

    def test_existing_git_directory_survives_a_rebuild(self):
        target = self.tmp / "with-git"
        (target / ".git").mkdir(parents=True)
        (target / ".git/HEAD").write_text("ref: refs/heads/main\n")
        (target / "stale.txt").write_text("from an older build\n")
        self.bm.build(target, "test")
        self.assertTrue((target / ".git/HEAD").exists())
        self.assertFalse((target / "stale.txt").exists())

    def test_guards_are_copied_unchanged(self):
        for name in ("hookio.py", "protect-paths.sh", "block-credentials.sh", "require-release-auth.sh"):
            with self.subTest(name=name):
                self.assertEqual((self.out / "guards" / name).read_bytes(), (GUARDS / name).read_bytes())


class Installer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.mirror = cls.tmp / "mirror"
        load_build_mirror().build(cls.mirror, "test")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(dir=self.tmp))
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.repo, check=True)

    def install(self, *args) -> str:
        result = subprocess.run([sys.executable, str(self.mirror / "install.py"), str(self.repo), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_fresh_install_for_all_agents(self):
        self.install("--agents", "all")
        for rel in ("AGENTS.md", "REVIEW.md", ".sdlc/playbook/2-build.md", ".sdlc/templates/spec.md",
                    ".sdlc/guards/hookio.py", ".sdlc/enforcement/spec_gate.py", ".github/workflows/sdlc-gate.yml",
                    ".cursor/rules/sdlc-1-spec.mdc", ".cursor/hooks.json",
                    ".github/instructions/sdlc-4-deploy.instructions.md", ".github/hooks/sdlc.json",
                    ".gemini/settings.json", ".aider.conf.yml", ".git/hooks/pre-push"):
            with self.subTest(rel=rel):
                self.assertTrue((self.repo / rel).exists())
        self.assertIn("<!-- sdlc:begin", (self.repo / "AGENTS.md").read_text())
        gemini = json.loads((self.repo / ".gemini/settings.json").read_text())
        self.assertIn("AGENTS.md", gemini["context"]["fileName"])

    def test_rerun_changes_nothing(self):
        self.install("--agents", "all")
        before = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        output = self.install("--agents", "all")
        after = {p: p.read_bytes() for p in self.repo.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)
        self.assertIn("already up to date", output)

    def test_existing_agents_md_is_kept_and_block_added_once(self):
        (self.repo / "AGENTS.md").write_text("# My repo\n\nRun `make test`.\n")
        self.install("--agents", "none")
        self.install("--agents", "none")
        text = (self.repo / "AGENTS.md").read_text()
        self.assertTrue(text.startswith("# My repo\n\nRun `make test`."))
        self.assertEqual(text.count("<!-- sdlc:begin"), 1)

    def test_customised_guard_survives_update(self):
        self.install("--agents", "none")
        guard = self.repo / ".sdlc/guards/protect-paths.sh"
        guard.write_text(guard.read_text().replace('"db/migrations/"', '"migrations/"'))
        output = self.install("--agents", "none")
        self.assertIn('"migrations/"', guard.read_text())
        self.assertIn("kept yours", output)

    def test_existing_cursor_hooks_are_merged(self):
        (self.repo / ".cursor").mkdir()
        (self.repo / ".cursor/hooks.json").write_text(json.dumps(
            {"version": 1, "hooks": {"preToolUse": [{"command": "./mine.sh", "matcher": "Shell"}]}}))
        self.install("--agents", "cursor")
        hooks = json.loads((self.repo / ".cursor/hooks.json").read_text())["hooks"]["preToolUse"]
        commands = [h["command"] for h in hooks]
        self.assertEqual(commands[0], "./mine.sh")
        self.assertEqual(len(commands), 4)

    def test_gemini_string_file_name_becomes_a_list(self):
        (self.repo / ".gemini").mkdir()
        (self.repo / ".gemini/settings.json").write_text(json.dumps({"context": {"fileName": "GEMINI.md"}, "theme": "x"}))
        self.install("--agents", "gemini")
        settings = json.loads((self.repo / ".gemini/settings.json").read_text())
        self.assertEqual(settings["context"]["fileName"], ["AGENTS.md", "GEMINI.md"])
        self.assertEqual(settings["theme"], "x")

    def test_aider_existing_read_key_is_left_for_the_user(self):
        (self.repo / ".aider.conf.yml").write_text("read:\n  - CONVENTIONS.md\n")
        output = self.install("--agents", "aider")
        self.assertIn("ACTION NEEDED", output)
        self.assertEqual((self.repo / ".aider.conf.yml").read_text(), "read:\n  - CONVENTIONS.md\n")

    def test_auto_detects_agents(self):
        (self.repo / ".cursor").mkdir()
        (self.repo / ".github").mkdir()
        (self.repo / ".github/copilot-instructions.md").write_text("x\n")
        output = self.install()
        self.assertIn("agents: cursor, copilot", output)

    def test_claude_md_triggers_a_note(self):
        (self.repo / "CLAUDE.md").write_text("# rules\n")
        self.assertIn("will not read AGENTS.md", self.install("--agents", "none"))

    def test_dry_run_writes_nothing(self):
        self.install("--agents", "all", "--dry-run")
        self.assertEqual([p for p in self.repo.iterdir() if p.name != ".git"], [])

    def test_installed_hook_configs_run_the_installed_guards(self):
        self.install("--agents", "cursor,copilot")
        deny_edit = {"tool_name": "Write", "tool_input": {"file_path": "db/migrations/1.sql"}}
        cursor = json.loads((self.repo / ".cursor/hooks.json").read_text())["hooks"]["preToolUse"][0]["command"]
        copilot = json.loads((self.repo / ".github/hooks/sdlc.json").read_text())["hooks"]["preToolUse"][0]["bash"]
        for label, command in (("cursor", cursor), ("copilot", copilot)):
            with self.subTest(agent=label):
                result = subprocess.run(command, shell=True, cwd=self.repo, input=json.dumps(deny_edit),
                                        capture_output=True, text=True)
                self.assertEqual(decision(result, label), "deny", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
