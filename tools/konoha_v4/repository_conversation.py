"""Terminal routing/presentation over the existing repository workflow.

No provider calls, independent study engine, or execution authority lives here.
Durable state is exclusively the workflow's existing private study records.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.repo_evidence import workflow as wf
from tools.repo_evidence.acquire_repo_evidence import _is_private_or_excluded
from tools.repo_evidence.study import explain_repository_study


HELP = """Repository study (no provider or application execution):
  understand this repository / explain Konoha to me
  :repo study /absolute/local/checkout
  :repo list | :repo resume STUDY_ID [ /absolute/local/checkout ]
  explain / explain that again / explain tests / explain components
  show me the evidence / what could Konoha improve?
  compare this authorized repo with Konoha / what could we learn from it?
  show donor evidence / show Konoha evidence / what are the compatibility risks?
  :repo details / implement recommendation NUMBER
  :repo leave (leave the study view without closing understanding)
Natural-language turns use the existing :fin terminator; :repo commands and
the exact human :entendido are single lines. Only :entendido closes repository
understanding; it grants no execution approval or mission closure.
External checkouts require a separate exact public-repository authorization.
Study state stays private under KONOHA_STATE_ROOT/repository-studies.
"""


def _safe_text(value: object) -> str:
    # Repository statements and paths are untrusted terminal text, not controls.
    return "".join(c if c in "\n\t" or c.isprintable() else "?" for c in str(value))


@dataclass(frozen=True)
class StudySession:
    repo: Path
    authorization: wf.StudyAuthorization
    state_root: Path
    study_id: str

    def load(self):
        return wf.load_study(self.repo, self.authorization, self.state_root, self.study_id)


@dataclass(frozen=True)
class RepositoryTurn:
    handled: bool
    planning_evidence: dict | None = None


class RepositoryConversation:
    def __init__(self, repo: Path, state_root: Path, output: Callable[[str], object] | None = None):
        self.repo = repo.resolve()
        self.state_root = state_root / "repository-studies"
        self.output = output or (lambda message: print(message, end=""))
        self.active: StudySession | None = None
        self.target: StudySession | None = None
        self.sessions: dict[str, StudySession] = {}
        self.pending: tuple[Path, str | None] | None = None
        self.authorization_command: str | None = None
        self.report: dict | None = None
        self.report_sessions: list[StudySession] = []

    def say(self, message: object):
        self.output(_safe_text(message) + "\n")

    def _clear_report(self):
        self.report = None
        self.report_sessions = []

    def _activate(self, session: StudySession):
        self.say(f"Requested study: {session.study_id}")
        session.load()  # validate before remembering a session or displaying facts
        self.active = session
        self.sessions[session.study_id] = session
        if session.repo == self.repo:
            self.target = session
        self._clear_report()
        self._explain()

    def _request_study(self, path: str | None = None, study_id: str | None = None):
        # Do not stat, resolve symlinks, or inspect an external target before the
        # human answers the exact challenge. Merely naming a path is not consent.
        if path and ("://" in path or not Path(path).is_absolute()):
            raise ValueError("absolute_local_checkout_required_no_remote_acquisition")
        repo = Path(path) if path else self.repo
        if _is_private_or_excluded(repo.as_posix(), ()):
            raise ValueError("private_or_excluded_repository_root_refused")
        self.pending = None
        self.authorization_command = None
        if repo == self.repo:
            self._open(repo, study_id)
        elif study_id in self.sessions and self.sessions[study_id].repo == repo:
            self._activate(self.sessions[study_id])
        else:
            self.pending = (repo, study_id)
            self.authorization_command = ":repo authorize " + secrets.token_hex(8)
            self.say(f"Target requested: {repo}\nNo target evidence has been read. Confirm that this is an authorized PUBLIC local checkout.\n"
                     "This permits bounded static study and private study-state storage only; private/ignored paths stay excluded.\n"
                     f"Enter exactly: {self.authorization_command}\nUse :repo cancel to cancel. Ordinary yes/ok is not authorization.")

    def _open(self, repo: Path, study_id: str | None):
        repo = repo.resolve()
        if _is_private_or_excluded(repo.as_posix(), ()):
            raise ValueError("private_or_excluded_repository_root_refused")
        wf._check_state_location(self.repo, self.state_root)
        if study_id:
            # Explicit reentry reads only the selected workflow record. Retained
            # authorization supplies identity, never fresh external permission.
            record = wf._read_state(wf._session_dir(self.state_root, study_id) / "study.json")
            auth = wf.StudyAuthorization(**record["authorization"])
            if auth.authorized_repo_root != str(repo):
                raise ValueError("study_target_mismatch_supply_explicit_local_path_for_external_resume")
        else:
            auth = wf.StudyAuthorization(str(repo), "human", "Interactive human repository study authorization", True)
            record = wf.start_study(repo, auth, self.state_root)
            study_id = record["study"]["study_id"]
        self._activate(StudySession(repo, auth, self.state_root, study_id))

    def _required(self) -> StudySession:
        if self.active is None:
            raise ValueError("no_active_study_use_understand_this_repository_or_repo_resume")
        return self.active

    def _explain(self, category: str | None = None, *, session: StudySession | None = None, evidence: bool = False):
        session = session or self._required()
        record, study, _ = session.load()
        identity = study.repository_identity
        self.say(f"Repository identity: {identity['repo_root_id']} | VCS: {identity['vcs']} | HEAD: {identity['head']}\n"
                 f"Currentness: current | Teachback: {record['teachback']['status']}")
        if evidence:
            self.say(f"Study: {study.study_id}\nEvidence pack: {study.evidence_reference['pack_id']}\n"
                     f"Evidence digest: {study.evidence_reference['sha256']}")
            for fact in study.facts:
                self.say(f"{fact['category']}: {fact['observation']} [{self._locator({'study_id': study.study_id, 'evidence_reference': study.evidence_reference, 'locator': fact['locator'], 'evidence_ref': fact['evidence_ref']})}]")
            self.say("Bounded evidence only. " + " ".join(study.limitations))
        else:
            self.say(explain_repository_study(study, category))
        self.say("Next: explain <category>, show me the evidence, :entendido, :repo resume, :repo help.")

    def _list(self):
        # List opaque IDs only. No bulk raw private state or external paths.
        ids = sorted(p.name for p in self.state_root.glob("study-*")
                     if re.fullmatch(r"study-[0-9a-f]{32}", p.name) and not p.is_symlink())
        self.say("Saved local studies (currentness unverified until resume):\n" +
                 ("\n".join(ids[:50]) if ids else "No saved studies.") +
                 "\nResume with :repo resume STUDY_ID [ /absolute/local/checkout ].")
        if len(ids) > 50:
            self.say("List limited to 50 IDs; resume another known ID explicitly.")

    @staticmethod
    def _locator(provenance: dict) -> str:
        loc = provenance.get("locator", {})
        return (f"{provenance['study_id']} / {provenance['evidence_reference']['pack_id']} / "
                f"{provenance.get('evidence_ref', 'bounded-study')} / "
                f"{loc.get('path', 'no included locator')}:{loc.get('line_start', '?')}")

    def _recommend(self):
        session = self.target
        if session is None:
            raise ValueError("study_current_repository_first_before_Konoha_recommendations")
        self._clear_report()
        self.report = wf.recommend_study(session.repo, session.authorization, session.state_root, session.study_id)
        self.report_sessions = [session]
        self._render_report()

    def _compare(self):
        donor = self._required()
        if self.target is None:
            raise ValueError("study_and_close_teachback_for_current_repository_then_resume_donor")
        target = self.target
        self._clear_report()
        self.report = wf.compare_studies(donor.repo, donor.authorization, donor.state_root, donor.study_id,
                                         target.repo, target.authorization, target.state_root, target.study_id)
        self.report_sessions = [donor, target]
        self._render_report()

    def _report_items(self) -> list[dict]:
        if self.report is None:
            raise ValueError("request_recommendations_or_comparison_first")
        for session in self.report_sessions:
            session.load()  # stale cached suggestions may never become planning input
        if "recommendations" in self.report:
            return self.report["recommendations"]
        return self.report["validated"] + self.report["model_suggestions"]

    def _render_report(self, details: bool = False):
        items = self._report_items()
        self.say(self.report["non_authority"])
        self.say(f"Recommendations: {len(items)}; proposed only; authorizes_action=false.")
        for number, item in enumerate(items if details else items[:3], 1):
            if "observed_donor_fact" in item:
                comparison = item["comparison_with_target"]
                self.say(f"{number}. Observed donor fact: {item['observed_donor_fact']}\n"
                         f"Donor provenance: {self._locator(item['provenance'])}\n"
                         f"Konoha comparison: {comparison['observation']}\n"
                         f"Konoha provenance: {self._locator(comparison['provenance'])}\n"
                         f"Candidate lesson: {item['candidate_lesson']}\n"
                         f"Compatibility/risk: {item['compatibility_and_risk']}")
            else:
                model = item["basis"] == "model_suggestion"
                self.say(f"{number}. {'Model suggestion' if model else 'Deterministic finding'}: {item.get('observation', item['recommendation'])}\n"
                         f"Validation: {item['validation']}\nRisk: {item['risk']}\nScope: {item['scope']}")
                refs = item["provenance"] if model else [item["provenance"]]
                for ref in refs:
                    self.say("Provenance: " + self._locator(ref))
            self.say("Recommendation: " + item["recommendation"])
        for item in self.report.get("suppressed", []):
            self.say("Suppressed suggestion: " + item["reason"])
        if "model_suggestions" in self.report:
            self.say(f"Model suggestions: {len(self.report['model_suggestions'])}; locator validation only, not deterministic truth. No model was invoked by this route.")
        for limitation in self.report.get("limitations", []):
            self.say("Known limitation: " + limitation)
        if len(items) > 3 and not details:
            self.say("Showing first 3; :repo details shows all bounded recommendations.")
        self.say("Implement recommendation NUMBER starts a separate supervised mission with fresh planning/approval/review gates.")

    def handle(self, text: str) -> RepositoryTurn:
        # A multiline mission is never intercepted by a keyword inside it.
        if "\n" in text:
            return RepositoryTurn(False)
        key = text.strip().casefold().rstrip("?")
        try:
            return self._handle(text, key)
        except (wf.RepositoryEvidenceError, wf.TeachbackError, ValueError, OSError, KeyError, TypeError) as exc:
            # No raw exception paths/content from private state reach the screen.
            reason = str(exc)
            if not re.fullmatch(r"[a-zA-Z0-9_]+", reason):
                reason = "study_state_or_input_invalid"
            self.say(f"Repository study stopped: {reason}.")
            if "stale" in reason:
                self.say("Currentness: stale. Retained evidence was not refreshed. Explicit next action: start a new study with :repo study [ /absolute/local/checkout ]; replan any affected mission separately.")
            return RepositoryTurn(True)

    def _handle(self, text: str, key: str) -> RepositoryTurn:
        if text == self.authorization_command and self.pending is not None:
            repo, study_id = self.pending
            self.pending = None
            self.authorization_command = None
            self._open(repo, study_id)
        elif key.startswith(":repo authorize") or self.pending and key in {"ok", "yes", "si", "sí", "understood", "thanks"}:
            self.say("Authorization pending; use the exact displayed :repo authorize command or :repo cancel.")
        elif key == ":repo cancel":
            self.pending = None
            self.authorization_command = None
            self.say("Pending repository authorization cancelled; no target evidence acquired.")
        elif key == ":repo help":
            self.say(HELP)
        elif key in {"understand this repository", "understand current repository", "understand konoha", "explain konoha to me"}:
            if self.target:
                self._activate(self.target)
            else:
                self._request_study()
        elif key == ":repo study":
            self._request_study()
        elif text.startswith(":repo study "):
            self._request_study(text[len(":repo study "):])
        elif key.startswith("study this authorized local repository "):
            self._request_study(text[len("study this authorized local repository "):])
        elif key in {"study this authorized local repository", "study this repository"}:
            self.say("Use :repo study for the current repository, or :repo study /absolute/local/checkout for an external target requiring explicit authorization.")
        elif key == ":repo list":
            self._list()
        elif key in {"resume the repository study", ":repo resume"}:
            if self.active:
                self._explain()
            else:
                self._list()
        elif text.startswith(":repo resume "):
            parts = text[len(":repo resume "):].split(maxsplit=1)
            self._request_study(parts[1] if len(parts) == 2 else None, parts[0])
        elif key == ":repo leave":
            self.active = None
            self.pending = None
            self.authorization_command = None
            self._clear_report()
            self.say("Study view left; repository understanding was not closed. Saved studies remain resumable.")
        elif key == ":entendido" or self.active and key in {"ok", "yes", "understood", "thanks", "si", "sí", "gracias"}:
            session = self._required()
            record = wf.respond_to_study(session.repo, session.authorization, session.state_root, session.study_id, text, actor="human")
            self.say(f"Teachback: {record['teachback']['status']}. {record['teachback']['non_authority']}\n"
                     "Repeat/clarify remains available. Only exact :entendido closes repository understanding.")
        elif key in {"explain", "explain that again", "repeat", "show me the evidence", ":repo evidence", "what does this component do"} or key.startswith("explain ") and self.active:
            category = None
            if key == "what does this component do":
                category = "components"
            elif key.startswith("explain ") and key != "explain that again":
                category = key[len("explain "):]
            session = self._required()
            wf.respond_to_study(session.repo, session.authorization, session.state_root, session.study_id, text, actor="human")
            self._explain(category, evidence=key in {"show me the evidence", ":repo evidence"})
        elif key.startswith("what does ") and key.endswith(" do") and self.active:
            self.say("Included component evidence follows. Static imports do not establish runtime behavior; use explain <category> for clarification.")
            self._explain("components")
        elif key in {"what could konoha improve", ":repo recommend"}:
            self._recommend()
        elif key in {"compare this authorized repo with konoha", "compare konoha with this authorized repository", "what could we learn from it", "what can konoha learn from it", ":repo compare"}:
            self._compare()
        elif key in {"show donor evidence", "show konoha evidence"}:
            self._report_items()
            if len(self.report_sessions) != 2:
                raise ValueError("request_donor_comparison_first")
            self._explain(session=self.report_sessions[0 if key == "show donor evidence" else 1], evidence=True)
        elif key in {":repo details", "what are the compatibility risks"}:
            self._render_report(details=True)
        elif re.fullmatch(r"(?:i want to )?implement (?:the |this )?recommendation(?: [0-9]+)?", key):
            items = self._report_items()
            if not key.rsplit(" ", 1)[-1].isdigit():
                self.say("Select an explicit recommendation number: implement recommendation NUMBER. No action authorized.")
            else:
                index = int(key.rsplit(" ", 1)[1]) - 1
                if not 0 <= index < len(items):
                    raise ValueError("recommendation_number_not_in_report")
                self.say("New supervised mission: recommendation supplied as evidence only. Planning may invoke the configured provider. Charter/plan approval, action approval, review and mission closure remain separate; no patch has been applied.")
                return RepositoryTurn(True, {"recommendation": items[index], "authorizes_action": False,
                                             "non_authority": self.report["non_authority"]})
        elif key.startswith(":repo"):
            self.say("Unknown repository command. Use :repo help; no authority granted.")
        else:
            return RepositoryTurn(False)
        return RepositoryTurn(True)
