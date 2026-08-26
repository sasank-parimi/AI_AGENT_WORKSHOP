"""Live server for the UWA AI Club AI Agents workshop deck.

Why this exists:
- The browser slide deck can make real Claude API calls.
- The Anthropic API key remains on the Python server, not in front-end JavaScript.
- One endpoint demonstrates a real Claude tool-use loop using deterministic student-planning data.

Run:
    pip install -r requirements.txt
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

from anthropic import Anthropic, AuthenticationError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

import workshopkit
from workshopkit import PLANNER_TOOLS

ROOT = Path(__file__).resolve().parent
# A local .env is the source of truth for notebooks and local presentation
# runs. Hosted deployments do not contain this ignored file and use the
# platform's environment variables instead.
load_dotenv(ROOT / ".env", override=True)

MODEL = os.getenv("WORKSHOP_MODEL", "claude-sonnet-5")
MAX_PROMPT_CHARS = int(os.getenv("WORKSHOP_MAX_PROMPT_CHARS", "12000"))
MAX_OUTPUT_TOKENS = int(os.getenv("WORKSHOP_MAX_OUTPUT_TOKENS", "1200"))

app = FastAPI(title="AI Agents Workshop: Live Server")


class ClaudeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)
    system: str = Field(default="", max_length=6000)
    max_tokens: int = Field(default=900, ge=32, le=MAX_OUTPUT_TOKENS)


class AgentRequest(BaseModel):
    task: str = Field(min_length=1, max_length=6000)
    instructions: str = Field(default="", max_length=6000)


class ResearchRequest(BaseModel):
    task: str = Field(min_length=1, max_length=8000)
    instructions: str = Field(min_length=1, max_length=8000)
    max_searches: int = Field(default=3, ge=1, le=workshopkit.MAX_SEARCHES)


def api_key() -> str:
    """Reload local workshop credentials so editing .env does not require a restart."""
    if (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env", override=True)
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def credential_source() -> str:
    return "local .env" if (ROOT / ".env").exists() else "host environment"


def client() -> Anthropic:
    key = api_key()
    if not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "ANTHROPIC_API_KEY is not configured. Add it to the project .env for local use, "
                "or to the hosting provider's environment variables for a deployed website."
            ),
        )
    return Anthropic(api_key=key)


@app.get("/")
def deck() -> FileResponse:
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/api/health")
def health(validate: bool = False) -> dict[str, Any]:
    key = api_key()
    result: dict[str, Any] = {
        "ok": True,
        "configured": bool(key),
        "authenticated": None,
        "credential_source": credential_source(),
        "model": MODEL,
        "live": True,
        "web_search_max": workshopkit.MAX_SEARCHES,
    }
    if validate and key:
        try:
            Anthropic(api_key=key).models.list(limit=1)
            result["authenticated"] = True
        except AuthenticationError:
            result.update({
                "ok": False,
                "authenticated": False,
                "error": (
                    "Anthropic rejected the configured API key. Replace it in .env locally "
                    "or in the deployed site's environment settings."
                ),
            })
        except Exception:
            # Authentication could not be checked, but a temporary network or
            # provider problem should not be misreported as an invalid key.
            result["validation_unavailable"] = True
    return result


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
        except AuthenticationError:
            yield (
                "\n\n[Website API authentication failed. Anthropic rejected the configured key. "
                "Replace ANTHROPIC_API_KEY in the local .env or the deployed site's environment settings.]"
            )
        except Exception as exc:  # surfaced as text because streaming may have begun
            yield f"\n\n[Workshop API error: {type(exc).__name__}: {exc}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/agent/study-session")
def study_session_agent(req: AgentRequest) -> JSONResponse:
    """Run a genuine Student Agent loop with deterministic planning tools.

    The trace returned to the deck contains only observable events:
    user task, tool requests, tool results and final answer.
    """
    c = client()
    instructions = req.instructions.strip() or (
        "You are a Student Planning Agent. Inspect deadlines, calendar, current progress and available hours "
        "before prioritising the week. Protect rest and include buffer. Do not invent student data or assessed "
        "content. Never save a plan or create calendar blocks without explicit student approval."
    )

    messages: list[dict[str, Any]] = [{"role": "user", "content": req.task}]
    events: list[dict[str, Any]] = [{"type": "user", "text": req.task}]
    tool_calls = 0

    definitions = [tool.api_definition() for tool in PLANNER_TOOLS]
    tools_by_name = {tool.name: tool for tool in PLANNER_TOOLS}

    for _ in range(7):
        response = c.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=instructions,
            tools=definitions,
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
                tool = tools_by_name.get(block.name)
                if tool is None:
                    result: dict[str, Any] = {"ok": False, "error": f"Unknown tool: {block.name}"}
                    is_error = True
                else:
                    try:
                        result = tool.execute(tool_input)
                        is_error = isinstance(result, dict) and result.get("ok") is False
                    except Exception as exc:
                        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                        is_error = True

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

    events.append({"type": "error", "message": "Agent stopped after the workshop safety limit of 7 model turns."})
    return JSONResponse({"ok": False, "model": MODEL, "tool_calls": tool_calls, "events": events}, status_code=500)


@app.post("/api/agent/research")
def research_agent(req: ResearchRequest) -> JSONResponse:
    """Run the bounded NVIDIA capstone research agent.

    The response contains only observable searches, sources, visible model text,
    usage and errors. Missing or rejected credentials activate the explicitly
    dated classroom fallback instead of stopping the notebook exercise.
    """
    research_client = Anthropic(api_key=api_key()) if api_key() else None
    result = workshopkit.run_research_agent(
        req.instructions,
        req.task,
        max_searches=req.max_searches,
        client=research_client,
    )
    return JSONResponse(result)


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(AuthenticationError)
def authentication_exception_handler(_, __: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "detail": (
                "Anthropic rejected the configured API key. Replace ANTHROPIC_API_KEY "
                "in the local .env or the deployed site's environment settings."
            )
        },
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("\nAI Agents Workshop: Live Server")
    print(f"Model: {MODEL}")
    print(f"API key configured: {'yes' if api_key() else 'NO'} ({credential_source()})")
    print(f"Open: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
