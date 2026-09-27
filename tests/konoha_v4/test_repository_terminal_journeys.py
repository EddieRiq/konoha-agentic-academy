"""Separate-process terminal smoke: local fixtures, no real providers/network."""
import json
import os
import re
import selectors
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


# Only the provider/context seams are synthetic. The real CLI, reader, study
# workflow, approval loop and private continuity remain in the child process.
PLANNING_FIXTURE = """
import sys
from types import SimpleNamespace
from unittest import mock
from tools.konoha_v4 import conversation as c, cli
from tools.konoha_v4.models import MissionPlan
from tools.repo_evidence.persistence import evidence_reference
def plan(repo, request, state, registry, **kwargs):
    assert request == 'implement recommendation 1'
    assert state['recommendation_evidence_only']['authorizes_action'] is False
    print('SYNTHETIC_PLANNER: separate supervised mission')
    result = MissionPlan('mission-recommendation-smoke', 'Evaluate the selected recommendation under separate approval',
        [], [], [], 'low', [], ['Human review required'], ['No mutation without separate approval'],
        0, 'low', 'Synthetic provider output for terminal gate verification')
    result.repository_evidence = evidence_reference(kwargs['repo_evidence'])
    return result.seal(), [], 1
with mock.patch.object(c, 'CapabilityRegistry'), \\
     mock.patch.object(c, 'acquire_context', return_value=SimpleNamespace(provider_readiness={}, as_dict=lambda: {})), \\
     mock.patch.object(c, '_build_validated_plan', side_effect=plan), \\
     mock.patch.object(c, '_run_resumable_execution', side_effect=AssertionError('execution forbidden in smoke')):
    raise SystemExit(cli.main(sys.argv[1:]))
"""


class Terminal:
    def __init__(self, test, repo, state, *, planning=False, plan_only=False):
        command = [sys.executable, "-u"]
        command += ["-c", PLANNING_FIXTURE] if planning else ["-m", "tools.konoha_v4.cli"]
        command += ["--repo", str(repo)]
        if plan_only:
            command.append("--plan-only")
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "KONOHA_STATE_ROOT": str(state)})
        test.addCleanup(self.close)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.transcript = ""
        self.read_prompt()

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
        self.selector.close()

    def read_prompt(self):
        output = ""
        deadline = time.monotonic() + 20
        while not output.endswith("Vos> "):
            if time.monotonic() >= deadline:
                raise AssertionError("terminal prompt timed out: " + output)
            if self.selector.select(timeout=0.5):
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise AssertionError("terminal exited before prompt: " + output)
                output += chunk.decode()
        self.transcript += output
        return output

    def send(self, text, *, decision=False):
        suffix = "\n" if decision or text.strip().startswith(":") else "\n:fin\n"
        self.process.stdin.write((text + suffix).encode())
        self.process.stdin.flush()
        return self.read_prompt()

    def exit(self):
        self.process.stdin.write(b"exit\n")
        self.process.stdin.flush()
        output, _ = self.process.communicate(timeout=20)
        self.transcript += output.decode()
        if self.process.returncode != 0:
            raise AssertionError(self.transcript)


