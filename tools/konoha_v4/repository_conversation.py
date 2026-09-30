"""Terminal routing/presentation over the existing repository workflow.

No provider calls, independent study engine, or execution authority lives here.
Durable state is exclusively the workflow's existing private study records.
"""
from __future__ import annotations

import re
import secrets
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.repo_evidence import workflow as wf
from tools.repo_evidence.acquire_repo_evidence import _is_private_or_excluded
from tools.repo_evidence.study import explain_repository_study


HELP = """Repository study (no provider or application execution):
  understand this repository / explain Konoha to me
  or in your own words, e.g. explicame este repositorio / qué es Konoha y cómo funciona
  (a request to change, fix, add or run something is a normal mission instead)
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


# Natural-language intent families: deterministic word lists, no model. Matched
# on accent-stripped casefolded tokens. A change/action verb always wins, so a
# coding mission is never captured merely because it mentions the repository.
_MUTATION = re.compile(
    r"modific(?:a|ar|alo|ala|arlo|ame)|modifiqu(?:e|es|en)|arregl(?:a|ar|alo|ala|arlo|e|es|en)"
    r"|agreg(?:a|ar|alo|ala|arlo)|agregu(?:e|es|en)|anad(?:i|e|ir|ilo)|implement(?:a|ar|alo|ala|arlo|e|es|en)"
    r"|ejecut(?:a|ar|alo|ala|arlo|alos|e|es|en)|corr(?:e|er|elo|elos|as)|borr(?:a|ar|alo|ala|e|es|en)"
    r"|elimin(?:a|ar|alo|ala|e|es|en)|cambi(?:a|ar|alo|ala|e|es|en)|actualiz(?:a|ar|alo|ala)|actualic(?:e|es|en)"
    r"|instal(?:a|ar|alo|e|es|en)|refactoriz(?:a|ar|alo)|refactoric(?:e|es|en)|escrib(?:i|e|ir|ilo|as|a)"
    r"|cre(?:a|ar|alo|ala)|corregi(?:r|lo)?|corrig(?:e|elo|a|as)|planific(?:a|ar|alo)|planifiqu(?:e|es|en)"
    r"|migr(?:a|ar|e|es)|aplic(?:a|ar|alo)|apliqu(?:e|es|en)|commite(?:a|ar)|pushe(?:a|ar)"
    r"|modify|fix|add|implement|run|execute|delete|remove|create|write|rewrite|refactor|install|change"
    r"|update|migrate|prepare|deploy|commit|push|patch|apply|edit|merge|rename|build")
# Compared with accents kept: "qué"/"cómo" describe, "que" may introduce a request.
# "se" is not here: "que se agregue" is still a request. These only exempt a verb
# within the same clause; punctuation and conjunctions end the clause.
_NOT_A_REQUEST = {"no", "sin", "nunca", "ni", "jamás", "not", "dont", "doesnt", "without", "never",
                  "cómo", "qué", "cuándo", "dónde", "quién", "how", "what", "when", "where", "who", "does", "did"}
_CLAUSE_END = re.compile(r"[.,;:!?¡¿…()\[\]\n]")
_CONJUNCTION = {"y", "e", "o", "u", "pero", "sino", "despues", "luego", "and", "or", "but", "then"}
_STUDY_VERB = re.compile(
    r"explic(?:a|ame|amelo|amela|anos|ar|arme|alo|as|acion)|explain|entender(?:lo|la)?|entiendo"
    r"|comprender|understand|estudi(?:a|ar|alo|o)|study|mira(?:lo|r)?|ensen(?:a|ame|ar|arme)|teach"
    r"|conta(?:me|nos)|cuenta(?:me|nos)|describ(?:i|ime|e|eme|ir)|describe|resum(?:i|ime|ir)")
_STUDY_QUESTION = ("que es", "como funciona", "como se usa", "para que sirve", "what is", "how does", "how do")
_REPOSITORY = {"repositorio", "repositorios", "repository", "repo", "konoha"}
# An evidence request asks where something came from, or pairs a show/give verb
# with an evidence noun in the same clause. Merely naming a term such as
# "evidence pack" (e.g. to ask what it means) is not a request for evidence.
_EVIDENCE_ORIGIN = ("de donde", "where did", "where does", "where do", "from where")
_EVIDENCE_NOUN = {"evidencia", "evidencias", "evidence", "fuente", "fuentes", "source", "sources", "locator", "locators"}
_SHOW = re.compile(r"mostr\w*|muestr\w*|ensen\w*|dame|danos|pasame|decime|cita\w*|show|give|list|cite")
_CLARIFY = ("no entendi", "no entiendo", "no me quedo claro", "todavia no", "otra manera", "otra forma",
            "de nuevo", "otra vez", "mas simple", "mas facil", "mas despacio", "mas claro", "ejemplo",
            "que significa", "que quiere decir", "repeti", "por que", "que parte", "dont understand",
            "didnt understand", "again", "simpler", "example", "what does", "why")
_ACKNOWLEDGE = {"ok", "okay", "dale", "gracias", "muchas", "mil", "thanks", "thank", "you", "listo", "bien",
                "perfecto", "genial", "joya", "entendi", "entendido", "understood", "si", "yes", "got", "it",
                "claro", "de", "acuerdo", "bueno", "vale", "ya", "perfect", "great", "cool", "nice"}
_CATEGORY_ES = {"components": "Componentes (archivos de código escritos en Python, un lenguaje de programación)",
                "relationships": "Relaciones (qué archivo usa a cuál)",
                "capabilities": "Puntos de entrada (comandos o programas declarados)",
                "tests": "Pruebas (tests: código que comprueba otro código)",
                "documentation": "Documentación (lo que el proyecto dice de sí mismo)",
                "candidates": "Candidatos a revisar (código que quizá no se usa)"}


def _words(text: str) -> tuple[list[str], list[str]]:
    """(accent-stripped tokens, accent-kept tokens) of one human turn."""
    kept = re.findall(r"[^\W_]+", text.casefold().replace("'", "").replace("’", ""))
    plain = ["".join(c for c in unicodedata.normalize("NFKD", w) if not unicodedata.combining(c)) for w in kept]
    return plain, kept


def _requests_action(text: str) -> bool:
    """True when any clause asks to change, fix, add or run something."""
    for clause in _CLAUSE_END.split(text):
        plain, kept = _words(clause)
        before: list[str] = []
        for word, raw in zip(plain, kept):
            if _MUTATION.fullmatch(word) and not _NOT_A_REQUEST.intersection(before[-2:]):
                return True
            before = [] if word in _CONJUNCTION else before + [raw]
    return False


def _asks_for_evidence(text: str) -> bool:
    for clause in _CLAUSE_END.split(text):
        plain, _ = _words(clause)
        joined = " " + " ".join(plain) + " "
        if any(f" {phrase} " in joined for phrase in _EVIDENCE_ORIGIN):
            return True
        if _EVIDENCE_NOUN.intersection(plain) and any(_SHOW.fullmatch(w) for w in plain):
            return True
    return False


def _natural_intent(text: str, active: bool) -> str | None:
    if _requests_action(text):
        return None
    plain, _ = _words(text)
    joined = " " + " ".join(plain) + " "
    about_repository = bool(_REPOSITORY.intersection(plain))
    if _asks_for_evidence(text) and (active or about_repository):
        return "evidence"
    studying = any(_STUDY_VERB.fullmatch(w) for w in plain) or any(f" {q} " in joined for q in _STUDY_QUESTION)
    if studying and about_repository:
        return "study"
    if not active:
        return None
    if studying or any(f" {phrase} " in joined for phrase in _CLARIFY):
        return "clarify"
    if plain and set(plain) <= _ACKNOWLEDGE:
        return "acknowledge"
    return None


# Plain-language presentation for a novice. Sentences about the studied
# repository are chosen by general word families that must match its retained
# README lines, and each one carries those lines' locators. Nothing is read
# afresh; lines that match no family are not quoted, so their unexplained
# optional jargon is omitted and only their source locators are shown;
# missing evidence is reported as missing. Step and rule wording describes this
# terminal's own gates and is cited only where the repository also states it.
_GLOSSARY = (  # general definitions, shown for the terms the human asked about
    (r"\bagentes?\b|\bagents?\b", "Agente",
     "un programa de IA al que se le asigna una responsabilidad concreta y con límites: hace los pasos "
     "de esa tarea (leer, proponer, escribir) y no se sale de lo que le asignaron."),
    (r"\borquestador\w*|\borchestrat\w*", "Orquestador",
     "el que coordina: reparte el trabajo entre varios agentes y cuida el orden, como un director de orquesta."),
    (r"\bruntime\b", "Runtime",
     "la parte del programa que, mientras funciona, lleva a cabo el proceso supervisado paso a paso "
     "(hace lo aprobado y se frena en cada control); no es el código escrito y quieto."),
    (r"\bschemas?\b|\besquemas?\b", "Schema",
     "un molde que dice qué forma deben tener unos datos (qué campos y de qué tipo), para poder comprobarlos."),
    (r"\bevidence packs?\b|\bpaquetes? de evidencia\b", "Evidence pack",
     "«paquete de evidencia»: lo que el estudio guardó de lo que leyó, con archivo y línea exactos, "
     "para poder mostrar de dónde sale cada dato."),
    (r"\bllms?\b", "LLM",
     "«modelo grande de lenguaje»: el tipo de IA que escribe texto o código a partir de lo que le pedís. "
     "Por sí solo no tiene autoridad: lo que escribe es una propuesta, no un permiso ni una verdad comprobada."),
    (r"\bframeworks?\b", "Framework", "una base ya armada que da una forma de trabajar y piezas listas para usar."),
    (r"\bprompts?\b", "Prompt", "el texto que se le escribe a una IA para pedirle algo."),
    (r"\bgit\b|\bcommits?\b", "Git", "un programa que guarda el historial de cambios de los archivos de un proyecto."),
    (r"\brepositori\w*|\brepo\b|\brepository\b", "Repositorio",
     "la carpeta de un proyecto, con todos sus archivos y su historial de cambios."),
)
_DEFINITION = (
    ("terminal", r"terminal|command[- ]line|\bcli\b",
     "se usa escribiendo órdenes en la terminal (la ventana de texto donde se le dan instrucciones a la computadora)"),
    ("local", r"local[- ]first|\blocal\b|your own (?:machine|computer)", "funciona en tu propia computadora"),
    ("ai", r"\bai\b|\bagents?\b|\bllms?\b|\bmodels?\b|artificial",
     "coordina asistentes de inteligencia artificial (IA: programas que escriben texto o código)"),
    ("supervised", r"supervis|human authority|human approval|oversight",
     "trabaja en tareas siempre bajo el control de una persona"),
)
_TOOL_KIND = r"framework|\btool|library|platform|application|\bapp\b|program|system"
_STEPS = (
    ("Pedido", (r"\brequest\b|\bintent\b",), "vos escribís lo que querés que se haga."),
    ("Plan", (r"\bplan\b|charter", r"strateg|propos"),
     "se propone por escrito qué se haría, en qué archivos y con qué riesgos. Es solo una propuesta."),
    ("Aprobación humana", (r"approv|permission|consent",), "vos decís explícitamente «sí» o «no». Sin tu «sí», no pasa nada más."),
    ("Ejecución acotada", (r"execut",), "se hace solo lo aprobado, dentro de límites claros; si algo se sale del plan, se frena."),
    ("Revisión", (r"review",), "otro revisor controla el resultado antes de darlo por bueno."),
)
_RULES = (
    ("plan != permiso", "un plan es una propuesta, no una autorización.",
     (r"(propos|plan)\w*\b.{0,40}\b(?:not|no)\b.{0,15}(permission|approv|authori)", r"(charter|plan)\w* before execution")),
    ("recomendación != permiso", "una sugerencia de mejora no autoriza hacerla.",
     (r"recommend\w*.{0,60}(propos|\bnot\b|\bno\b)",)),
    ("entender != permiso", ":entendido solo cierra este aprendizaje; no aprueba ninguna ejecución.",
     (r"(understand|teachback|entendido).{0,80}\b(no|not)\b",)),
)
_ROLE = (  # (clause pattern, affirmative, negated) for "- **Name:** description" bullets
    (r"\bown work\b|self-approv|approv\w* (?:itself|its own|their own)", None,
     "no aprueba su propio trabajo"),
    (r"final approval|approval authority", "tiene la última palabra: aprueba o rechaza", None),
    (r"interpret|coordinat|orchestrat", "entiende el pedido y coordina el trabajo", "no coordina"),
    (r"draft", "redacta propuestas de cambios a las reglas", None),
    (r"review", "revisa el trabajo de otros", "no revisa"),
    (r"provider|replaceable", "son programas de IA intercambiables que hacen el trabajo técnico", None),
    (r"approv|permission|authori", "aprueba", "no aprueba ni da permiso por su cuenta"),
    (r"stor|retriev|memor", "guarda y recupera información", None),
    (r"execut|assignment", "hace una tarea concreta y con límites", "no ejecuta el trabajo"),
    (r"decide|strateg", "decide la estrategia", "no le toca decidir la estrategia"),
)
_CAN = (
    (r"terminal|entry point", "se usa con un solo comando desde la terminal"),
    (r"first (?:use|run)|reentry", "reconoce si es la primera vez o si estás retomando algo"),
    (r"creat\w*.{0,40}private.{0,40}approv", "crea una carpeta privada para sus datos, solo si lo aprobás"),
    (r"creat\w*.{0,40}private", "crea una carpeta privada para sus datos"),
    (r"inspect\w*.{0,30}(?:cpu|ram|disk|gpu|hardware|machine)", "revisa qué recursos tiene tu computadora"),
    (r"detect\w*.{0,40}readiness|readiness", "detecta qué herramientas externas están listas para usar"),
    (r"propos\w*.{0,30}(?:provider|model)", "propone qué asistente de IA usar para cada tarea"),
    (r"estimat\w*.{0,30}(?:token|cost|usage)", "estima cuánto uso va a gastar una tarea"),
    (r"approvals? separate|separate approvals?", "pide una aprobación distinta para cada paso importante"),
    (r"(?:charter|plan)\w*.{0,30}before", "escribe un plan antes de ejecutar nada"),
    (r"(?:memor|continuity|telemetry).{0,60}private", "guarda su memoria y sus registros en carpetas privadas"),
)
_CANNOT = (
    (r"memory\b.{0,30}(?:authori|permission)", "su memoria no cuenta como permiso para actuar"),
    (r"model output.{0,20}truth", "no toma como verdad lo que dice una IA"),
    (r"provider\w*.{0,40}strateg", "las IAs externas no deciden la estrategia"),
    (r"bypass\w*.{0,10}\bgit\b|\bgit\b.{0,10}gates?", "no se saltea los controles de Git (el registro de cambios del código)"),
    (r"(?:modif|chang|rewrit)\w*.{0,20}(?:doctrine|rules|polic)", "no cambia sus propias reglas"),
    (r"(?:expos|publish|leak|shar)\w*.{0,30}(?:private|secret|personal)", "no publica tus datos privados"),
    (r"self-approv|approv\w* (?:itself|its own)", "no se aprueba a sí mismo"),
    (r"autonom|on its own|by itself", "no ejecuta nada por su cuenta"),
)
_NEEDS = (
    (r"charter|\bplan\b", "el plan escrito de la tarea"),
    (r"\baction\b|execut", "cada acción que cambie algo"),
    (r"review", "aceptar el resultado de la revisión"),
    (r"\bgit\b(?![-\w])|commit|push", "guardar o subir cambios con Git"),
    (r"release|publish", "publicar una versión nueva"),
    (r"village|private", "crear su carpeta privada"),
    (r"install", "instalar programas"),
    (r"closure|\bclose\b", "dar la tarea por terminada"),
)
_CAN_SECTION = r"what .*\bdoes\b|features?|capabilit|que hace|funcionalidad|caracteristicas"
_CANNOT_SECTION = r"\b(?:not|never|cannot|limitations?|limits?|non-goals?|limites)\b|no (?:hace|puede)"
_FLOW_SECTION = r"flow|how it works|workflow|lifecycle|como funciona|flujo|proceso"
_NEGATED = r"\b(?:no|not|never|cannot|without)\b|n't\b"
_DIAGRAM_LANGUAGES = {"mermaid", "dot", "graphviz", "plantuml"}
_TEXT_LANGUAGES = {"", "text", "txt", "plain", "plaintext"}


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def _readme_lines(pack) -> list[dict]:
    """Retained lines of the top-level README, annotated with section and kind."""
    readmes = [c for c in pack.doc_claims if c["path"].rsplit("/", 1)[-1].casefold() == "readme.md"
               and c["evidence_ref"] in pack.provenance_index]
    if not readmes:
        return []
    path = min({c["path"] for c in readmes}, key=lambda p: (p.count("/"), p))
    lines, fence, section = [], None, ""
    for claim in sorted((c for c in readmes if c["path"] == path), key=lambda c: c["line"]):
        text = claim["statement"]
        if text.startswith("```"):
            fence = None if fence is not None else text[3:].strip().casefold()
            continue
        if fence is None and text.startswith("#"):
            kind, section = "heading", text.lstrip("#").strip()
        elif fence is not None:
            # Prose-like text blocks count; commands and diagrams are not statements.
            kind = "block" if fence in _TEXT_LANGUAGES else "diagram" if fence in _DIAGRAM_LANGUAGES else "code"
        elif re.match(r"(?:[-*+]|\d+[.)])\s", text):
            kind = "bullet"
        elif re.match(r"(?:!\[|\[!\[|<|\|)", text):
            kind = "other"
        else:
            kind = "prose"
        lines.append({**claim, "kind": kind, "section": _fold(section)})
    return lines


def _first(lines: list[dict], patterns, *, kinds=("prose", "bullet", "block"), affirmative=False) -> dict | None:
    for pattern in patterns:
        for line in lines:
            text = _fold(line["statement"])
            if line["kind"] in kinds and re.search(pattern, text) and not (affirmative and re.search(_NEGATED, text)):
                return line
    return None


def _bullets(lines: list[dict], section: str, exclude: str | None = None) -> list[dict]:
    return [line for line in lines if line["kind"] == "bullet" and re.search(section, line["section"])
            and not (exclude and re.search(exclude, line["section"]))]


def _mapped(lines: list[dict], table, *, affirmative=False) -> tuple[list[tuple[str, list[dict]]], list[dict]]:
    """Group lines under the first matching plain phrase; also return unmatched lines."""
    phrases: dict[str, list[dict]] = {}
    unmatched = []
    for line in lines:
        text = _fold(line["statement"])
        negated = affirmative and re.search(_NEGATED, text)
        phrase = None if negated else next((spanish for pattern, spanish in table if re.search(pattern, text)), None)
        if phrase is None:
            unmatched.append(line)
        else:
            phrases.setdefault(phrase, []).append(line)
    return list(phrases.items()), unmatched


def _role(description: str) -> str | None:
    glosses = []
    for clause in re.split(r"[;:]", _fold(description)):
        negated = re.search(_NEGATED, clause)
        for pattern, affirmative, negative in _ROLE:
            if re.search(pattern, clause) and (negative if negated else affirmative):
                glosses.append(negative if negated else affirmative)
                break
    return "; ".join(dict.fromkeys(glosses)) or None


def _compose(pack, study) -> dict:
    """Evidence-conditioned novice explanation: every repository sentence has sources."""
    lines = _readme_lines(pack)
    title = next((line for line in lines if line["kind"] == "heading" and line["statement"].startswith("# ")), None)
    purpose = [line for line in lines if line["kind"] == "prose" and len(line["statement"].split()) >= 4][:2]
    subject = re.match(r"\W*([A-Z][\w.-]*(?: [A-Z][\w.-]*){0,3}) (?:is|es|are)\b",
                       re.sub(r"[*_`]", "", purpose[0]["statement"])) if purpose else None
    name = subject[1] if subject else re.sub(r"[*_`#]", "", title["statement"]).strip() if title else "Este proyecto"
    result: dict = {"name": name, "readme": bool(lines), "purpose": purpose, "definition": None, "problem": None}
    # Only affirmative clauses describe what the project is; a negated clause
    # ("is not an AI framework") must never become a positive capability.
    purpose_text = " . ".join(clause for line in purpose for clause in re.split(r"[.;:!?]", _fold(line["statement"]))
                              if not re.search(_NEGATED, clause))
    found = {key: phrase for key, pattern, phrase in _DEFINITION if re.search(pattern, purpose_text)}
    if found:
        phrases = list(found.values())
        sentence = ", ".join(phrases[:-1]) + (" y " if len(phrases) > 1 else "") + phrases[-1]
        if "supervised" in found and re.search(r"\bmissions?\b", purpose_text):
            sentence += " (su documentación llama «misiones» a esas tareas)"
        kind = "una herramienta" if re.search(_TOOL_KIND, purpose_text) else "un proyecto"
        result["definition"] = (f"{name} es {kind} que {sentence}.", purpose)
    if {"ai", "supervised"} <= set(found):
        support = [line for line in [_first(purpose, (r"not replace human|human authority",)),
                                     _first(_bullets(lines, _CANNOT_SECTION), (r"autonom|on its own|by itself",))] if line]
        result["problem"] = ("Una IA que actúa sola puede hacer cambios que nadie aprobó. "
                             f"{name} sirve para usar asistentes de IA en tareas reales sin perder el control: "
                             "la IA propone y trabaja, y una persona decide cada paso importante.",
                             list({line["evidence_ref"]: line for line in purpose + support}.values()))
    flow = [line for line in lines if re.search(_FLOW_SECTION, line["section"])]
    result["steps"] = []
    for label, patterns, text in _STEPS:
        source = _first(flow, patterns) or _first(lines, patterns, kinds=("prose", "bullet"), affirmative=True)
        result["steps"].append((label, text, [source] if source else []))
    result["rules"] = []
    for label, text, patterns in _RULES:
        source = _first(lines, patterns)
        sources = [source] if source else []
        # A sentence wrapped over retained consecutive lines is cited whole.
        while sources and len(sources) < 3 and not re.search(r"[.:;!?]$", sources[-1]["statement"]):
            following = next((line for line in lines if line["line"] == sources[-1]["line"] + 1
                              and line["kind"] == sources[-1]["kind"]), None)
            if following is None:
                break
            sources.append(following)
        result["rules"].append((label, text, sources))
    parts, unnamed = [], []
    for line in lines:
        match = re.match(r"[-*+]\s+\*\*(.+?)\*\*\s*:?\s*(.*)$", line["statement"]) if line["kind"] == "bullet" else None
        if match and len(parts) < 8:
            gloss = _role(match[2])
            if gloss:
                parts.append((f"{match[1].rstrip(':').strip()}: {gloss}", [line]))
            else:
                unnamed.append(line)
    result["parts"], result["parts_rest"] = parts, unnamed
    can, can_rest = _mapped(_bullets(lines, _CAN_SECTION, _CANNOT_SECTION), _CAN, affirmative=True)
    cannot, cannot_rest = _mapped(_bullets(lines, _CANNOT_SECTION), _CANNOT)
    result["can"], result["can_rest"] = can, can_rest
    result["cannot"], result["cannot_rest"] = cannot, cannot_rest
    approvals = [line for line in lines if line["kind"] in ("prose", "bullet", "block")
                 and re.search(r"approv|permission|consent|authori", _fold(line["statement"]))
                 and not re.search(_NEGATED, _fold(line["statement"]))]
    result["needs"] = []
    for pattern, phrase in _NEEDS:
        source = next((line for line in approvals if re.search(pattern, _fold(line["statement"]))), None)
        if source:
            result["needs"].append((phrase, [source]))
    facts = {}
    for fact in study.facts:
        facts.setdefault(fact["category"], []).append(fact)
    result["facts"] = facts
    return result


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

    def _activate(self, session: StudySession, *, novice: str | None = None):
        # novice: the human's own natural request, answered in plain language.
        if novice is None:
            self.say(f"Requested study: {session.study_id}")
        session.load()  # validate before remembering a session or displaying facts
        self.active = session
        self.sessions[session.study_id] = session
        if session.repo == self.repo:
            self.target = session
        self._clear_report()
        if novice is None:
            self._explain()
        else:
            self._novice("study", novice)

    def _request_study(self, path: str | None = None, study_id: str | None = None, *, novice: str | None = None):
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
            self._open(repo, study_id, novice=novice)
        elif study_id in self.sessions and self.sessions[study_id].repo == repo:
            self._activate(self.sessions[study_id])
        else:
            self.pending = (repo, study_id)
            self.authorization_command = ":repo authorize " + secrets.token_hex(8)
            self.say(f"Target requested: {repo}\nNo target evidence has been read. Confirm that this is an authorized PUBLIC local checkout.\n"
                     "This permits bounded static study and private study-state storage only; private/ignored paths stay excluded.\n"
                     f"Enter exactly: {self.authorization_command}\nUse :repo cancel to cancel. Ordinary yes/ok is not authorization.")

    def _open(self, repo: Path, study_id: str | None, *, novice: str | None = None):
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
        self._activate(StudySession(repo, auth, self.state_root, study_id), novice=novice)

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

    def _novice(self, mode: str, request: str):
        # Presentation only: the retained pack and study from the workflow's own
        # validated load; no provider, no fresh repository reads.
        record, study, pack = self._required().load()
        view = _compose(pack, study)
        render = {"study": self._novice_study, "clarify": self._novice_clarify, "evidence": self._novice_evidence}[mode]
        self.say(render(view, study, request))
        status = {"awaiting_human": "esperando que lo expliques con tus palabras",
                  "understood": "cerrado con :entendido"}.get(record["teachback"]["status"], record["teachback"]["status"])
        self.say(f"Estudio {study.study_id} (aprendizaje: {status}).\n"
                 "Podés decir: 'no entendí esa parte', 'explicámelo de otra manera' o 'mostrame de dónde sacaste eso'. "
                 "Cuando puedas explicarlo con tus palabras, escribí exactamente :entendido; eso no aprueba ninguna ejecución.")

    @staticmethod
    def _cite(sources: list[dict]) -> str:
        return " ".join(f"[{s['path']}:{s['line']}]" for s in sources)

    @classmethod
    def _untranslated(cls, sources: list[dict]) -> str:
        one = len(sources) == 1
        return (f"no {'la' if one else 'las'} resumo porque no sé decirl{'a' if one else 'as'} en simple sin inventar "
                "ni sin usar palabras técnicas que no te expliqué; "
                f"{'está' if one else 'están'} en {cls._cite(sources[:10])}" + (" y otras" if len(sources) > 10 else "") + ".")

    @staticmethod
    def _glossary(request: str) -> list[str]:
        folded = _fold(request)
        return [f"  - {term}: {meaning}" for pattern, term, meaning in _GLOSSARY if re.search(pattern, folded)]

    def _novice_study(self, view: dict, study, request: str) -> str:
        cite, facts, name = self._cite, view["facts"], view["name"]
        lines = [f"Explicación desde cero: {name}.", "Qué es, en un párrafo:"]
        if view["definition"]:
            text, sources = view["definition"]
            lines.append(f"  {text} {cite(sources)}")
        elif view["purpose"]:
            lines.append("  Su documentación se describe con palabras que no puedo simplificar sin inventar; "
                         f"la ves textual si pedís la evidencia {cite(view['purpose'])}.")
        else:
            lines.append("  No encontré un README con una descripción, así que no puedo decir qué es sin inventarlo.")
        lines.append("Para qué sirve y qué problema intenta resolver (mi resumen de su documentación):")
        if view["problem"]:
            text, sources = view["problem"]
            lines.append(f"  {text} {cite(sources)}")
        else:
            lines.append("  Su documentación no lo dice con claridad; no lo voy a inventar.")
        glossary = self._glossary(request)
        if glossary:
            lines += ["Palabras técnicas, cada una en una frase:"] + glossary
        lines.append("Cómo funciona una tarea, desde que la pedís hasta que termina:")
        for number, (label, text, sources) in enumerate(view["steps"], 1):
            lines.append(f"  {number}) {label}: {text} " + (cite(sources) or "(así funciona esta terminal; su documentación no lo menciona)"))
        lines.append("  Es como una fila de puertas: si una no se abre (por ejemplo, no aprobás), las siguientes no pasan.")
        lines.append("Reglas que no cambian:")
        for label, text, sources in view["rules"]:
            lines.append(f"  - {label}: {text} {cite(sources)}".rstrip())
        lines.append("Partes principales (nombres que usa su documentación; cada uno es un rol: un papel con tareas y límites):")
        lines += [f"  - {text} {cite(sources)}" for text, sources in view["parts"]]
        if view["parts_rest"]:
            lines.append(f"  - y {len(view['parts_rest'])} más: {self._untranslated(view['parts_rest'])}")
        if not view["parts"]:
            first = (facts.get("components") or [None])[0]
            lines.append("  - Su README no trae una lista de partes. " + (
                f"El estudio encontró {study.coverage['components']['total']} archivos de código escritos en Python "
                "(un lenguaje de programación); "
                f"por ejemplo {first['locator']['path']} [{first['locator']['path']}:{first['locator']['line_start']}]."
                if first else "El estudio tampoco incluyó archivos de código."))
        for title, phrases, rest, empty in (
                ("Qué cosas puede hacer, según su documentación:", view["can"], view["can_rest"],
                 "Su documentación no trae una lista clara de lo que hace."),
                ("Qué cosas NO hace por su cuenta, según su documentación:", view["cannot"], view["cannot_rest"],
                 "Su documentación no trae una lista de lo que no hace. Lo seguro: este estudio no ejecutó nada.")):
            lines.append(title)
            lines += [f"  - {phrase} {cite(sources)}" for phrase, sources in phrases]
            if rest:
                lines.append(f"  - y {len(rest)} {'cosa' if len(rest) == 1 else 'cosas'} más: {self._untranslated(rest)}")
            if not phrases and not rest:
                lines.append("  - " + empty)
        lines.append("Qué cosas siempre necesitan tu permiso explícito:")
        lines += [f"  - {phrase} {cite(sources)}" for phrase, sources in view["needs"]]
        lines.append("  - En esta terminal, cualquier pedido de cambiar, arreglar, agregar o ejecutar algo es una misión nueva: "
                     "no se ejecuta nada hasta que apruebes su plan. Un «ok» suelto no cuenta como permiso.")
        lines.append("Qué encontró el estudio en este repositorio (leyendo archivos, sin ejecutarlos; no es una lista completa):")
        for category, label in _CATEGORY_ES.items():
            if facts.get(category):
                locator = facts[category][0]["locator"]
                lines.append(f"  - {label}: {study.coverage.get(category, {}).get('total', '?')} encontrados; "
                             f"por ejemplo [{locator['path']}:{locator['line_start']}]")
        example = (facts.get("tests") or facts.get("components") or [None])[0]
        if example is None:
            lines.append("Ejemplo concreto: el estudio no incluyó archivos suficientes para armar uno.")
        else:
            path = example["locator"]["path"]
            tests = example["category"] == "tests"
            lines += [f"Ejemplo concreto de una tarea real, paso a paso: querés {'comprobar que pasan las pruebas de' if tests else 'que se revise'} "
                      f"{path} [{path}:{example['locator']['line_start']}].",
                      f"  1) Pedido: escribís «{'ejecutá las pruebas de' if tests else 'revisá'} {path}». "
                      "Como pide hacer algo, ya no es una pregunta: es una misión nueva.",
                      "  2) Plan: se propone qué se va a hacer, qué archivos se tocan y qué riesgos hay.",
                      "  3) Aprobación humana: leés el plan y respondés que sí o que no. Si decís que no, termina acá.",
                      "  4) Ejecución acotada: se hace solo eso, nada más.",
                      "  5) Revisión: se controla el resultado y se te muestra qué pasó; vos decidís si la tarea terminó.",
                      "  Hoy el estudio solo sabe que ese archivo existe; no sabe si funciona."]
        lines += ["Límites, en simple: el estudio solo leyó archivos; no ejecutó nada, no comprobó que la documentación diga "
                  "la verdad y puede haber dejado cosas afuera. Entenderlo no autoriza ningún cambio.",
                  "Los [archivo:línea] dicen de dónde salió cada dato; si pedís 'mostrame de dónde sacaste eso', "
                  "te muestro el texto exacto de cada fuente."]
        return "\n".join(lines)

    def _novice_clarify(self, view: dict, study, request: str) -> str:
        lines = ["Otra forma de verlo."]
        glossary = self._glossary(request)
        if glossary:
            lines += ["Palabras técnicas, cada una en una frase:"] + glossary
        if re.search(r"plan|permis|aprob|autoriz|permission|approv", _fold(request)):
            lines += ["Planear y tener permiso son dos cosas distintas:",
                      "  - Planear es escribir qué se haría. Es como el presupuesto de un mecánico: dice qué arreglaría, "
                      "con qué repuestos y qué puede salir mal. Leer el presupuesto no le da permiso para tocar tu auto.",
                      "  - Tener permiso es que vos digas explícitamente «sí, hacelo». Recién ahí puede empezar, y solo con lo que aprobaste.",
                      "  - Si no decís nada, o respondés algo ambiguo como «ok», no hay permiso: todo queda frenado.",
                      "  - Lo mismo con una recomendación (es una idea, no un permiso) y con :entendido "
                      "(dice que entendiste, no que aprobás algo)."]
            cited = [f"  - {label} {self._cite(sources)}" for label, _, sources in view["rules"] if sources]
            if cited:
                lines += ["Dónde lo dice su documentación:"] + cited
        elif view["definition"]:
            text, sources = view["definition"]
            lines.append(f"En una frase: {text} {self._cite(sources)}")
        lines += ["La fila de puertas, que se abren de a una:",
                  "  pedido -> plan propuesto -> tu aprobación -> ejecución acotada -> revisión",
                  "  Si una puerta no se abre (por ejemplo, no aprobás), las siguientes no pasan."]
        return "\n".join(lines)

    def _novice_evidence(self, view: dict, study, request: str) -> str:
        def full(source: dict) -> str:
            return self._locator({"study_id": study.study_id, "evidence_reference": study.evidence_reference,
                                  "evidence_ref": source["evidence_ref"],
                                  "locator": {"path": source["path"], "line_start": source["line"]}})

        items = []
        if view["definition"]:
            items.append(("Qué es", *view["definition"]))
        elif view["purpose"]:
            items.append(("Cómo se describe a sí mismo", "(texto original, sin simplificar)", view["purpose"]))
        if view["problem"]:
            items.append(("Para qué sirve", *view["problem"]))
        items += [(f"Paso «{label}»", text, sources) for label, text, sources in view["steps"] if sources]
        items += [(label, text, sources) for label, text, sources in view["rules"] if sources]
        items += [("Parte", text, sources) for text, sources in view["parts"]]
        items += [("Puede", phrase, sources) for phrase, sources in view["can"]]
        items += [("No hace por su cuenta", phrase, sources) for phrase, sources in view["cannot"]]
        items += [("Necesita tu permiso", phrase, sources) for phrase, sources in view["needs"]]
        lines = ["De dónde salen las afirmaciones más importantes.",
                 "Cómo leerlo: debajo de cada afirmación va la línea exacta del archivo, copiada tal cual quedó guardada "
                 "en el estudio, y entre corchetes su ubicación: [estudio / paquete de evidencia / referencia interna / archivo:línea].",
                 "Esas líneas dicen lo que el proyecto afirma de sí mismo; el estudio no comprobó que sea verdad."]
        for number, (label, text, sources) in enumerate(items, 1):
            lines.append(f"{number}. {label}: {text}")
            lines += [f"   «{source['statement']}» [{full(source)}]" for source in sources[:3]]
        rest = view["parts_rest"] + view["can_rest"] + view["cannot_rest"]
        if rest:
            # Unmatched lines are not important claims; quoting their jargon would leave it unexplained.
            lines.append(f"{'Otra línea' if len(rest) == 1 else 'Otras líneas'} de esas listas: {self._untranslated(rest)}")
        example = (view["facts"].get("tests") or view["facts"].get("components") or [None])[0]
        if example is not None:
            lines.append(f"{len(items) + 1}. Ejemplo: el archivo {example['locator']['path']} existe; el estudio no lo ejecutó. "
                         f"[{self._locator({'study_id': study.study_id, 'evidence_reference': study.evidence_reference, 'evidence_ref': example['evidence_ref'], 'locator': example['locator']})}]")
        if not items:
            lines.append("No encontré en la documentación guardada afirmaciones sobre qué es o cómo funciona; "
                         "solo tengo los datos técnicos del estudio (show me the evidence).")
        lines += ["Cada fuente quedó guardada junto con una huella (hash) del archivo: si el archivo cambia, "
                  "este estudio deja de valer y hay que hacer uno nuevo.",
                  "La lista técnica completa se ve con: show me the evidence"]
        return "\n".join(lines)

    def _natural(self, text: str) -> RepositoryTurn:
        intent = _natural_intent(text, self.active is not None)
        if intent is None:
            return RepositoryTurn(False)
        if self.pending is not None and intent == "acknowledge":
            self.say("Authorization pending; use the exact displayed :repo authorize command or :repo cancel.")
            return RepositoryTurn(True)
        if intent == "study" or intent == "evidence" and self.active is None:
            # Same canonical path as "understand this repository".
            if self.target:
                self._activate(self.target, novice=text)
            else:
                self._request_study(novice=text)
            if intent == "study" or self.active is None:
                return RepositoryTurn(True)
        session = self._required()
        record = wf.respond_to_study(session.repo, session.authorization, session.state_root, session.study_id, text, actor="human")
        if intent in ("evidence", "clarify"):
            self._novice(intent, text)
        else:
            self.say(f"Teachback: {record['teachback']['status']}. {record['teachback']['non_authority']}\n"
                     "Anotado. Un 'ok' o un 'gracias' no cierra el aprendizaje; cuando puedas explicarlo con tus palabras, "
                     "escribí exactamente :entendido. Eso no aprueba ninguna ejecución.")
        return RepositoryTurn(True)

    def handle(self, text: str) -> RepositoryTurn:
        key = text.strip().casefold().rstrip("?")
        try:
            # Exact commands are single lines. A multiline turn only reaches the
            # conservative natural-language families, never a keyword inside it.
            if "\n" in text:
                return self._natural(text)
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
        elif key in {"explain", "explain that again", "repeat", "show me the evidence", ":repo evidence", "what does this component do"} or key.startswith("explain ") and self.active and not _requests_action(text):
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
            return self._natural(text)
        return RepositoryTurn(True)
