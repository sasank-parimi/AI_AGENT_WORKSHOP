"""Inspectable runtime for the UWA AI Agents student workshop.

The notebook builds one Student Agent and progressively gives it planning,
retrieval, revision and specialist capabilities. Every tool call and result is
returned as an observable event. Hidden chain-of-thought is never requested or
displayed. All student records and actions are deterministic workshop data.
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


QUIZ_BANK: dict[str, list[dict[str, str]]] = {
    "graph traversal": [
        {"question": "When does breadth-first search guarantee a shortest path?", "check_for": "An unweighted graph, with distance measured in edges."},
        {"question": "What does O(V + E) assume about the graph representation?", "check_for": "An adjacency-list representation."},
    ],
    "shortest paths": [
        {"question": "Why can Dijkstra's algorithm fail with a negative edge?", "check_for": "Its greedy settled choice may later be improved."},
        {"question": "Which algorithm would you choose for an unweighted shortest-path problem, and why?", "check_for": "Breadth-first search because it explores by edge distance."},
    ],
    "dynamic programming": [
        {"question": "What two properties suggest a dynamic-programming approach?", "check_for": "Overlapping subproblems and optimal substructure."},
        {"question": "What should a state definition make explicit?", "check_for": "The information needed to describe a subproblem."},
    ],
}


def _generate_quiz(args: dict[str, Any]) -> dict[str, Any]:
    topic = str(args.get("topic", "")).strip().lower()
    excerpt = str(args.get("source_excerpt", "")).strip()
    if not excerpt:
        return {"ok": False, "error": "Retrieve a course passage before generating a quiz"}
    questions = next((items for key, items in QUIZ_BANK.items() if key in topic or topic in key), None)
    if not questions:
        return {"ok": False, "error": f"No supplied quiz bank for topic: {topic}"}
    grounding_terms = {
        "graph traversal": ("breadth-first", "graph traversal", "adjacency"),
        "shortest paths": ("dijkstra", "shortest path", "edge weight"),
        "dynamic programming": ("dynamic programming", "subproblem", "optimal substructure"),
    }
    matched_topic = next(key for key in QUIZ_BANK if key in topic or topic in key)
    if not any(term in excerpt.lower() for term in grounding_terms[matched_topic]):
        return {
            "ok": False,
            "error": f"The retrieved excerpt does not support a quiz about {matched_topic}",
        }
    count = max(1, min(len(questions), int(args.get("count", 2))))
    return {
        "ok": True,
        "topic": topic,
        "questions": questions[:count],
        "status": "formative_practice_only",
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

generate_quiz = Tool(
    "generate_quiz",
    "Generate formative questions from a retrieved course passage. This must not create assessed answers.",
    {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "source_excerpt": {"type": "string"},
            "count": {"type": "integer", "default": 2},
        },
        "required": ["topic", "source_excerpt"],
    },
    _generate_quiz,
)

STUDY_UPGRADE_TOOLS = [search_course_notes, get_mastery_record, generate_quiz]
STUDENT_AGENT_TOOLS = PLANNER_TOOLS + STUDY_UPGRADE_TOOLS


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


def run_student_planner(instructions: str, task: str) -> dict[str, Any]:
    """Run Mission 1 with the five planning tools."""
    return run_agent(instructions, task, tools=PLANNER_TOOLS, max_steps=7, max_tokens=1000)


def run_revision_upgrade(instructions: str, task: str) -> dict[str, Any]:
    """Run the same Student Agent with planning, retrieval and quiz tools."""
    return run_agent(instructions, task, tools=STUDENT_AGENT_TOOLS, max_steps=8, max_tokens=1000)


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
