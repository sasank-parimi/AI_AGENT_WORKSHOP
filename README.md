# AI Agents for an ordinary student week

An interactive UWA AI Club workshop that teaches prompting, context, tools, agent loops, retrieval, orchestration, MCP and human approval through three recurring student stories.

- **Maya:** prioritising four assessments around work shifts.
- **Noah:** coordinating an accessible group-project meeting.
- **Priya:** retrieving unit material and reviewing her own essay outline.

The presentation makes real Claude API calls and shows observable tool requests and results. All room, calendar, policy and action data is fictional workshop simulation data.

## Project structure

- index.html — self-contained interactive presentation and presenter notes.
- server.py — FastAPI server for the presentation and server-side Claude calls.
- AI_AGENTS_WORKSHOP.ipynb — participant exercises matching the presentation.
- workshopkit.py — small, inspectable notebook runtime and simulated tools.
- data/ — fictional assessment, unit, calendar and room documents for retrieval.
- FACILITATOR_GUIDE.md — 120-minute run sheet and teaching notes.
- requirements-live.txt — dependencies for the live presentation.
- requirements.txt — dependencies for the participant notebook.

## Run the live presentation

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-live.txt
    cp .env.example .env
    # Add a workshop-only ANTHROPIC_API_KEY to .env
    python server.py

Open http://localhost:8000.

The root `.env` is loaded by both the participant notebook and a locally running `server.py`. The API key stays in Python and is never included in browser JavaScript. Editing `.env` is picked up on the next API request.

For a deployed website, `.env` is intentionally ignored and is not uploaded. Set a valid Anthropic `ANTHROPIC_API_KEY` in the hosting provider's environment settings, then redeploy. The live-slide status checks whether Anthropic accepts that credential; a non-empty but invalid key is shown as **API KEY REJECTED**.

Presentation controls:

- Left/right arrows or Space — navigate.
- Home / End — first or last slide.
- F — fullscreen.
- N — presenter notes.
- Contents — overview navigator.
- URL hash — deep-link to a presentation state, for example #20.

If the API is unavailable, navigation and non-API interactions still work. Live-call slides show an explicit offline state.

## Run the participant notebook

    source .venv/bin/activate
    pip install -r requirements.txt
    jupyter lab AI_AGENTS_WORKSHOP.ipynb

The notebook loads `ANTHROPIC_API_KEY` from the root `.env`. If it is missing, the setup cell requests it through `getpass()` instead. It then imports the local `workshopkit.py`.

## Live API

### GET /api/health

Reports whether the live server is running, whether an API key is configured and which model is selected.

### POST /api/claude/stream

Streams visible model text. Request fields are prompt, optional system instructions and max_tokens.

### POST /api/agent/study-session

Runs a real Claude tool-selection loop with the deterministic find_study_room workshop tool. The request keeps the existing task and instructions fields.

The response contains only observable user, tool, result, final and error events. Room availability is always labelled as simulated and the tool never books a room.

Set WORKSHOP_SIMULATE_ROOM_FAILURE=1 to return a controlled room-service failure.

## Deploy on Vercel

The included vercel.json uses Vercel's FastAPI runtime. Add ANTHROPIC_API_KEY as a project environment variable and deploy the project root. Optionally set WORKSHOP_MODEL, WORKSHOP_MAX_PROMPT_CHARS and WORKSHOP_MAX_OUTPUT_TOKENS.

Use a workshop-specific API key with appropriate spending limits and disable it after the event.

## Design and accessibility

The deck uses a warm workshop-notebook visual system with editorial typography, varied compositions and restrained annotations. Local fonts are preferred from fonts/; the CSS includes readable system fallbacks.

The presentation supports keyboard-only navigation, visible focus states, reduced motion, responsive layouts and print output. Verify the final venue projector at 1366×768 and 1920×1080 before delivery.
