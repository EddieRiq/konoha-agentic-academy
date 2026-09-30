"""User journeys through the normal conversation with real synthetic studies."""
import contextlib
import hashlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4 import conversation as cli
from tools.konoha_v4.repository_conversation import RepositoryConversation, _natural_intent
from tools.konoha_v4.terminal_input import TerminalTurnReader
from tools.repo_evidence import workflow as wf


# Frozen dogfood human turns, copied literally (byte-exact, hashes below).
FROZEN_TURNS = (
    "Hola. Acabo de terminar el colegio y no sé nada de Konoha.\nTampoco sé qué significa agente, orquestador, runtime, schema,\nevidence pack o LLM.\n\nMirá este repositorio y explicame, desde cero y con palabras simples:\n\n- qué es Konoha;\n- para qué sirve;\n- qué problema intenta resolver;\n- cómo funciona una tarea desde que yo la pido hasta que termina;\n- qué partes principales tiene;\n- qué cosas puede hacer;\n- qué cosas NO puede hacer por su cuenta;\n- qué cosas siempre necesitan mi permiso.\n\nSi necesitás usar una palabra técnica, explicala en una frase simple.\n\nAl final dame un ejemplo concreto de una tarea real,\npaso por paso.\n\nNo supongas que conozco el proyecto.",
    "Todavía no entendí bien la diferencia entre planear algo\ny tener permiso para hacerlo. Explicámelo de otra manera.",
    "Mostrame de dónde sacaste las afirmaciones más importantes.",
    "ok, gracias",
    ":entendido",
)
FROZEN_SHA256 = (
    "622d6f9b194767a8d5a12c9134249b5d23671b77a53b2f7bfbd4ff74a5efd7a2",
    "81bdf5a2c5e9a1d205eb9ba4132bb8c3e0f864f0dadb3e99cf667a3ed0fd03fa",
    "460b196840b7989ba7c164fff3c46a0ff24d95e093130d90219604792cad93c2",
    "0a78faa1ff5909e8ba384d6d3744fd458a9c15c3d0e88674fa502213e1ecfcdf",
    "83881d461cec31b78c589d6224194f5397c3b4728dfd2d55c9800da95d00973b",
)
# Synthetic README with purpose, flow, roles and limits under another name, so
# the explanation must come from retained evidence rather than known Konoha text.
SUPERVISED_README = """# Lantern Toolkit

**Lantern is a local-first, terminal-first framework for supervised AI missions.**

It coordinates agents and models. Lantern does not replace human authority: it proposes a plan and requests approval.

## What Lantern does

- Starts from a single terminal entry point.
- Produces a plan before execution.
- Paints the sky purple.

## What Lantern does not do

- It does not execute autonomously.
- It does not self-approve.

## Mission flow

```text
Request
  -> Plan proposal
  -> Human approval
  -> Bounded execution
  -> Review
```

## Roles

- **Human user:** final approval authority.
- **Coordinator:** interprets intent and coordinates; does not execute.

Command proposals are not permission.
Recommendations remain proposals, not permission.
Understanding grants no execution approval.
"""


class RepositoryConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.fixture("target")
        self.donor = self.fixture("donor")
        self.state = self.base / "state"
        self.output = io.StringIO()
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)

    def fixture(self, name):
        repo = self.base / name
        repo.mkdir()
        (repo / "app.py").write_text("def main(): return 1\ndef unused(): return 2\n")
        (repo / "test_app.py").write_text("import app\n")
        (repo / "orphan.py").write_text("def unused(): return 2\n")
        (repo / "README.md").write_text("# Synthetic application\nA small local test application.\n")
        (repo / "private").mkdir()
        (repo / "private" / "hidden.py").write_text("PRIVATE_FIXTURE_SENTINEL = 1\n")
        return repo

    def turn(self, text):
        result = self.ui.handle(text)
        self.assertTrue(result.handled)
        return result

    def start(self):
        self.turn("understand this repository")
        return self.ui.active.study_id

    def test_self_study_explanation_evidence_and_no_workspace_mutation(self):
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        identity = self.start()
        self.turn("explain")
        self.turn("show me the evidence")
        rendered = self.output.getvalue()
        for value in (identity, "Currentness: current", "Repository identity:", "Evidence pack:", "app.py", "Static evidence only"):
            self.assertIn(value, rendered)
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", rendered)
        self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_teachback_exact_human_command_only(self):
        self.start()
        for text in ("ok", "yes", "understood", "thanks", "explain that again", "what does this component do?", " :entendido", ":ENTENDIDO", ":entendido "):
            self.turn(text)
            record, _, _ = self.ui.active.load()
            self.assertEqual("awaiting_human", record["teachback"]["status"])
        self.turn(":entendido")
        record, _, _ = self.ui.active.load()
        self.assertTrue(record["teachback"]["completed_by_user"])
        self.assertFalse((self.state / "missions").exists())

    def test_resume_preserves_identity_and_stale_stops_without_acquisition(self):
        identity = self.start()
        self.turn(":entendido")
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
        with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("silent refresh")):
            self.turn(f":repo resume {identity}")
            self.assertEqual(identity, self.ui.active.study_id)
            self.assertEqual("understood", self.ui.active.load()[0]["teachback"]["status"])
            (self.repo / "app.py").write_text("def changed(): return 3\n")
            self.turn("resume the repository study")
            self.turn("show me the evidence")
            self.turn("explain Konoha to me")
        self.assertIn("stale", self.output.getvalue())
        self.assertIn("new study", self.output.getvalue())

    def test_external_authorization_precedes_target_read(self):
        with mock.patch.object(wf, "start_study", wraps=wf.start_study) as start:
            self.turn(f"study this authorized local repository {self.donor}")
            start.assert_not_called()
            self.turn("yes")
            start.assert_not_called()
            command = self.ui.authorization_command
            self.turn(command.upper())
            start.assert_not_called()
            self.turn(command)
            start.assert_called_once()
        self.assertEqual(self.donor, self.ui.active.repo)
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", self.output.getvalue())

    def test_recommendations_and_model_suggestions_remain_distinct(self):
        self.start()
        self.turn("what could Konoha improve?")
        self.assertIn("requires_human_entendido", self.output.getvalue())
        self.turn(":entendido")
        original = wf.recommend_study
        ref = self.ui.active.load()[1].facts[0]["evidence_ref"]
        suggestions = [{"recommendation": "Investigate structure", "risk": "Unknown runtime use", "scope": "One module", "evidence_refs": [ref]},
                       {"recommendation": "SUPPRESSED_CONTENT", "evidence_refs": ["invented"]}]
        with mock.patch.object(wf, "recommend_study", side_effect=lambda *args: original(*args, model_suggestions=suggestions)):
            self.turn("what could Konoha improve?")
        rendered = self.output.getvalue()
        for value in ("Deterministic finding", "Model suggestion", "locator_linkage_only_not_deterministic_truth", "Suppressed", "Risk:", "Scope:", "Recommendation is not permission"):
            self.assertIn(value, rendered)
        self.assertNotIn("SUPPRESSED_CONTENT", rendered)

    def test_donor_requires_both_teachbacks_and_preserves_provenance(self):
        target_id = self.start()
        self.turn(f":repo study {self.donor}")
        self.turn(self.ui.authorization_command)
        donor_id = self.ui.active.study_id
        self.turn("compare this authorized repo with Konoha")
        self.assertIn("requires_human_entendido", self.output.getvalue())
        self.turn(":entendido")
        self.turn("compare this authorized repo with Konoha")
        self.assertIsNone(self.ui.report)
        self.turn(f":repo resume {target_id}")
        self.turn(":entendido")
        self.turn(f":repo resume {donor_id} {self.donor}")
        self.turn("compare this authorized repo with Konoha")
        self.turn("show donor evidence")
        self.turn("show Konoha evidence")
        self.turn("what are the compatibility risks?")
        rendered = self.output.getvalue()
        for value in (target_id, donor_id, "Observed donor fact", "Konoha comparison", "Candidate lesson", "Compatibility/risk", "Recommendation is not permission"):
            self.assertIn(value, rendered)
        self.assertFalse(self.ui.report["authorizes_action"])

    def test_implement_recommendation_returns_planning_evidence_only(self):
        self.start()
        self.turn(":entendido")
        self.turn("what could Konoha improve?")
        result = self.turn("implement recommendation 1")
        self.assertIsNotNone(result.planning_evidence)
        self.assertFalse(result.planning_evidence["authorizes_action"])
        self.assertFalse((self.state / "missions").exists())

    def test_implementation_enters_existing_approval_path_with_exact_human_request(self):
        for plan_only in (False, True):
            with self.subTest(plan_only=plan_only):
                turns = ["understand this repository", ":entendido", "what could Konoha improve?", "implement recommendation 1", "exit"]
                acquired = SimpleNamespace(provider_readiness={}, as_dict=lambda: {})
                plan = mock.Mock()
                with mock.patch.object(cli, "default_state_root", return_value=self.state), \
                     mock.patch.object(cli, "_read_turn", side_effect=turns), \
                     mock.patch.object(cli, "CapabilityRegistry"), \
                     mock.patch.object(cli, "acquire_context", return_value=acquired), \
                     mock.patch.object(cli, "_build_validated_plan", return_value=(plan, [], 1)) as build, \
                     mock.patch.object(cli, "_approval_loop", return_value=None) as approval, \
                     mock.patch.object(cli, "_run_resumable_execution") as execute, contextlib.redirect_stdout(self.output):
                    self.assertEqual(0, cli.run(self.repo, plan_only=plan_only))
                build.assert_called_once()
                args = build.call_args.args
                self.assertEqual("implement recommendation 1", args[1])
                self.assertFalse(args[2]["recommendation_evidence_only"]["authorizes_action"])
                approval.assert_called_once()
                self.assertEqual(plan_only, approval.call_args.kwargs["plan_only"])
                self.assertIs(plan, approval.call_args.args[3])
                execute.assert_not_called()

    def test_stale_report_cannot_enter_planning(self):
        self.start()
        self.turn(":entendido")
        self.turn("what could Konoha improve?")
        (self.repo / "app.py").write_text("# changed\n")
        with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("refresh")):
            result = self.turn("implement recommendation 1")
        self.assertIsNone(result.planning_evidence)
        self.assertIn("Currentness: stale", self.output.getvalue())

    def test_external_resume_requires_fresh_authorization_in_new_session(self):
        self.turn(f":repo study {self.donor}")
        self.turn(self.ui.authorization_command)
        identity = self.ui.active.study_id
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
        with mock.patch.object(wf, "load_study", wraps=wf.load_study) as load:
            self.turn(f":repo resume {identity} {self.donor}")
            load.assert_not_called()
            self.turn("ok")
            load.assert_not_called()
            self.turn(self.ui.authorization_command)
            self.assertTrue(load.called)
        self.assertEqual(identity, self.ui.active.study_id)

    def test_unsafe_roots_remote_paths_and_public_state_are_refused(self):
        for path in (str(self.repo / "private"), "https://example.org/repo", "../relative"):
            with mock.patch.object(wf, "start_study") as start:
                self.turn(f":repo study {path}")
                start.assert_not_called()
        public_state = self.repo / "public-state"
        self.ui = RepositoryConversation(self.repo, public_state, self.output.write)
        self.turn("understand this repository")
        self.assertIsNone(self.ui.active)
        self.assertFalse(public_state.exists())

    def test_multiline_mission_is_not_intercepted_and_leave_does_not_close(self):
        self.assertFalse(self.ui.handle("understand this repository\nthen prepare a migration plan").handled)
        identity = self.start()
        self.turn(":repo leave")
        self.assertIsNone(self.ui.active)
        self.turn(f":repo resume {identity}")
        self.assertEqual("awaiting_human", self.ui.active.load()[0]["teachback"]["status"])


    def test_main_loop_deterministic_routes_never_invoke_provider_or_executor(self):
        turns = ["understand this repository", "ok", "explain that again", ":entendido", "what could Konoha improve?", "exit"]
        with mock.patch.object(cli, "default_state_root", return_value=self.state), mock.patch.object(cli, "_read_turn", side_effect=turns), \
             mock.patch.object(cli, "acquire_context", side_effect=AssertionError("provider probe")), \
             mock.patch.object(cli, "_build_validated_plan", side_effect=AssertionError("provider planning")), \
             mock.patch.object(cli, "_run_resumable_execution", side_effect=AssertionError("execution")), contextlib.redirect_stdout(self.output):
            self.assertEqual(0, cli.run(self.repo))

    # Short synthetic novice-shaped request; the frozen prompt is FROZEN_TURNS[0].
    NOVICE =("Hola. Soy nuevo y no sé nada de Konoha.\n"
              "No quiero cambiar nada, solo entender.\n"
              "Mirá este repositorio y explicame, desde cero, qué es y cómo funciona.")

    def test_natural_study_requests_use_canonical_study(self):
        self.start()
        canonical = self.ui.active.load()[1].repository_identity
        for text in ("explicame este repositorio", "explicame Konoha", "quiero entender este repositorio",
                     "mirá este repositorio y explicame", "estudiá este repositorio", "qué es Konoha y cómo funciona",
                     "show me evidence for this repository", "mostrame la evidencia del repositorio", self.NOVICE):
            with self.subTest(text=text):
                self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
                with mock.patch.object(wf, "start_study", wraps=wf.start_study) as start:
                    self.turn(text)
                start.assert_called_once()
                self.assertEqual((self.repo, "human"), (start.call_args.args[0], start.call_args.args[1].authorized_by))
                self.assertIs(self.ui.target, self.ui.active)
                self.assertEqual(canonical, self.ui.active.load()[1].repository_identity)

    def test_change_requests_remain_missions_with_or_without_active_study(self):
        missions = ("modificá este repositorio", "arreglá este bug", "agregá una función", "ejecutá los tests",
                    "implementá la recomendación 3", "explicame este repositorio y después arreglá el bug",
                    "quiero que arregles el repositorio", "fix the repository and explain it",
                    "understand this repository\nthen prepare a migration plan", "¿cuál es la capital de Francia?",
                    # A later clause still asks for an action: punctuation, "se" and conjunctions do not negate it.
                    "Explicame este repositorio y quiero que se agregue una función",
                    "Explicame este repositorio, no, arreglá el bug", "Explicame este repositorio y que se ejecute el test",
                    "Explain this repository. What? Run the tests.", "Explain how and run the tests",
                    "No. Arreglá el bug y explicame el repositorio",
                    "Explicame este repositorio.\nNo sé nada. Ejecutá los tests.",
                    # The legacy active "explain <category>" prefix must not bypass the action guard.
                    "explain this repository and fix the bug", "explain tests, then run them")
        for active in (False, True):
            if active:
                self.start()
            for text in missions:
                with self.subTest(text=text, active=active), \
                     mock.patch.object(wf, "respond_to_study", side_effect=AssertionError("captured")), \
                     mock.patch.object(wf, "start_study", side_effect=AssertionError("captured")):
                    self.assertFalse(self.ui.handle(text).handled)
        self.assertEqual(0, self.ui.active.load()[0]["teachback"]["clarification_count"])

    def test_negated_or_descriptive_actions_still_study_with_or_without_active_study(self):
        for text in ("explicame este repositorio sin modificar nada", "explicame este repositorio, sin modificar nada",
                     "no modifiques nada y explicame este repositorio", "explicame cómo se ejecuta este repositorio",
                     "explain this repository without changing anything"):
            for active in (False, True):
                with self.subTest(text=text, active=active):
                    self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
                    if active:
                        self.start()
                    with mock.patch.object(wf, "start_study", wraps=wf.start_study) as start:
                        self.turn(text)
                    self.assertEqual(0 if active else 1, start.call_count)
                    self.assertIs(self.ui.target, self.ui.active)
                    self.assertEqual("awaiting_human", self.ui.active.load()[0]["teachback"]["status"])

    def test_novice_journey_stays_in_study_until_exact_entendido(self):
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        self.turn(self.NOVICE)
        study_id = self.ui.active.study_id
        first = self.output.getvalue()
        self.assertNotIn("This is a static map", first)  # novice view replaces the English fact dump
        for noise in ("Repository identity:", "VCS:", "HEAD:", "Evidence digest:", "Requested study:", "De dónde salen"):
            self.assertNotIn(noise, first)  # opaque identifiers and unrequested evidence dumps
        for value in ("Explicación desde cero: Synthetic application.",
                      "Synthetic application es una herramienta que funciona en tu propia computadora. [README.md:2]",
                      "Su documentación no lo dice con claridad; no lo voy a inventar.",
                      "1) Pedido:", "3) Aprobación humana:", "4) Ejecución acotada:", "5) Revisión:",
                      "(así funciona esta terminal; su documentación no lo menciona)",
                      "plan != permiso", "recomendación != permiso", "entender != permiso",
                      "querés comprobar que pasan las pruebas de test_app.py [test_app.py:1]",
                      "Límites, en simple: el estudio solo leyó archivos; no ejecutó nada"):
            self.assertIn(value, first)
        self.assertLess(first.index("Qué es, en un párrafo"), first.index("Cómo funciona una tarea"))
        for text in ("Todavía no entendí.\n¿Me lo explicás más simple?", "explicámelo de otra manera", "no entendí esa parte"):
            self.turn(text)
        self.assertIn("pedido -> plan propuesto -> tu aprobación", self.output.getvalue())
        self.turn("mostrame de dónde sacaste eso")
        evidence = self.output.getvalue()
        self.assertIn(f"«A small local test application.» [{study_id} / ", evidence)
        self.assertIn(" / README.md:2]", evidence)
        self.assertIn(" / test_app.py:1]", evidence)
        for text in ("ok, gracias", "entendido", "ya entendí", ":entendido.", "Entendido!"):
            self.turn(text)
            self.assertEqual("awaiting_human", self.ui.active.load()[0]["teachback"]["status"])
        self.turn(":entendido")
        record = self.ui.active.load()[0]["teachback"]
        self.assertEqual(("understood", ":entendido", 9), (record["status"], record["human_command"], record["clarification_count"]))
        self.assertIn("not execution approval", record["non_authority"])
        self.assertFalse((self.state / "missions").exists())
        self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", self.output.getvalue())

    def test_frozen_fixture_is_byte_exact(self):
        self.assertEqual(FROZEN_SHA256, tuple(hashlib.sha256(turn.encode()).hexdigest() for turn in FROZEN_TURNS))
        self.assertEqual((21, 2, 1, 1, 1), tuple(len(turn.split("\n")) for turn in FROZEN_TURNS))

    def test_evidence_intent_needs_a_request_not_a_term_mention(self):
        self.assertEqual(("study", "study"), (_natural_intent(FROZEN_TURNS[0], False), _natural_intent(FROZEN_TURNS[0], True)))
        for text in ("¿qué significa evidence pack?", "no sé qué es un evidence pack", "Tampoco sé qué significa\nevidence pack o LLM."):
            self.assertEqual("clarify", _natural_intent(text, True), text)
        for text in (FROZEN_TURNS[2], "mostrame de dónde sacaste eso", "mostrame la evidencia", "show me the sources"):
            self.assertEqual("evidence", _natural_intent(text, True), text)
        self.assertEqual("clarify", _natural_intent(FROZEN_TURNS[1], True))
        self.assertEqual("acknowledge", _natural_intent(FROZEN_TURNS[3], True))

    def frozen_journey(self):
        """The literal frozen turns through the real main loop and terminal reader."""
        (self.repo / "README.md").write_text(SUPERVISED_README)
        stdin = "".join(turn + "\n:fin\n" for turn in FROZEN_TURNS[:-1]) + FROZEN_TURNS[-1] + "\nexit\n"
        reader = TerminalTurnReader(io.StringIO(stdin), self.output)
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        seen = []
        original = RepositoryConversation.handle
        with mock.patch.object(cli, "default_state_root", return_value=self.state), mock.patch.object(cli, "_TERMINAL_INPUT", reader), \
             mock.patch.object(RepositoryConversation, "handle", autospec=True,
                               side_effect=lambda ui, text: seen.append(text) or original(ui, text)), \
             mock.patch.object(wf, "start_study", wraps=wf.start_study) as start, \
             mock.patch.object(cli, "CapabilityRegistry", side_effect=AssertionError("provider registry")), \
             mock.patch.object(cli, "acquire_context", side_effect=AssertionError("provider probe")), \
             mock.patch.object(cli, "_build_validated_plan", side_effect=AssertionError("provider planning")), \
             mock.patch.object(cli, "_run_resumable_execution", side_effect=AssertionError("execution")), \
             contextlib.redirect_stdout(self.output):
            self.assertEqual(0, cli.run(self.repo))
        self.assertEqual(list(FROZEN_TURNS), seen)  # every multiline turn captured whole, byte-exact
        start.assert_called_once()
        self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})
        self.assertFalse((self.state / "missions").exists())
        self.assertFalse((self.state / "context_acquisition.json").exists())
        return self.output.getvalue()

    def test_frozen_novice_journey_explains_from_retained_evidence(self):
        output = self.frozen_journey()
        studies = sorted(p.name for p in (self.state / "repository-studies").glob("study-*"))
        self.assertEqual(1, len(studies))
        study_id = studies[0]
        self.assertEqual({study_id}, set(re.findall(r"study-[0-9a-f]{32}", output)))  # one study throughout
        auth = wf.StudyAuthorization(str(self.repo.resolve()), "human", "Interactive human repository study authorization", True)
        record, study, pack = wf.load_study(self.repo, auth, self.state / "repository-studies", study_id)
        teachback = record["teachback"]
        self.assertEqual(("understood", ":entendido", 3), (teachback["status"], teachback["human_command"], teachback["clarification_count"]))
        self.assertIn("not execution approval or mission closure", teachback["non_authority"])
        first, second, third, fourth, fifth = output.split("Vos> ")[1:6]
        # Plain definition and purpose before any implementation detail, from the retained README.
        definition = ("Lantern es una herramienta que se usa escribiendo órdenes en la terminal (la ventana de texto donde "
                      "se le dan instrucciones a la computadora), funciona en tu propia computadora, coordina asistentes de "
                      "inteligencia artificial (IA: programas que escriben texto o código) y trabaja en tareas siempre bajo "
                      "el control de una persona (su documentación llama «misiones» a esas tareas). [README.md:3] [README.md:5]")
        self.assertIn(definition, first)
        self.assertNotIn("Konoha es", output)  # the subject comes from evidence, not from the prompt
        self.assertLess(first.index("Qué es, en un párrafo"), first.index("Qué encontró el estudio"))
        for opaque in ("Repository identity", "VCS:", "HEAD:", "Evidence digest", "incoming and", "De dónde salen"):
            self.assertNotIn(opaque, first)
        # Every term the human asked about is explained in one sentence.
        for term in ("Agente:", "Orquestador:", "Runtime:", "Schema:", "Evidence pack:", "LLM:"):
            self.assertIn("  - " + term, first)
        for meaning in ("se le asigna una responsabilidad concreta y con límites", "lleva a cabo el proceso supervisado",
                        "Por sí solo no tiene autoridad"):
            self.assertIn(meaning, first)
        # Flow, rules, parts, limits and permissions carry the locators of their retained lines.
        for value in ("1) Pedido: vos escribís lo que querés que se haga. [README.md:21]",
                      "2) Plan: se propone por escrito", "[README.md:22]", "[README.md:23]", "[README.md:24]", "[README.md:25]",
                      "plan != permiso: un plan es una propuesta, no una autorización. [README.md:33]",
                      "recomendación != permiso: una sugerencia de mejora no autoriza hacerla. [README.md:34]",
                      "entender != permiso: :entendido solo cierra este aprendizaje; no aprueba ninguna ejecución. [README.md:35]",
                      "Human user: tiene la última palabra: aprueba o rechaza [README.md:30]",
                      "Coordinator: entiende el pedido y coordina el trabajo; no ejecuta el trabajo [README.md:31]",
                      "se usa con un solo comando desde la terminal [README.md:9]",
                      "escribe un plan antes de ejecutar nada [README.md:10]",
                      "no ejecuta nada por su cuenta [README.md:15]", "no se aprueba a sí mismo [README.md:16]",
                      "no se ejecuta nada hasta que apruebes su plan",
                      "Ejemplo concreto de una tarea real, paso a paso: querés comprobar que pasan las pruebas de test_app.py"):
            self.assertIn(value, first)
        # An unmatched capability is never paraphrased or quoted as unexplained jargon; only its locator is given.
        self.assertIn("y 1 cosa más: no la resumo porque no sé decirla en simple sin inventar", first)
        self.assertIn("está en [README.md:11].", first)
        self.assertNotIn("Paints", output)
        self.assertNotIn("términos técnicos", output)
        self.assertIn("escritos en Python, un lenguaje de programación", first)
        # The plan-versus-permission clarification stays in the study and explains the difference.
        self.assertIn("Planear y tener permiso son dos cosas distintas", second)
        self.assertIn("plan != permiso [README.md:33]", second)
        # The evidence request quotes the retained lines with full provenance.
        pack_id = study.evidence_reference["pack_id"]
        refs = {(c["path"], c["line"]): c["evidence_ref"] for c in pack.doc_claims}
        for line, text in ((3, "**Lantern is a local-first, terminal-first framework for supervised AI missions.**"),
                           (33, "Command proposals are not permission."), (15, "- It does not execute autonomously.")):
            ref = refs[("README.md", line)]
            self.assertEqual(("README.md", line), (pack.provenance_index[ref]["path"], pack.provenance_index[ref]["line_start"]))
            self.assertIn(f"«{text}» [{study_id} / {pack_id} / {ref} / README.md:{line}]", third)
        self.assertIn("Otra línea de esas listas: no la resumo porque", third)
        self.assertIn("[README.md:11].", third)
        # Acknowledgement leaves teachback open; only exact :entendido closes it, without authority.
        self.assertIn("Teachback: awaiting_human", fourth)
        self.assertIn("Teachback: understood. Repository understanding is not execution approval or mission closure.", fifth)
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", output)

    def test_novice_explanation_follows_changed_evidence(self):
        readmes = {"Orbit": "# Orbit\n\nOrbit is a command-line tool for local backups.\n", "sparse": "# Notes\n\nhello\n", "none": None}
        for name, text in readmes.items():
            with self.subTest(readme=name):
                repo = self.fixture(f"changed-{name}")
                if text is None:
                    (repo / "README.md").unlink()
                else:
                    (repo / "README.md").write_text(text)
                output = io.StringIO()
                ui = RepositoryConversation(repo, self.base / f"state-{name}", output.write)
                self.assertTrue(ui.handle("explicame este repositorio").handled)
                self.assertTrue(ui.handle("mostrame de dónde sacaste eso").handled)
                rendered = output.getvalue()
                for foreign in ("Konoha", "Lantern", "inteligencia artificial", "Hokage", "misiones", "Human user",
                                "no ejecuta nada por su cuenta", "Una IA que actúa sola"):
                    self.assertNotIn(foreign, rendered)
                self.assertIn("Su documentación no lo dice con claridad; no lo voy a inventar.", rendered)
                self.assertIn("(así funciona esta terminal; su documentación no lo menciona)", rendered)
                if name == "Orbit":
                    self.assertIn("Orbit es una herramienta que se usa escribiendo órdenes en la terminal (la ventana de texto "
                                  "donde se le dan instrucciones a la computadora) y funciona en tu propia computadora. [README.md:3]",
                                  rendered)
                    self.assertIn("«Orbit is a command-line tool for local backups.» [study-", rendered)
                else:
                    self.assertIn("Explicación desde cero: " + ("Notes." if name == "sparse" else "Este proyecto."), rendered)
                    self.assertIn("No encontré un README con una descripción", rendered)

    def test_only_root_readme_prose_is_retained_as_evidence(self):
        nested = ("docs/README.md", "examples/README.md", "package/subdir/README.md")
        for rel in nested:
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text("# Nested\n\nNested ordinary prose line.\nRun `tool check` first.\nUse tool --verbose.\n")
        study_id = self.start()
        auth = wf.StudyAuthorization(str(self.repo.resolve()), "human", "Interactive human repository study authorization", True)
        _, _, pack = wf.load_study(self.repo, auth, self.state / "repository-studies", study_id)
        claims = {(c["path"], c["line"]): c for c in pack.doc_claims}
        with self.subTest("root README ordinary prose retained"):
            claim = claims[("README.md", 2)]
            self.assertEqual("A small local test application.", claim["statement"])
            provenance = pack.provenance_index[claim["evidence_ref"]]
            self.assertEqual(("README.md", 2, 2), (provenance["path"], provenance["line_start"], provenance["line_end"]))
            self.assertEqual(hashlib.sha256((self.repo / "README.md").read_bytes()).hexdigest(), provenance["content_sha256"])
        for rel in nested:
            with self.subTest("nested README ordinary prose not retained by basename", path=rel):
                self.assertNotIn((rel, 1), claims)
                self.assertNotIn((rel, 3), claims)
            with self.subTest("nested README backtick and double-hyphen lines retained", path=rel):
                self.assertEqual("Run `tool check` first.", claims[(rel, 4)]["statement"])
                self.assertEqual("Use tool --verbose.", claims[(rel, 5)]["statement"])
                for line in (4, 5):
                    provenance = pack.provenance_index[claims[(rel, line)]["evidence_ref"]]
                    self.assertEqual((rel, line), (provenance["path"], provenance["line_start"]))

    def test_negated_evidence_never_becomes_a_positive_claim(self):
        repo = self.fixture("negated")
        (repo / "README.md").write_text(
            "# Maple\n\nMaple is not a supervised AI framework and does not coordinate agents.\n"
            "It is a static archive of notes; no software runs here.\n\n"
            "## What Maple does\n\n- Does not inspect CPU or RAM.\n- Stores notes.\n\n"
            "## Roles\n\n- **Keeper:** reviews independently; does not approve its own work.\n")
        output = io.StringIO()
        ui = RepositoryConversation(repo, self.base / "state-negated", output.write)
        self.assertTrue(ui.handle("explicame este repositorio").handled)
        self.assertTrue(ui.handle("mostrame de dónde sacaste eso").handled)
        rendered = output.getvalue()
        for fabricated in ("Maple es una herramienta", "Maple es un proyecto", "coordina asistentes",
                           "bajo el control de una persona", "Una IA que actúa sola", "revisa qué recursos tiene tu computadora",
                           "no aprueba ni da permiso"):
            self.assertNotIn(fabricated, rendered)
        self.assertIn("no puedo simplificar sin inventar", rendered)
        self.assertIn("Su documentación no lo dice con claridad; no lo voy a inventar.", rendered)
        # The self-approval limit keeps its exact meaning; independent review is not turned into "cannot approve".
        self.assertIn("Keeper: revisa el trabajo de otros; no aprueba su propio trabajo [README.md:13]", rendered)
        self.assertIn("«Maple is not a supervised AI framework and does not coordinate agents.» [study-", rendered)
        # A negated line outside its section is neither paraphrased nor quoted unexplained; only located.
        self.assertNotIn("Does not inspect CPU or RAM", rendered)
        self.assertIn("Otras líneas de esas listas: no las resumo porque no sé decirlas en simple sin inventar", rendered)

    def test_natural_acknowledgement_is_not_external_authorization(self):
        self.start()
        self.turn(f":repo study {self.donor}")
        with mock.patch.object(wf, "start_study", side_effect=AssertionError("authorized")):
            self.turn("ok, gracias")
        self.assertIn("Authorization pending", self.output.getvalue())
        self.assertIsNotNone(self.ui.pending)

    def test_main_loop_novice_journey_never_invokes_provider_or_executor(self):
        turns = [self.NOVICE, "no entendí esa parte", "mostrame de dónde sacaste eso", "ok, gracias", ":entendido", "exit"]
        with mock.patch.object(cli, "default_state_root", return_value=self.state), mock.patch.object(cli, "_read_turn", side_effect=turns), \
             mock.patch.object(cli, "acquire_context", side_effect=AssertionError("provider probe")), \
             mock.patch.object(cli, "_build_validated_plan", side_effect=AssertionError("provider planning")), \
             mock.patch.object(cli, "_run_resumable_execution", side_effect=AssertionError("execution")), contextlib.redirect_stdout(self.output):
            self.assertEqual(0, cli.run(self.repo))
        self.assertIn("Teachback: understood", self.output.getvalue())
        self.assertFalse((self.state / "context_acquisition.json").exists())

    def test_exact_command_whitespace_survives_terminal_reader(self):
        for text in (":entendido", " :entendido", ":entendido ", ":ENTENDIDO"):
            reader = TerminalTurnReader(io.StringIO(text + "\n"), self.output)
            with mock.patch.object(cli, "_TERMINAL_INPUT", reader):
                self.assertEqual(text, cli._read_turn())


if __name__ == "__main__":
    unittest.main()
