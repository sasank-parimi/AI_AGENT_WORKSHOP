# UWA AI Club — AI Agents Workshop V1

A beginner-friendly, two-hour workshop designed around **interaction first** rather than slide-heavy lecturing.

The learning spine is:

**prompt → context → tools → agent loop → multi-agent → RAG → MCP → Claude Managed Agents → system architecture**

## What is included

- `index.html` — built, self-contained interactive slide deck with the UWA AI Club palette, logo and Marv mascot embedded.
- `AI_AGENTS_WORKSHOP.ipynb` — participant notebook. Real Claude API calls; tool schemas, loops and traces are prebuilt.
- `workshopkit/` — the hidden plumbing for Claude calls, tool execution, agent traces, RAG and specialist-agent orchestration.
- `data/` — workshop-only mock club policies and room information for the RAG exercise.
- `instructor/AI_AGENTS_WORKSHOP_SOLUTION.ipynb` — filled example prompts for the instructor.
- `instructor/MANAGED_AGENTS_DEMO.ipynb` — isolated Managed Agents demo.
- `instructor/mcp_demo/` — current MCP Python SDK v2 workshop server.
- `FACILITATOR_GUIDE.md` — timing, transitions and contingency cuts.


## Live Claude inside the HTML deck

The deck now supports **real API calls directly from the interactive slides**. Participants can type or edit prompts in the deck, press **ASK CLAUDE**, and watch the response stream into the slide. The first tool-use demo also runs a real Claude tool-selection loop and renders the observable tool request/result trace.

Do **not** open `index.html` directly if you want live calls. Run the small Python server so the Anthropic key stays server-side:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-live.txt
cp .env.example .env
# edit .env and paste the workshop-only ANTHROPIC_API_KEY
python server.py
```

Then open:

```text
http://localhost:8000
```

The top-left status pill should read **LIVE CLAUDE · claude-sonnet-5**. If it says **LIVE API OFFLINE**, the rest of the deck still works but the live-generation controls will not.

### What is live in V2

- **Cold open:** type any job and get a real Claude response.
- **Prompt Builder:** toggle prompt ingredients, edit the assembled prompt, then run it against Claude.
- **Prompt Surgery:** participants rewrite a weak prompt and compare actual outputs immediately.
- **Tool-use trace:** edit the agent instructions/task and run a real Messages API tool loop. Claude decides whether to request `get_weather`; Python executes the workshop simulator and returns the tool result.

The weather tool is intentionally deterministic workshop data, not a live forecast. This keeps the lesson focused on tool selection rather than another external API dependency.

### Recommended workshop deployment

For a room of participants, the cleanest setup is to host `server.py` once and share the workshop URL. Your Anthropic key remains on the server, so students never need to see or paste it into the HTML deck. Use a workshop-specific key/spend limit and shut the server down after the event.

### Deploy on Vercel

This repository is ready for Vercel's FastAPI runtime. Vercel detects the `app` exported by `server.py`; the presentation stays at `/`, and its existing same-origin API calls continue to use `/api/health`, `/api/claude/stream`, and `/api/agent/weather`.

1. Push this folder to a GitHub repository.
2. In Vercel, choose **Add New → Project** and import that repository.
3. Keep the detected project settings and root directory unchanged.
4. Add `ANTHROPIC_API_KEY` under **Settings → Environment Variables** for Production, Preview, and Development as needed.
5. Optionally add `WORKSHOP_MODEL=claude-sonnet-5` and the two `WORKSHOP_MAX_*` guardrails shown in `.env.example`.
6. Deploy, open the assigned URL, and confirm the top-left status pill says **LIVE CLAUDE · claude-sonnet-5**.

Do not upload a populated `.env` file or expose the key in browser JavaScript. The included `.gitignore` excludes local environment files and Vercel's local project metadata.

## Slide deck

For **static/fallback presentation mode**, open `index.html` directly in a browser; the non-API interactions still work and the supplied logo/mascot are inlined. For the intended **live Claude mode**, run `server.py` and open `http://localhost:8000`.

Controls:

- `←` / `→` — navigate
- `Space` — next
- `F` — fullscreen
- `N` — presenter notes for the current slide
- URL hash — deep-link to a slide, e.g. `index.html#20`

### Rebuild after editing source

```bash
python3 build.py
```

Source layout:

```text
src/index.html
src/css/
src/js/
src/slides/
src/assets/
build.py
```

The build script is Python stdlib only. It concatenates the CSS/JS/slides and base64-inlines the images into `index.html`.

## Participant notebook setup

From the repository root:

```bash
pip install -r requirements.txt
jupyter lab AI_AGENTS_WORKSHOP.ipynb
```

The notebook asks for the workshop API key with `getpass()`, so the key is not written into the notebook file.

The default model is set in one place through `WORKSHOP_MODEL` and currently defaults to `claude-sonnet-5`. If the workshop key has access to another model, change the setup cell or set the environment variable before import.

## API design

The core participant notebook uses the Claude **Messages API** and user-defined tools. Claude returns structured tool requests; the local workshop runtime executes the Python functions and returns tool results to Claude. The trace displays observable actions and results, not hidden chain-of-thought.

The Managed Agents material is kept separate because it is currently a beta surface and is more likely to change than the core Messages API exercises.

## MCP demo

Current MCP Python SDK v2:

```bash
pip install "mcp[cli]>=2,<3"
mcp dev instructor/mcp_demo/server.py
```

The server exposes workshop-only tools/resources/prompts and touches no real UWA systems.

## Technical references checked for this V1 (25 Aug 2026)

- Anthropic Prompting Best Practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic Tool Use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Anthropic Building Effective Agents: https://www.anthropic.com/engineering/building-effective-agents
- Anthropic Effective Context Engineering for AI Agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Claude Managed Agents Quickstart: https://platform.claude.com/docs/en/managed-agents/quickstart
- Claude Managed Agents Overview: https://platform.claude.com/docs/en/managed-agents/overview
- MCP Python SDK v2: https://github.com/modelcontextprotocol/python-sdk

## Design references

The source/build philosophy is intentionally influenced by the earlier UWA AI Club Local AI workshop: self-contained HTML, modular editable source, projector legibility, and interactions that encode a teaching point rather than decorate it.

The visual system for this deck is original to this workshop and uses the supplied UWA AI Club logo and Marv artwork.
