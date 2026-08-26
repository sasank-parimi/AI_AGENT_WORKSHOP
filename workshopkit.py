"""Inspectable runtime for the UWA AI Agents student workshop.

The notebook builds three independent agents: a Tutor, a Flashcard Generator
and a Study Planner. Each one is fully scaffolded with tools and fictional
course data, so participants focus on writing the instructions. Every tool
call and result is returned as an observable event. Hidden chain-of-thought is
never requested or displayed. All student records and actions are
deterministic workshop data.
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
    """Make one model call and return only its visible text."""
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


def _read_json(filename: str) -> dict[str, Any]:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def _planner_failure(tool_name: str) -> dict[str, Any] | None:
    if os.getenv("WORKSHOP_SIMULATE_PLANNER_FAILURE") == "1":
        return {
            "ok": False,
            "error": f"{tool_name} is temporarily unavailable",
            "source": "workshop simulator",
        }
    return None


def _get_deadlines(args: dict[str, Any]) -> dict[str, Any]:
    failure = _planner_failure("Deadline service")
    if failure:
        return failure
    data = _read_json("student_deadlines.json")
    unit_code = str(args.get("unit_code", "")).strip().upper()
    deadlines = data["deadlines"]
    if unit_code:
        deadlines = [item for item in deadlines if item["unit_code"] == unit_code]
    return {
        "ok": True,
        "as_of": data["as_of"],
        "deadlines": deadlines,
        "source": data["source"],
        "is_live_lms_data": False,
    }


def _get_calendar(args: dict[str, Any]) -> dict[str, Any]:
    failure = _planner_failure("Calendar service")
    if failure:
        return failure
    data = _read_json("student_calendar.json")
    return {"ok": True, **data, "is_live_calendar_data": False}


def _get_current_progress(args: dict[str, Any]) -> dict[str, Any]:
    failure = _planner_failure("Progress service")
    if failure:
        return failure
    data = _read_json("student_progress.json")
    unit_code = str(args.get("unit_code", "")).strip().upper()
    progress = data["progress"]
    if unit_code:
        progress = [item for item in progress if item["unit_code"] == unit_code]
    return {
        "ok": True,
        "progress": progress,
        "source": data["source"],
        "is_live_progress_data": False,
    }


def _estimate_available_hours(args: dict[str, Any]) -> dict[str, Any]:
    failure = _planner_failure("Availability estimator")
    if failure:
        return failure
    calendar = _read_json("student_calendar.json")
    reserve = max(0.0, float(args.get("buffer_hours", 2)))
    total = sum(float(block["hours"]) for block in calendar["available_blocks"])
    return {
        "ok": True,
        "week": calendar["week"],
        "available_hours": total,
        "recommended_buffer_hours": reserve,
        "plannable_hours": max(0.0, total - reserve),
        "available_blocks": calendar["available_blocks"],
        "protected_time": calendar["protected_time"],
        "source": "calculated from fictional workshop calendar data",
    }


def _save_study_plan(args: dict[str, Any]) -> dict[str, Any]:
    plan = args.get("plan")
    if not plan:
        return {"ok": False, "error": "A proposed plan is required"}
    return {
        "ok": True,
        "status": "approval_required",
        "preview": plan,
        "message": "The plan has not been saved. Approval must come from the student outside the model-controlled tool call.",
        "is_real_calendar_action": False,
    }


get_deadlines = Tool(
    "get_deadlines",
    "Read the student's fictional assessment deadlines. Use this before prioritising study work; do not guess dates or weights.",
    {
        "type": "object",
        "properties": {"unit_code": {"type": "string", "description": "Optional unit-code filter"}},
    },
    _get_deadlines,
)

get_calendar = Tool(
    "get_calendar",
    "Read fixed commitments, available study blocks and protected time from the student's fictional calendar.",
    {
        "type": "object",
        "properties": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
    },
    _get_calendar,
)

get_current_progress = Tool(
    "get_current_progress",
    "Read the student's fictional completion estimates and blockers. Use this to avoid treating every deadline as equally unfinished.",
    {
        "type": "object",
        "properties": {"unit_code": {"type": "string", "description": "Optional unit-code filter"}},
    },
    _get_current_progress,
)

estimate_available_hours = Tool(
    "estimate_available_hours",
    "Calculate realistic study capacity from the fictional calendar while reserving buffer and protected time.",
    {
        "type": "object",
        "properties": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
            "buffer_hours": {"type": "number", "default": 2},
        },
    },
    _estimate_available_hours,
)

save_study_plan = Tool(
    "save_study_plan",
    "Preview a study plan and request student approval. This tool never treats a model-provided argument as human approval and does not modify a real calendar.",
    {
        "type": "object",
        "properties": {
            "plan": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["plan"],
    },
    _save_study_plan,
)

PLANNER_TOOLS = [
    get_deadlines,
    get_calendar,
    get_current_progress,
    estimate_available_hours,
    save_study_plan,
]


COURSE_DOCUMENTS = (
    "unit_outline.txt",
    "lecture_04_notes.txt",
    "lecture_05_notes.txt",
    "assignment_rubric.txt",
    "assessment_policy.txt",
    "student_calendar.txt",
)


def _search_course_notes(args: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("WORKSHOP_SIMULATE_RETRIEVAL_FAILURE") == "1":
        return {"ok": False, "error": "Course-document search is temporarily unavailable"}
    query = str(args.get("query", "")).strip()
    top_k = max(1, min(5, int(args.get("top_k", 3))))
    unit_code = str(args.get("unit_code", "")).strip().upper()
    terms = set(re.findall(r"[a-z0-9]+", f"{query} {unit_code}".lower()))
    results: list[dict[str, Any]] = []
    for filename in COURSE_DOCUMENTS:
        text = (DATA_DIR / filename).read_text(encoding="utf-8")
        sections = re.split(r"\n\s*\n", text)
        for index, passage in enumerate(sections):
            words = set(re.findall(r"[a-z0-9]+", passage.lower()))
            score = len(terms & words)
            if score:
                results.append({
                    "source": filename,
                    "passage": index + 1,
                    "score": score,
                    "text": passage.strip(),
                })
    results.sort(key=lambda item: (-item["score"], item["source"], item["passage"]))
    return {
        "ok": True,
        "query": query,
        "unit_code": unit_code or None,
        "results": results[:top_k],
        "source_scope": "fictional workshop documents",
    }


def _get_mastery_record(args: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("WORKSHOP_SIMULATE_RETRIEVAL_FAILURE") == "1":
        return {"ok": False, "error": "Mastery record is temporarily unavailable"}
    data = _read_json("mastery_record.json")
    topic = str(args.get("topic", "")).strip().lower()
    topics = data["topics"]
    if topic:
        matches = {name: score for name, score in topics.items() if topic in name or name in topic}
        if not matches:
            return {"ok": False, "error": f"No mastery record for topic: {topic}"}
        topics = matches
    return {"ok": True, **data, "topics": topics}


FLASHCARD_BANK: dict[str, list[dict[str, str]]] = {
    "leadership styles": [
        {"front": "What does situational leadership say a leader should adjust?", "back": "The style used, based on a follower's readiness: their competence and confidence for the task."},
        {"front": "When does a transactional approach make the most sense?", "back": "For routine, well-defined work where the exchange of effort for reward is clear."},
    ],
    "organisational culture": [
        {"front": "What are artifacts in organisational culture?", "back": "The visible, audible parts of a culture: dress code, office layout, how meetings run."},
        {"front": "Why are basic assumptions the hardest layer of culture to shift?", "back": "People usually aren't consciously aware they hold them, so they're rarely said out loud."},
    ],
    "team dynamics": [
        {"front": "What happens during the storming stage of team development?", "back": "Disagreement surfaces as the team works out roles, expectations and how to handle conflict."},
        {"front": "What can push a team back to an earlier stage?", "back": "A change in membership, or a task that turns out to be harder than expected."},
    ],
}


def _generate_flashcards(args: dict[str, Any]) -> dict[str, Any]:
    topic = str(args.get("topic", "")).strip().lower()
    excerpt = str(args.get("source_excerpt", "")).strip()
    if not excerpt:
        return {"ok": False, "error": "Retrieve a course passage before generating flashcards"}
    cards = next((items for key, items in FLASHCARD_BANK.items() if key in topic or topic in key), None)
    if not cards:
        return {"ok": False, "error": f"No supplied flashcard bank for topic: {topic}"}
    grounding_terms = {
        "leadership styles": ("situational leadership", "transformational", "transactional"),
        "organisational culture": ("organisational culture", "artifacts", "espoused values", "basic assumptions"),
        "team dynamics": ("team dynamics", "tuckman", "forming", "storming", "norming", "performing"),
    }
    matched_topic = next(key for key in FLASHCARD_BANK if key in topic or topic in key)
    if not any(term in excerpt.lower() for term in grounding_terms[matched_topic]):
        return {
            "ok": False,
            "error": f"The retrieved excerpt does not support flashcards about {matched_topic}",
        }
    count = max(1, min(len(cards), int(args.get("count", 2))))
    return {
        "ok": True,
        "topic": topic,
        "cards": cards[:count],
        "status": "self_study_only",
        "grounded_in_supplied_excerpt": True,
    }


search_course_notes = Tool(
    "search_course_notes",
    "Search supplied fictional unit documents and return source-labelled passages. Use this before answering unit-specific questions.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "unit_code": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
        },
        "required": ["query"],
    },
    _search_course_notes,
)

get_mastery_record = Tool(
    "get_mastery_record",
    "Read the student's fictional topic-mastery record so revision can focus on weaker topics.",
    {
        "type": "object",
        "properties": {"topic": {"type": "string", "description": "Optional topic filter"}},
    },
    _get_mastery_record,
)

generate_flashcards = Tool(
    "generate_flashcards",
    "Generate front/back flashcards from a retrieved course passage. This must not create assessed answers.",
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "source_excerpt": {"type": "string"},
            "count": {"type": "integer", "default": 2},
        },
        "required": ["topic", "source_excerpt"],
    },
    _generate_flashcards,
)

TUTOR_TOOLS = [search_course_notes]
FLASHCARD_TOOLS = [search_course_notes, get_mastery_record, generate_flashcards]


def run_agent(
    instructions: str,
    task: str,
    tools: list[Tool] | None = None,
    max_steps: int = 7,
    max_tokens: int = 900,
) -> dict[str, Any]:
    """Run a transparent tool-use loop and return observable events."""
    if not instructions.strip() or not task.strip():
        raise ValueError("instructions and task are required")
    tools = tools or []
    messages: list[dict[str, Any]] = [{"role": "user", "content": task.strip()}]
    events: list[dict[str, Any]] = [{"type": "user", "text": task.strip()}]
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
                assistant_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": arguments,
                })
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


def run_study_planner(instructions: str, task: str) -> dict[str, Any]:
    """Run the Study Planner Agent with the five planning tools."""
    return run_agent(instructions, task, tools=PLANNER_TOOLS, max_steps=7, max_tokens=1000)


def run_tutor_agent(instructions: str, task: str) -> dict[str, Any]:
    """Run the Tutor Agent, which retrieves supplied unit material before answering."""
    return run_agent(instructions, task, tools=TUTOR_TOOLS, max_steps=6, max_tokens=900)


def run_flashcard_agent(instructions: str, task: str) -> dict[str, Any]:
    """Run the Flashcard Generator Agent: check mastery, retrieve, then generate cards."""
    return run_agent(instructions, task, tools=FLASHCARD_TOOLS, max_steps=7, max_tokens=900)


def show_trace(result: dict[str, Any], title: str = "OBSERVABLE TRACE") -> None:
    print(f"\n{title}")
    print("-" * len(title))
    labels = {
        "user": "USER",
        "tool": "TOOL REQUEST",
        "result": "TOOL RESULT",
        "final": "FINAL",
        "error": "ERROR",
    }
    for event in result.get("events", []):
        kind = event.get("type", "event")
        print(f"\n[{labels.get(kind, kind.upper())}]")
        if kind == "tool":
            print(f"{event['name']}({json.dumps(event.get('input', {}), indent=2)})")
        elif kind == "result":
            print(json.dumps(event.get("result"), indent=2))
        else:
            print(event.get("text") or event.get("message") or "")


def _specialist(name: str, purpose: str) -> Tool:
    def call(args: dict[str, Any]) -> dict[str, Any]:
        material = str(args.get("material", ""))
        question = str(args.get("question", ""))
        response = ask_claude(
            f"You are the {name} specialist supporting one Student Agent. {purpose} "
            "Use only supplied material, name uncertainty and never produce assessed work for submission.",
            f"Student question:\n{question}\n\nSupplied material:\n{material}",
            max_tokens=700,
        )
        return {"ok": True, "specialist": name, "response": response}

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


researcher = _specialist(
    "researcher",
    "Compare supplied sources, identify evidence and gaps, and suggest useful next searches without inventing citations.",
)
planner = _specialist(
    "planner",
    "Turn known deadlines, progress and capacity into a realistic sequence of student-owned next steps.",
)
reviewer = _specialist(
    "reviewer",
    "Evaluate a student's own draft or plan against explicit criteria and return revision questions.",
)
SPECIALISTS = [researcher, planner, reviewer]


def run_manager(instructions: str, task: str, max_steps: int = 7) -> dict[str, Any]:
    """Let the Student Agent delegate only when specialist work is justified."""
    return run_agent(instructions, task, tools=SPECIALISTS, max_steps=max_steps, max_tokens=1000)


# A readable alias for the retrieval exercise.
search_student_docs = search_course_notes


# NVIDIA capstone research and grounded-generation helpers.
FALLBACK_PATH = DATA_DIR / "nvidia_research_fallback.md"
DEFAULT_MAX_SEARCHES = 3
MAX_SEARCHES = 5
RESEARCH_QUESTION = (
    "What are NVIDIA's strongest evidence-backed growth drivers and material "
    "business risks over the next 12-24 months, as of today?"
)

def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_none=True)
    if hasattr(value, "__dict__"):
        return {key: item for key, item in vars(value).items() if not key.startswith("_")}
    return {}


def _usage_dict(response: Any) -> dict[str, Any]:
    usage = _as_dict(getattr(response, "usage", {}))
    server = usage.get("server_tool_use") or {}
    if not isinstance(server, dict):
        server = _as_dict(server)
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "web_search_requests": server.get("web_search_requests", 0),
    }


def _merge_usage(total: dict[str, int], current: dict[str, Any]) -> None:
    for key in total:
        total[key] += int(current.get(key, 0) or 0)


def extract_visible_content(response: Any) -> tuple[str, list[dict[str, str]], list[dict[str, Any]]]:
    """Extract visible text, deduplicated sources and observable searches."""
    text_parts: list[str] = []
    sources: dict[str, dict[str, str]] = {}
    events: list[dict[str, Any]] = []

    for raw_block in getattr(response, "content", []):
        block = _as_dict(raw_block)
        kind = block.get("type") or getattr(raw_block, "type", "")
        if kind == "text":
            visible = block.get("text") or getattr(raw_block, "text", "")
            if visible:
                text_parts.append(str(visible))
            citations = block.get("citations") or getattr(raw_block, "citations", []) or []
            for raw_citation in citations:
                citation = _as_dict(raw_citation)
                url = str(citation.get("url", "")).strip()
                if url:
                    sources[url] = {
                        "title": str(citation.get("title") or url),
                        "url": url,
                        "date": str(citation.get("page_age") or citation.get("date") or "Date not supplied"),
                    }
        elif kind in {"server_tool_use", "tool_use"}:
            name = str(block.get("name", ""))
            if name == "web_search":
                tool_input = block.get("input") or {}
                events.append({"type": "search", "query": str(tool_input.get("query") or tool_input)})
        elif kind == "web_search_tool_result":
            result_content = block.get("content") or []
            if isinstance(result_content, dict):
                result_content = [result_content]
            for raw_result in result_content:
                result = _as_dict(raw_result)
                url = str(result.get("url", "")).strip()
                if url:
                    sources[url] = {
                        "title": str(result.get("title") or url),
                        "url": url,
                        "date": str(result.get("page_age") or result.get("date") or "Date not supplied"),
                    }
    return "\n".join(text_parts).strip(), list(sources.values()), events


def _fallback_result(task: str, message: str) -> dict[str, Any]:
    fallback = FALLBACK_PATH.read_text(encoding="utf-8")
    return {
        "ok": True,
        "model": DEFAULT_MODEL,
        "events": [
            {"type": "user", "text": task},
            {"type": "error", "message": message},
            {"type": "final", "text": fallback, "label": "DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH"},
        ],
        "sources": [],
        "usage": {"input_tokens": 0, "output_tokens": 0, "web_search_requests": 0},
        "fallback_used": True,
        "stop_reason": "fallback",
        "text": fallback,
    }


def run_research_agent(
    system_prompt: str,
    task: str = RESEARCH_QUESTION,
    max_searches: int = DEFAULT_MAX_SEARCHES,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run one bounded server-tool research turn and expose its evidence trail."""
    if not system_prompt.strip() or not task.strip():
        raise ValueError("system_prompt and task are required")
    bounded_searches = max(1, min(int(max_searches), MAX_SEARCHES))
    tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": bounded_searches}
    messages: list[dict[str, Any]] = [{"role": "user", "content": task.strip()}]
    events: list[dict[str, Any]] = [{"type": "user", "text": task.strip()}]
    sources_by_url: dict[str, dict[str, str]] = {}
    visible_parts: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0, "web_search_requests": 0}

    try:
        api = client or _client()
        for _ in range(3):
            response = api.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1800,
                system=system_prompt.strip(),
                tools=[tool],
                messages=messages,
            )
            text, sources, response_events = extract_visible_content(response)
            events.extend(response_events)
            if text:
                visible_parts.append(text)
            for source in sources:
                sources_by_url[source["url"]] = source
            _merge_usage(usage, _usage_dict(response))
            stop_reason = str(getattr(response, "stop_reason", "end_turn"))
            if stop_reason != "pause_turn":
                final_text = "\n".join(visible_parts).strip()
                if not final_text:
                    return _fallback_result(task, "Live research returned no visible text; the dated fallback was loaded.")
                source_list = list(sources_by_url.values())
                events.extend({"type": "source", **source} for source in source_list)
                events.append({"type": "final", "text": final_text})
                events.append({"type": "usage", **usage, "stop_reason": stop_reason})
                return {
                    "ok": True,
                    "model": DEFAULT_MODEL,
                    "events": events,
                    "sources": source_list,
                    "usage": usage,
                    "fallback_used": False,
                    "stop_reason": stop_reason,
                    "text": final_text,
                }
            messages.append({"role": "assistant", "content": getattr(response, "content", [])})
        return _fallback_result(task, "Live research remained paused after the retry limit; the dated fallback was loaded.")
    except Exception as exc:
        return _fallback_result(task, f"Live research unavailable ({type(exc).__name__}); the dated fallback was loaded.")


