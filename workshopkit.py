"""Small, inspectable runtime for the AI Agents student workshop.

The helpers deliberately expose observable messages, tool requests, tool
results and final answers. They never request or display hidden reasoning.
All campus data and actions in this module are deterministic simulations.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
load_dotenv(ROOT / ".env", override=True)
DEFAULT_MODEL = os.getenv("WORKSHOP_MODEL", "claude-sonnet-5")


def _client() -> Anthropic:
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env", override=True)
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    return Anthropic(api_key=api_key)


def ask_claude(system: str, prompt: str, max_tokens: int = 900) -> str:
    """Make one model call and return visible text."""
    response = _client().messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system.strip(),
        messages=[{"role": "user", "content": prompt.strip()}],
    )
    return "\n".join(block.text for block in response.content if block.type == "text").strip()


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]

    def api_definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def execute(self, arguments: dict[str, Any]) -> Any:
        return self.handler(arguments)


def _find_study_room(args: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("WORKSHOP_SIMULATE_ROOM_FAILURE") == "1":
        return {
            "ok": False,
            "error": "Room availability service is temporarily unavailable",
            "source": "workshop simulator",
            "is_live_booking_data": False,
        }
    date = str(args.get("date", "unspecified"))
    time = str(args.get("time", "unspecified"))
    group_size = max(1, int(args.get("group_size", 1)))
    duration = int(args.get("duration_minutes", 120))
    accessible = bool(args.get("accessibility_required", False))
    day = date.lower()
    start = time.lower()
    rooms = [
        {"room": "Bayliss 2.24", "capacity": 8, "accessible": True, "available": "tue" in day and ("3" in start or "15" in start)},
        {"room": "Reid 1.43", "capacity": 6, "accessible": False, "available": True},
        {"room": "Barry J Marshall 5.10", "capacity": 16, "accessible": True, "available": group_size >= 7},
    ]
    matches = [
        room for room in rooms
        if room["available"]
        and room["capacity"] >= group_size
        and (not accessible or room["accessible"])
    ]
    return {
        "ok": True,
        "date": date,
        "time": time,
        "duration_minutes": duration,
        "group_size": group_size,
        "accessibility_required": accessible,
        "matches": matches,
        "source": "workshop simulator",
        "is_live_booking_data": False,
    }


def _check_group_availability(args: dict[str, Any]) -> dict[str, Any]:
    options = args.get("options") or ["Tuesday 15:00", "Wednesday 11:00", "Friday 15:00"]
    return {
        "ok": True,
        "group_size": 5,
        "available_for_everyone": [option for option in options if "Tuesday" in option or "15:00" in option][:2],
        "source": "fictional group calendars",
        "is_live_calendar_data": False,
    }


def _create_group_task(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "draft_only",
        "task": str(args.get("task", "Untitled task")),
        "owner": str(args.get("owner", "unassigned")),
        "due": str(args.get("due", "not set")),
        "requires_student_confirmation": True,
    }


def _draft_calendar_invite(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "draft_only",
        "title": str(args.get("title", "Group study session")),
        "date": str(args.get("date", "unspecified")),
        "time": str(args.get("time", "unspecified")),
        "room": str(args.get("room", "not selected")),
        "requires_student_approval_before_sending": True,
    }


find_study_room = Tool(
    "find_study_room",
    "Find simulated study rooms that meet a requested time, capacity and accessibility need. This does not book a room.",
    {
        "type": "object",
        "properties": {
            "date": {"type": "string"},
            "time": {"type": "string"},
            "duration_minutes": {"type": "integer", "default": 120},
            "group_size": {"type": "integer"},
            "accessibility_required": {"type": "boolean", "default": False},
        },
        "required": ["date", "time", "group_size"],
    },
    _find_study_room,
)

check_group_availability = Tool(
    "check_group_availability",
    "Compare fictional group calendars and return times that work for everyone.",
    {
        "type": "object",
        "properties": {"options": {"type": "array", "items": {"type": "string"}}},
        "required": ["options"],
    },
    _check_group_availability,
)

create_group_task = Tool(
    "create_group_task",
    "Prepare a group task as a draft. The student must confirm before it is shared.",
    {
        "type": "object",
        "properties": {
            "task": {"type": "string"},
            "owner": {"type": "string"},
            "due": {"type": "string"},
        },
        "required": ["task"],
    },
    _create_group_task,
)

draft_calendar_invite = Tool(
    "draft_calendar_invite",
    "Prepare, but do not send, a calendar invitation for the group.",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "date": {"type": "string"},
            "time": {"type": "string"},
            "room": {"type": "string"},
        },
        "required": ["title", "date", "time"],
    },
    _draft_calendar_invite,
)

BASIC_TOOLS = [
    check_group_availability,
    find_study_room,
    create_group_task,
    draft_calendar_invite,
]


LEADERSHIP_NOTES = DATA_DIR / "leadership_revision_notes.txt"
LEADERSHIP_MASTERY = DATA_DIR / "leadership_mastery.json"


def _normalise_leadership_topic(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ")
    aliases = {
        "motivation": "motivation",
        "situational": "situational leadership",
        "situational leadership": "situational leadership",
        "psychological safety": "psychological safety",
        "safety": "psychological safety",
    }
    return aliases.get(text, text)


def _get_mastery_record(args: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("WORKSHOP_SIMULATE_STUDY_DATA_FAILURE") == "1":
        return {
            "ok": False,
            "error": "Mastery record is temporarily unavailable",
            "source": "workshop simulator",
        }
    data = json.loads(LEADERSHIP_MASTERY.read_text(encoding="utf-8"))
    profile = str(args.get("profile", "mixed")).strip().lower()
    scores = data["profiles"].get(profile)
    if scores is None:
        return {
            "ok": False,
            "error": f"Unknown mastery profile: {profile}",
            "available_profiles": sorted(data["profiles"]),
        }
    topic = _normalise_leadership_topic(args.get("topic"))
    if topic:
        if topic not in scores:
            return {"ok": False, "error": f"Unknown leadership topic: {topic}"}
        scores = {topic: scores[topic]}
    return {
        "ok": True,
        "student": data["student"],
        "unit": data["unit"],
        "profile": profile,
        "scores": scores,
        "scale": data["scale"],
        "source": data["source"],
    }


def _leadership_search(args: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("WORKSHOP_SIMULATE_STUDY_DATA_FAILURE") == "1":
        return {
            "ok": False,
            "error": "Leadership notes search is temporarily unavailable",
            "source": "workshop simulator",
        }
    query = str(args.get("query", "")).strip()
    top_k = max(1, min(3, int(args.get("top_k", 2))))
    text = LEADERSHIP_NOTES.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## (.+)$", text, flags=re.MULTILINE))
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    results = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = heading.group(1).strip()
        passage = text[heading.end():end].strip()
        words = set(re.findall(r"[a-z0-9]+", f"{section} {passage}".lower()))
        score = len(terms & words)
        if score:
            results.append({"section": section, "score": score, "text": passage})
    results.sort(key=lambda item: (-item["score"], item["section"]))
    return {
        "ok": True,
        "query": query,
        "results": results[:top_k],
        "source": LEADERSHIP_NOTES.name,
        "is_official_course_material": False,
    }


_STUDY_BANK: dict[str, dict[str, Any]] = {
    "motivation": {
        "section": "Motivation",
        "flashcards": [
            {"front": "What distinguishes intrinsic from extrinsic motivation?", "back": "Intrinsic motivation comes from the activity itself; extrinsic motivation is driven by a separable outcome."},
            {"front": "Which three needs are central to self-determination theory?", "back": "Autonomy, competence and relatedness."},
            {"front": "What three judgments connect effort to motivation in expectancy theory?", "back": "Effort can improve performance, performance can produce an outcome, and the outcome is valued."},
            {"front": "Why might a valued reward still fail to motivate?", "back": "Motivation can remain low when the effort-to-performance or performance-to-outcome link is weak."},
        ],
        "questions": [
            {"question": "A team values a bonus but believes workload makes the target impossible. Which part of expectancy theory is weakest?", "check_for": "The effort-to-performance judgment."},
            {"question": "Give one management action that supports autonomy without removing expectations.", "check_for": "Meaningful choice combined with clear expectations."},
        ],
    },
    "situational leadership": {
        "section": "Situational leadership",
        "flashcards": [
            {"front": "What should a leader diagnose before adapting their approach?", "back": "The specific task plus the person’s current capability and confidence."},
            {"front": "Why is readiness not a permanent label?", "back": "Capability and confidence can vary across tasks and change over time."},
            {"front": "What two dimensions are balanced in situational leadership?", "back": "Direction and support."},
        ],
        "questions": [
            {"question": "A capable employee is confident in routine work but new to client negotiation. How should the leader’s approach change for that task?", "check_for": "More task-specific direction while preserving appropriate autonomy and support."},
            {"question": "What evidence would you seek before deciding that someone needs more direction?", "check_for": "Task-specific capability and confidence rather than a fixed personality label."},
        ],
    },
    "psychological safety": {
        "section": "Psychological safety",
        "flashcards": [
            {"front": "What is psychological safety?", "back": "A shared belief that interpersonal risks can be taken without humiliation or punishment."},
            {"front": "Does psychological safety mean lowering standards?", "back": "No. A team can combine safety for speaking up with clear accountability and quality standards."},
            {"front": "Name two leader behaviours that support psychological safety.", "back": "Examples include acknowledging uncertainty, inviting dissent and responding constructively to bad news."},
        ],
        "questions": [
            {"question": "A manager says mistakes are unacceptable, so team members hide problems. What leadership behaviour could change the pattern?", "check_for": "A constructive response to bad news while keeping accountability clear."},
            {"question": "How can a team encourage dissent without allowing decisions to stall indefinitely?", "check_for": "Separate safe contribution from final accountability and decision rules."},
        ],
    },
}


def _draft_flashcards(args: dict[str, Any]) -> dict[str, Any]:
    topic = _normalise_leadership_topic(args.get("topic"))
    source_excerpt = str(args.get("source_excerpt", "")).strip()
    if not source_excerpt:
        return {"ok": False, "error": "A retrieved source excerpt is required before drafting flashcards"}
    bank = _STUDY_BANK.get(topic)
    if bank is None:
        return {"ok": False, "error": f"No supplied flashcard material for: {topic}"}
    count = max(1, min(len(bank["flashcards"]), int(args.get("count", 3))))
    return {
        "ok": True,
        "topic": topic,
        "cards": bank["flashcards"][:count],
        "source": LEADERSHIP_NOTES.name,
        "source_section": bank["section"],
        "status": "draft_for_student_review",
    }


def _draft_practice_questions(args: dict[str, Any]) -> dict[str, Any]:
    topic = _normalise_leadership_topic(args.get("topic"))
    source_excerpt = str(args.get("source_excerpt", "")).strip()
    if not source_excerpt:
        return {"ok": False, "error": "A retrieved source excerpt is required before drafting practice questions"}
    bank = _STUDY_BANK.get(topic)
    if bank is None:
        return {"ok": False, "error": f"No supplied practice material for: {topic}"}
    count = max(1, min(len(bank["questions"]), int(args.get("count", 2))))
    return {
        "ok": True,
        "topic": topic,
        "questions": bank["questions"][:count],
        "source": LEADERSHIP_NOTES.name,
        "source_section": bank["section"],
        "status": "formative_practice_only",
    }


get_mastery_record = Tool(
    "get_mastery_record",
    "Read Aisha's fictional topic mastery scores. Use this before choosing the kind of revision support.",
    {
        "type": "object",
        "properties": {
            "profile": {"type": "string", "enum": ["weak", "mixed", "strong"]},
            "topic": {"type": "string"},
        },
        "required": ["profile"],
    },
    _get_mastery_record,
)

search_leadership_notes = Tool(
    "search_leadership_notes",
    "Search the supplied fictional Leadership in Organisations notes and return source-labelled passages.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 2},
        },
        "required": ["query"],
    },
    _leadership_search,
)

draft_flashcards = Tool(
    "draft_flashcards",
    "Draft short, source-grounded flashcards from a retrieved leadership-notes passage.",
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "source_excerpt": {"type": "string"},
            "count": {"type": "integer", "default": 3},
        },
        "required": ["topic", "source_excerpt"],
    },
    _draft_flashcards,
)

draft_practice_questions = Tool(
    "draft_practice_questions",
    "Draft formative application questions from a retrieved leadership-notes passage.",
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "source_excerpt": {"type": "string"},
            "count": {"type": "integer", "default": 2},
        },
        "required": ["topic", "source_excerpt"],
    },
    _draft_practice_questions,
)

STUDY_COACH_TOOLS = [
    get_mastery_record,
    search_leadership_notes,
    draft_flashcards,
    draft_practice_questions,
]


def run_agent(
    instructions: str,
    task: str,
    tools: list[Tool] | None = None,
    max_steps: int = 6,
    max_tokens: int = 800,
) -> dict[str, Any]:
    """Run a transparent tool-use loop and return observable events."""
    tools = tools or []
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
    events: list[dict[str, Any]] = [{"type": "user", "text": task}]
    definitions = [tool.api_definition() for tool in tools]
    by_name = {tool.name: tool for tool in tools}

    for _ in range(max_steps):
        kwargs: dict[str, Any] = {
            "model": DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "system": instructions.strip(),
            "messages": messages,
        }
        if definitions:
            kwargs["tools"] = definitions
        response = _client().messages.create(**kwargs)
        assistant_blocks: list[dict[str, Any]] = []
        tool_results: list[dict[str, Any]] = []
        final_text: list[str] = []

        for block in response.content:
            if block.type == "text":
                final_text.append(block.text)
                assistant_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                arguments = dict(block.input)
                events.append({"type": "tool", "name": block.name, "input": arguments})
                tool = by_name.get(block.name)
                if tool is None:
                    result: Any = {"ok": False, "error": f"Unknown tool: {block.name}"}
                    is_error = True
                else:
                    try:
                        result = tool.execute(arguments)
                        is_error = isinstance(result, dict) and result.get("ok") is False
                    except Exception as exc:
                        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                        is_error = True
                events.append({"type": "result", "name": block.name, "result": result})
                assistant_blocks.append({"type": "tool_use", "id": block.id, "name": block.name, "input": arguments})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    **({"is_error": True} if is_error else {}),
                })

        if tool_results:
            messages.append({"role": "assistant", "content": assistant_blocks})
            messages.append({"role": "user", "content": tool_results})
            continue

        text = "\n".join(part for part in final_text if part.strip()).strip()
        events.append({"type": "final", "text": text or "Completed without visible text."})
        return {"ok": True, "model": DEFAULT_MODEL, "events": events}

    events.append({"type": "error", "message": f"Stopped after {max_steps} model turns."})
    return {"ok": False, "model": DEFAULT_MODEL, "events": events}


def run_study_coach(
    instructions: str,
    task: str,
    quality_prompt: str,
    max_steps: int = 8,
) -> dict[str, Any]:
    """Run the adaptive study coach and append an observable quality review."""
    if not instructions.strip() or not task.strip() or not quality_prompt.strip():
        raise ValueError("instructions, task and quality_prompt are all required")
    result = run_agent(
        instructions,
        task,
        tools=STUDY_COACH_TOOLS,
        max_steps=max_steps,
        max_tokens=1000,
    )
    result = {**result, "events": list(result.get("events", []))}
    if not result.get("ok"):
        return result
    final_text = next(
        (
            event.get("text", "")
            for event in reversed(result["events"])
            if event.get("type") == "final"
        ),
        "",
    )
    if not final_text.strip():
        result["ok"] = False
        result["events"].append({"type": "error", "message": "The study coach returned no study pack to review."})
        return result
    try:
        review = ask_claude(
            "Review a formative study pack against the student's explicit quality criteria. "
            "Return PASS or REVISE followed by concise, observable reasons. Do not rewrite "
            "the pack, reveal hidden reasoning or create assessed work.",
            f"Quality criteria:\n{quality_prompt.strip()}\n\nStudy pack:\n{final_text}",
            max_tokens=500,
        )
    except Exception as exc:
        result["ok"] = False
        result["quality_check"] = None
        result["events"].append({
            "type": "error",
            "message": f"Quality check failed: {type(exc).__name__}: {exc}",
        })
        return result
    result["quality_check"] = review
    result["events"].append({"type": "quality", "text": review})
    return result


def show_trace(result: dict[str, Any], title: str = "OBSERVABLE TRACE") -> None:
    print(f"\n{title}")
    print("-" * len(title))
    labels = {"user": "USER", "tool": "TOOL REQUEST", "result": "TOOL RESULT", "final": "FINAL", "quality": "QUALITY CHECK", "error": "ERROR"}
    for event in result.get("events", []):
        kind = event.get("type", "event")
        print(f"\n[{labels.get(kind, kind.upper())}]")
        if kind == "tool":
            print(f"{event['name']}({json.dumps(event.get('input', {}), indent=2)})")
        elif kind == "result":
            print(json.dumps(event.get("result"), indent=2))
        else:
            print(event.get("text") or event.get("message") or "")


def _document_search(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).strip()
    top_k = max(1, min(5, int(args.get("top_k", 3))))
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    hits = []
    for path in sorted(DATA_DIR.glob("*.txt")):
        if path.name == LEADERSHIP_NOTES.name:
            continue
        text = path.read_text(encoding="utf-8")
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        score = len(terms & words)
        if score:
            hits.append({"source": path.name, "score": score, "text": text[:1800]})
    hits.sort(key=lambda item: (-item["score"], item["source"]))
    return {"query": query, "results": hits[:top_k]}


search_student_docs = Tool(
    "search_student_docs",
    "Search fictional assessment, unit, calendar and room documents. Use this for private workshop knowledge and cite returned filenames.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
        },
        "required": ["query"],
    },
    _document_search,
)


def _specialist(name: str, purpose: str) -> Tool:
    def call(args: dict[str, Any]) -> dict[str, Any]:
        material = str(args.get("material", ""))
        question = str(args.get("question", ""))
        text = ask_claude(
            f"You are the {name} in a student revision workflow. {purpose} "
            "Support the student's thinking and never write assessed work for submission.",
            f"Student question:\n{question}\n\nStudent-provided material:\n{material}",
            max_tokens=700,
        )
        return {"specialist": name, "response": text}

    return Tool(
        name,
        purpose,
        {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "material": {"type": "string"},
            },
            "required": ["question", "material"],
        },
        call,
    )


evidence_retriever = _specialist(
    "evidence_retriever",
    "Identify which supplied passages are relevant and distinguish evidence from interpretation.",
)
rubric_reviewer = _specialist(
    "rubric_reviewer",
    "Evaluate the student's outline against explicit rubric criteria and return questions for revision.",
)
SPECIALISTS = [evidence_retriever, rubric_reviewer]


def run_manager(instructions: str, task: str, max_steps: int = 6) -> dict[str, Any]:
    return run_agent(instructions, task, tools=SPECIALISTS, max_steps=max_steps)
