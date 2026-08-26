"""FastAPI server for the AI Agent Research Lab deck."""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

MODEL = os.getenv("WORKSHOP_MODEL", workshopkit.DEFAULT_MODEL)
MAX_PROMPT_CHARS = int(os.getenv("WORKSHOP_MAX_PROMPT_CHARS", "16000"))
MAX_OUTPUT_TOKENS = int(os.getenv("WORKSHOP_MAX_OUTPUT_TOKENS", "1800"))

app = FastAPI(title="AI Agent Research Lab")


class ClaudeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_CHARS)
    system: str = Field(default="", max_length=8000)
    max_tokens: int = Field(default=900, ge=32, le=MAX_OUTPUT_TOKENS)


class ResearchRequest(BaseModel):
    task: str = Field(min_length=1, max_length=8000)
    instructions: str = Field(min_length=1, max_length=8000)
    max_searches: int = Field(default=3, ge=1, le=workshopkit.MAX_SEARCHES)


def api_key() -> str:
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
            detail="ANTHROPIC_API_KEY is not configured. Add it to .env locally or the host environment.",
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
            result.update({"ok": False, "authenticated": False, "error": "Anthropic rejected the configured API key."})
        except Exception:
            result["validation_unavailable"] = True
    return result


@app.post("/api/claude/stream")
def claude_stream(req: ClaudeRequest) -> StreamingResponse:
    """Stream one non-agentic generation response."""
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
                yield from stream.text_stream
        except AuthenticationError:
            yield "\n\n[API authentication failed. Replace ANTHROPIC_API_KEY and try again.]"
        except Exception as exc:
            yield f"\n\n[Workshop API error: {type(exc).__name__}: {exc}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8", headers={"Cache-Control": "no-store"})


@app.post("/api/agent/research")
def research_agent(req: ResearchRequest) -> JSONResponse:
    """Run bounded live research and return only visible searches, sources and output."""
    # Let the runtime load the dated fallback even when credentials are missing.
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
    return JSONResponse(status_code=401, content={"detail": "Anthropic rejected the configured API key."})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("\nAI Agent Research Lab")
    print(f"Model: {MODEL}")
    print(f"API key configured: {'yes' if api_key() else 'NO'} ({credential_source()})")
    print(f"Open: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