def run_briefing_editor(
    system_prompt: str,
    research: str | dict[str, Any],
    task: str = "Create the one-page NVIDIA investor briefing.",
    client: Any | None = None,
) -> dict[str, Any]:
    """Make one grounded generation call. No tools or autonomous loop are used."""
    if isinstance(research, dict):
        research_text = str(research.get("text", ""))
        sources = list(research.get("sources", []))
        fallback_used = bool(research.get("fallback_used"))
    else:
        research_text = str(research)
        sources = []
        fallback_used = False
    if not system_prompt.strip() or not research_text.strip():
        raise ValueError("system_prompt and research are required")
    api = client or _client()
    prompt = (
        f"TASK\n{task.strip()}\n\nVERIFIED RESEARCH\n{research_text}\n\n"
        f"SOURCE METADATA\n{json.dumps(sources, indent=2)}"
    )
    response = api.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1300,
        system=system_prompt.strip(),
        messages=[{"role": "user", "content": prompt}],
    )
    text, _, _ = extract_visible_content(response)
    if not text:
        raise RuntimeError("Briefing Editor returned no visible text")
    usage = _usage_dict(response)
    return {
        "ok": True,
        "model": DEFAULT_MODEL,
        "text": text,
        "sources": sources,
        "usage": usage,
        "fallback_used": fallback_used,
        "stop_reason": str(getattr(response, "stop_reason", "end_turn")),
        "events": [
            {"type": "user", "text": task},
            {"type": "final", "text": text},
            {"type": "usage", **usage},
        ],
    }


def show_result(result: dict[str, Any]) -> None:
    """Print a compact result and its observable evidence trail."""
    if result.get("fallback_used"):
        print("\n!!! DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH !!!")
    for event in result.get("events", []):
        kind = event.get("type", "event").upper()
        print(f"\n[{kind}]")
        if event.get("type") == "search":
            print(event.get("query", ""))
        elif event.get("type") == "source":
            print(f"{event.get('title')} | {event.get('url')} | {event.get('date')}")
        elif event.get("type") == "usage":
            print(json.dumps({key: value for key, value in event.items() if key != "type"}, indent=2))
        else:
            print(event.get("text") or event.get("message") or "")


def score_output(output: str, checklist: list[str]) -> dict[str, Any]:
    """Interactive self-check: learners decide which visible criteria are met."""
    print("Read the output, then answer y or n for each check.\n")
    checks: list[dict[str, Any]] = []
    for criterion in checklist:
        answer = input(f"{criterion} [y/n]: ").strip().lower()
        checks.append({"criterion": criterion, "passed": answer.startswith("y")})
    passed = sum(int(item["passed"]) for item in checks)
    result = {"score": passed, "total": len(checks), "checks": checks}
    print(f"\nScore: {passed}/{len(checks)}")
    return result
