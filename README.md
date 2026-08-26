# AI Agents Workshop

A complete two-hour, beginner-friendly workshop covering prompt engineering, CRAFT, context engineering, API anatomy, agent loops, tools, human approval, retrieval, multi-agent systems, evaluation and MCP.

The NVIDIA notebook is the applied capstone, not the whole workshop:

1. A **Research Agent** chooses bounded live web searches and produces an auditable source trail.
2. A **Briefing Editor** makes one tool-free generation call over that verified research.

## Project structure

- `index.html`: 32-state interactive presentation with four live model experiences.
- `server.py`: FastAPI server keeping credentials out of browser JavaScript.
- `AI_AGENTS_WORKSHOP.ipynb`: two-stage NVIDIA participant capstone.
- `workshopkit.py`: student-planning simulator, retrieval tools, specialists and NVIDIA research helpers.
- `data/`: fictional student/course data plus dated Perth and NVIDIA continuity snapshots.
- `FACILITATOR_GUIDE.md`: exact 120-minute run sheet, teaching cues and failure handling.

## Run the presentation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-live.txt
cp .env.example .env
# Add a workshop-only ANTHROPIC_API_KEY to .env
python server.py
```

Open `http://localhost:8000`. Use arrows or Space to navigate, Home/End to jump, F for fullscreen, and Contents for the workshop map.

Two prompt/context demonstrations call Claude through the server. Slide 6 is a prompt-only CRAFT editor seeded from slide 3. The Perth challenge uses bounded web search, and the Student Planner makes a real tool-selection loop over deterministic fictional data. API failures remain visible and never break navigation.

## Run the notebook capstone

```bash
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab AI_AGENTS_WORKSHOP.ipynb
```

The notebook loads `ANTHROPIC_API_KEY` from `.env`, with a `getpass()` fallback that does not write the key into the notebook. Learners edit only:

- `build_research_prompt()`
- `build_briefing_prompt(research)`

Each stage is run, scored against five visible checks, changed in one CRAFT component and rerun. The research stage uses at most three searches by default. If live research fails, the notebook visibly loads `data/nvidia_research_fallback.md`, which is dated and must not be presented as current research.

The capstone is educational. It produces no buy/sell recommendation, price target, fabricated financials, personalised financial advice or transaction.

## API interfaces

### `GET /api/health`

Reports configuration, credential source, model, authentication status and the maximum allowed research searches.

### `POST /api/claude/stream`

One visible-text generation call. Fields: `prompt`, optional `system`, and optional `max_tokens`.

### `POST /api/agent/study-session`

Runs the observable Student Planner loop with `get_deadlines`, `get_calendar`, `get_current_progress`, `estimate_available_hours` and approval-gated `save_study_plan` tools. No real LMS, calendar or student record is modified.

### `POST /api/agent/research`

Runs bounded Anthropic server-side web search for the NVIDIA capstone. Input fields are `task`, `instructions` and optional `max_searches` from one to five. Output includes observable events, sources, usage, stop reason, visible text and `fallback_used`. Hidden reasoning is never requested or returned.

### `POST /api/agent/web-research`

Runs the bounded Perth web-research demonstration used on slide 7. It has the same input and observable output contract as the NVIDIA endpoint, but selects `data/perth_weekend_fallback.md` if live search is unavailable. The fallback is visibly dated and is never presented as current research.

Anthropic web search adds per-search charges plus token costs. Use a workshop-specific key with spending limits and disable it after the event.

## Validate and deploy

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The existing `vercel.json` deploys the FastAPI project. Set `ANTHROPIC_API_KEY` in the host environment. Optional settings are `WORKSHOP_MODEL`, `WORKSHOP_MAX_PROMPT_CHARS`, and `WORKSHOP_MAX_OUTPUT_TOKENS`.

Before delivery, verify the deck at 1366×768 and 1920×1080, narrow mobile width, keyboard-only navigation, reduced motion and print layout.
