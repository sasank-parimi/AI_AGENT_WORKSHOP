"""Live server for the UWA AI Club AI Agents workshop deck.

Why this exists:
- The browser slide deck can make real Claude API calls.
- The Anthropic API key remains on the Python server, not in front-end JavaScript.
- One endpoint demonstrates a real Claude tool-use loop using a workshop-only study-room simulator.

Run:
    pip install -r requirements-live.txt
    cp .env.example .env
    # edit .env and add ANTHROPIC_API_KEY
    python server.py

Then open http://localhost:8000
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

MODEL = os.getenv("WORKSHOP_MODEL", "claude-sonnet-5")
API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
MAX_PROMPT_CHARS = int(os.getenv("WORKSHOP_MAX_PROMPT_CHARS", "12000"))
MAX_OUTPUT_TOKENS = int(os.getenv("WORKSHOP_MAX_OUTPUT_TOKENS", "1200"))

app = FastAPI(title="UWA AI Club — Live Agents Workshop")


class ClaudeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)
    system: str = Field(default="", max_length=6000)
    max_tokens: int = Field(default=900, ge=32, le=MAX_OUTPUT_TOKENS)


class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=6000)
    instructions: str = Field(default="", max_length=6000)


def client() -> Anthropic:
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY is not configured. Add it to .env or your shell before starting server.py.",
        )
    return Anthropic(api_key=API_KEY)


@app.get("/")
def deck() -> FileResponse:
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "configured": bool(API_KEY),
        "model": MODEL,
        "live": True,
    }


@app.post("/api/claude/stream")
def claude_stream(req: ClaudeRequest) -> StreamingResponse:
    """Stream Claude's visible text response to the browser.

    The API key is read server-side. The browser receives only generated text.
    """
    c = client()

    def generate():
        try:
            kwargs: dict[str, Any] = {
                "model": MODEL,
                "max_tokens": req.max_tokens,
                "messages": [{"role": "user", "content": req.prompt}],
            }
            if req.system.strip():
                kwargs["system"] = req.system.strip()

            with c.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as exc:  # surfaced as text because streaming may have begun
            yield f"\n\n[Workshop API error: {type(exc).__name__}: {exc}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


STUDY_ROOM_TOOL = {
    "name": "find_study_room",
    "description": (
        "Find simulated university study-room availability for a group. Use this tool when a recommendation "
        "depends on whether a room fits the requested time, group size or accessibility needs. "
        "Results are workshop simulation data, not live university bookings."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Requested date or day, for example next Tuesday"},
            "time": {"type": "string", "description": "Requested start time, for example 15:00"},
            "duration_minutes": {"type": "integer", "description": "Requested duration in minutes", "default": 120},
            "group_size": {"type": "integer", "description": "Number of students who need seats"},
            "accessibility_required": {
                "type": "boolean",
                "description": "Whether step-free access and an accessible route are required",
                "default": False,
            },
        },
        "required": ["date", "time", "group_size"],
    },
}


def find_study_room(
    date: str,
    time: str,
    group_size: int,
    duration_minutes: int = 120,
    accessibility_required: bool = False,
) -> dict[str, Any]:
    """Return deterministic room data so the lesson does not depend on a campus booking system."""
    if os.getenv("WORKSHOP_SIMULATE_ROOM_FAILURE") == "1":
        return {
            "ok": False,
            "error": "Room availability service is temporarily unavailable",
            "source": "UWA AI Club workshop simulator",
            "is_live_booking_data": False,
        }

    size = max(1, int(group_size))
    requested_time = time.strip().lower()
    requested_day = date.strip().lower()
    rooms = [
        {"room": "Bayliss 2.24", "capacity": 8, "accessible": True, "available": "tue" in requested_day and ("3" in requested_time or "15" in requested_time)},
        {"room": "Reid 1.43", "capacity": 6, "accessible": False, "available": True},
        {"room": "Barry J Marshall 5.10", "capacity": 16, "accessible": True, "available": size >= 7},
    ]
    matches = [
        room for room in rooms
        if room["available"]
        and room["capacity"] >= size
        and (not accessibility_required or room["accessible"])
    ]
    if matches:
        return {
            "date": date,
            "time": time,
            "duration_minutes": duration_minutes,
            "group_size": size,
            "accessibility_required": accessibility_required,
            "matches": matches[:3],
            "source": "UWA AI Club workshop simulator",
            "is_live_booking_data": False,
        }
    return {
        "date": date,
        "time": time,
        "duration_minutes": duration_minutes,
        "group_size": size,
        "accessibility_required": accessibility_required,
        "matches": [],
        "suggestion": "Try a different time or reduce the required capacity",
        "source": "UWA AI Club workshop simulator",
        "is_live_booking_data": False,
    }


@app.post("/api/agent/study-session")
def study_session_agent(req: AgentRequest) -> JSONResponse:
    """Run a genuine Claude tool-use loop with one workshop tool.

    The trace returned to the deck contains only observable events:
    user task, tool requests, tool results and final answer.
    """
    c = client()
    instructions = req.instructions.strip() or (
        "You coordinate university study sessions. If a recommendation depends on room availability, capacity "
        "or accessibility, use find_study_room before recommending anything. Clearly label room results as "
        "workshop simulation data and never claim that a room has been booked."
    )

    messages: list[dict[str, Any]] = [{"role": "user", "content": req.task}]
    events: list[dict[str, Any]] = [{"type": "user", "text": req.task}]
    tool_calls = 0

    for _ in range(4):
        response = c.messages.create(
            model=MODEL,
            max_tokens=800,
            system=instructions,
            tools=[STUDY_ROOM_TOOL],
            messages=messages,
        )

        assistant_blocks = []
        tool_results = []
        final_text_parts = []

        for block in response.content:
            if block.type == "text":
                final_text_parts.append(block.text)
                assistant_blocks.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                tool_calls += 1
                tool_input = dict(block.input)
                events.append({
                    "type": "tool",
                    "name": block.name,
                    "input": tool_input,
                })
                if block.name != "find_study_room":
                    result: dict[str, Any] = {"error": f"Unknown tool: {block.name}"}
                    is_error = True
                else:
                    result = find_study_room(
                        date=str(tool_input.get("date", "unspecified")),
                        time=str(tool_input.get("time", "unspecified")),
                        group_size=int(tool_input.get("group_size", 1)),
                        duration_minutes=int(tool_input.get("duration_minutes", 120)),
                        accessibility_required=bool(tool_input.get("accessibility_required", False)),
                    )
                    is_error = not result.get("ok", True)

                events.append({
                    "type": "result",
                    "name": block.name,
                    "result": result,
                })
                assistant_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": tool_input,
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

        final_text = "\n".join(part for part in final_text_parts if part.strip()).strip()
        events.append({"type": "final", "text": final_text or "Claude completed without visible text."})
        return JSONResponse({"ok": True, "model": MODEL, "tool_calls": tool_calls, "events": events})

    events.append({"type": "error", "message": "Agent stopped after the workshop safety limit of 4 model turns."})
    return JSONResponse({"ok": False, "model": MODEL, "tool_calls": tool_calls, "events": events}, status_code=500)


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("\nUWA AI Club — Live AI Agents Workshop")
    print(f"Model: {MODEL}")
    print(f"API key configured: {'yes' if API_KEY else 'NO'}")
    print(f"Open: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