class RepositoryTerminalJourneys(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.state = self.base / "state"
        self.repo = self.fixture("target")
        self.donor = self.fixture("donor")

    def fixture(self, name):
        repo = self.base / name
        repo.mkdir()
        (repo / "app.py").write_text("def main(): return 1\n")
        (repo / "orphan.py").write_text("def candidate(): return 2\n")
        (repo / "test_app.py").write_text("import app\n")
        return repo

    def test_live_study_teachback_resume_stale_recommendation_and_donor(self):
        before = {p: p.read_bytes() for root in (self.repo, self.donor) for p in root.iterdir()}
        terminal = Terminal(self, self.repo, self.state)
        output = terminal.send("understand this repository")
        target_id = re.search(r"study-[0-9a-f]{32}", output)[0]
        self.assertIn("Currentness: current", output)
        self.assertIn("awaiting_human", terminal.send("ok"))
        self.assertIn("app.py", terminal.send("explain"))
        self.assertIn("app.py", terminal.send("explain that again"))
        self.assertIn("Test source discovered", terminal.send("explain tests"))
        self.assertIn("awaiting_human", terminal.send(" :entendido"))
        self.assertIn("Teachback: understood", terminal.send(":entendido"))
        self.assertIn("Deterministic finding", terminal.send("what could Konoha improve?"))
        output = terminal.send(f":repo study {self.donor}")
        self.assertIn("No target evidence has been read", output)
        command = re.search(r":repo authorize [0-9a-f]+", output)[0]
        self.assertIn("Authorization pending", terminal.send("yes"))
        output = terminal.send(command)
        donor_id = re.search(r"study-[0-9a-f]{32}", output)[0]
        terminal.send(":entendido")
        comparison = terminal.send("compare this authorized repo with Konoha")
        self.assertIn(target_id, comparison)
        self.assertIn(donor_id, comparison)
        self.assertIn("Candidate lesson", comparison)
        self.assertIn("Evidence digest:", terminal.send("show donor evidence"))
        self.assertIn("Evidence digest:", terminal.send("show Konoha evidence"))
        self.assertIn("Compatibility/risk", terminal.send("what are the compatibility risks?"))
        terminal.exit()
        resumed = Terminal(self, self.repo, self.state)
        self.assertIn(target_id, resumed.send("resume the repository study"))
        self.assertIn("Teachback: understood", resumed.send(f":repo resume {target_id}"))
        self.assertEqual(before, {p: p.read_bytes() for root in (self.repo, self.donor) for p in root.iterdir()})
        packs_before = {p: p.read_bytes() for p in self.state.rglob("repository-evidence-*.json")}
        (self.repo / "app.py").write_text("def changed(): return 4\n")
        self.assertIn("Currentness: stale", resumed.send("resume the repository study"))
        self.assertIn("Currentness: stale", resumed.send("explain Konoha to me"))
        self.assertEqual(packs_before, {p: p.read_bytes() for p in self.state.rglob("repository-evidence-*.json")})
        resumed.exit()
        self.assertFalse((self.state / "missions").exists())
        self.assertFalse((self.state / "context_acquisition.json").exists())

    def test_live_implementation_uses_real_approval_gates_and_plan_only(self):
        for plan_only in (False, True):
            with self.subTest(plan_only=plan_only):
                state = self.base / f"planning-{plan_only}"
                terminal = Terminal(self, self.repo, state, planning=True, plan_only=plan_only)
                terminal.send("understand this repository")
                terminal.send(":entendido")
                terminal.send("what could Konoha improve?")
                output = terminal.send("implement recommendation 1")
                self.assertIn("SYNTHETIC_PLANNER: separate supervised mission", output)
                self.assertIn("New supervised mission", output)
                self.assertIn("pendiente", terminal.send("", decision=True))
                if plan_only:
                    output = terminal.send("sí", decision=True)
                    challenge = re.search(r":aceptar-plan[^\n]+", output)[0]
                    output = terminal.send(challenge, decision=True)
                    self.assertIn("No se autorizó ni ejecutó ninguna tarea", output)
                else:
                    self.assertIn("Plan rechazado", terminal.send("no", decision=True))
                terminal.exit()
                mission = state / "missions" / "mission-recommendation-smoke"
                self.assertFalse((mission / "plan.json").exists())
                continuity = json.loads((mission / "continuity.json").read_text())
                self.assertEqual("implement recommendation 1", continuity["original_request"])
                self.assertFalse(continuity["repo_baseline"]["recommendation_evidence_only"]["authorizes_action"])
                self.assertFalse(continuity["execution"]["started"])


if __name__ == "__main__":
    unittest.main()
