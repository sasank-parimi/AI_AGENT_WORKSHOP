# AI Agents Workshop

An interactive beginner workshop that teaches CRAFT prompting, context engineering, tools, agent loops, retrieval, multi-agent systems, MCP and human approval, then has participants build three agents of their own: a Tutor, a Flashcard Generator and a Study Planner.

Each agent is fully scaffolded with tools and fictional commerce-unit course data (Leadership and Organisational Behaviour, Financial Accounting, Marketing, Business Communication), so participants mainly write the CRAFT instructions and watch the agent's tool calls in an observable trace.

The presentation makes real Claude API calls and shows observable tool requests and results. All calendar, deadline, progress, course-document and action data is fictional workshop simulation data.

## Project structure

- index.html: self-contained interactive presentation.
- server.py: FastAPI server for the presentation and server-side Claude calls.
- AI_AGENTS_WORKSHOP.ipynb: participant exercises matching the presentation.
- workshopkit.py: small, inspectable notebook runtime and simulated tools.
- data/: fictional deadlines, calendar, progress, course notes, rubric and mastery data for the workshop's commerce units.
- FACILITATOR_GUIDE.md: run sheet and teaching notes.
- requirements-live.txt: dependencies for the live presentation.
- requirements.txt: dependencies for the participant notebook.

## Run the live presentation

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-live.txt
    cp .env.example .env
    # Add a workshop-only ANTHROPIC_API_KEY to .env
    python server.py

Open http://localhost:8000.

The root `.env` is loaded by the participant notebook and by `server.py` only when the website runs locally. The API key stays in Python and is never included in browser JavaScript. Editing `.env` is picked up on the next local API request.

For a deployed website, `.env` is intentionally ignored and is not uploaded. Set a valid Anthropic `ANTHROPIC_API_KEY` in the hosting provider's environment settings, then redeploy. The live-slide status checks whether Anthropic accepts that credential; a non-empty but invalid key is shown as **API KEY REJECTED**.

Presentation controls:

- Left/right arrows or Space: navigate.
- Home / End: first or last slide.
- F: fullscreen.
- Contents: overview navigator.
- URL hash: deep-link to a presentation state, for example #20.

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

Runs a real Claude tool-selection loop with deterministic Student Planner tools: `get_deadlines`, `get_calendar`, `get_current_progress`, `estimate_available_hours` and approval-gated `save_study_plan`. The request retains the `task` and `instructions` fields.

The response contains only observable user, tool, result, final and error events. Workshop tools never modify a real LMS, calendar or student record.

Set `WORKSHOP_SIMULATE_PLANNER_FAILURE=1` for a controlled planning-data failure or `WORKSHOP_SIMULATE_RETRIEVAL_FAILURE=1` for a controlled course-search failure.

## Deploy on Vercel

The included vercel.json uses Vercel's FastAPI runtime. Add ANTHROPIC_API_KEY as a project environment variable and deploy the project root. Optionally set WORKSHOP_MODEL, WORKSHOP_MAX_PROMPT_CHARS and WORKSHOP_MAX_OUTPUT_TOKENS.

Use a workshop-specific API key with appropriate spending limits and disable it after the event.

## Design and accessibility

The deck uses a warm workshop-notebook visual system with editorial typography, varied compositions and restrained annotations. Local fonts are preferred from fonts/; the CSS includes readable system fallbacks.

The presentation supports keyboard-only navigation, visible focus states, reduced motion, responsive layouts and print output. Verify the final venue projector at 1366×768 and 1920×1080 before delivery.
