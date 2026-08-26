"""Inspectable runtime for the AI Agent Research Lab.

Stage one is a tool-using Research Agent. Stage two is a grounded, single-call
Briefing Editor. Only observable API content is returned.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
FALLBACK_PATH = ROOT / "data" / "nvidia_research_fallback.md"
load_dotenv(ROOT / ".env", override=True)

DEFAULT_MODEL = os.getenv("WORKSHOP_MODEL", "claude-sonnet-5")
DEFAULT_MAX_SEARCHES = 3
MAX_SEARCHES = 5
RESEARCH_QUESTION = (
    "What are NVIDIA's strongest evidence-backed growth drivers and material "
    "business risks over the next 12-24 months, as of today?"
)


def _client() -> Anthropic:
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env", override=True)
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    return Anthropic(api_key=key)


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
