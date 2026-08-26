# AI Agents Workshop

A two-hour, beginner-friendly workshop covering prompt engineering, CRAFT, context engineering, API anatomy, agent loops, tools, human approval, retrieval, multi-agent systems, evaluation and MCP.

The included NVIDIA notebook is the applied capstone:

1. A **Research Agent** chooses bounded live web searches and produces an auditable source trail.
2. A **Briefing Editor** makes one tool-free generation call over that verified research.

## Download the workshop

On GitHub, select **Code**, then either:

- choose **Download ZIP** and extract the downloaded folder; or
- copy the repository URL and run `git clone <repository-url>`.

Open a terminal in the extracted or cloned project folder before running the commands below.

## What is included

- `index.html`: the interactive workshop presentation.
- `server.py`: the local FastAPI server that keeps credentials out of browser JavaScript.
- `AI_AGENTS_WORKSHOP.ipynb`: the participant capstone notebook.
- `workshopkit.py`: the workshop tools, simulated student data and research helpers.
- `data/`: fictional workshop data and the dated NVIDIA continuity snapshot.
- `fonts/`: bundled presentation fonts and their licence files.

## Set up once

Python 3.10 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Open `.env` and add a workshop-only Anthropic API key:

```dotenv
ANTHROPIC_API_KEY=your_key_here
```

Never commit or share `.env`. Use a key with an appropriate spending limit and disable it after the workshop. Anthropic web search adds per-search charges as well as token costs.

## Run the presentation

Activate the virtual environment, then run:

```bash
python server.py
```

Alternatively, macOS users can open `start_live_deck.command` after completing setup.

Visit `http://localhost:8000`. Use the arrow keys or Space to navigate, Home/End to jump, F for fullscreen, and Contents for the workshop map.

The presentation contains two Claude prompt/context demonstrations and one Student Planner tool loop over deterministic fictional data. Slide 6 is a local CRAFT prompt editor and does not call the model. API failures remain visible and do not break navigation.

## Run the notebook capstone

With the virtual environment active, run:

```bash
jupyter lab AI_AGENTS_WORKSHOP.ipynb
```

If `jupyter` is not already installed, install it in the environment first:

```bash
pip install jupyterlab
```

The notebook loads `ANTHROPIC_API_KEY` from `.env`, with a secure prompt fallback that does not save the key into the notebook. Learners edit only:

- `build_research_prompt()`
- `build_briefing_prompt(research)`

Each stage is run, scored against five visible checks, changed in one CRAFT component and rerun. Research uses at most three searches by default. If live research fails, the notebook visibly loads `data/nvidia_research_fallback.md`, which is dated and must not be presented as current research.

The capstone is educational. It produces no buy/sell recommendation, price target, fabricated financials, personalised financial advice or transaction.

## API interfaces

### `GET /api/health`

Reports configuration, credential source, model, authentication status and the maximum allowed research searches.

### `POST /api/claude/stream`

Makes one visible-text generation call. Fields are `prompt`, optional `system`, and optional `max_tokens`.

### `POST /api/agent/study-session`

Runs the observable Student Planner loop with `get_deadlines`, `get_calendar`, `get_current_progress`, `estimate_available_hours` and approval-gated `save_study_plan` tools. It does not modify a real LMS, calendar or student record.

### `POST /api/agent/research`

Runs bounded Anthropic server-side web search for the NVIDIA capstone. Input fields are `task`, `instructions` and optional `max_searches` from one to five. Output includes observable events, sources, usage, stop reason, visible text and `fallback_used`. Hidden reasoning is never requested or returned.

## Deploy with Vercel

The included `vercel.json` configures the FastAPI project. Set `ANTHROPIC_API_KEY` in the Vercel project environment rather than uploading a local `.env` file.

Optional environment settings are:

- `WORKSHOP_MODEL`
- `WORKSHOP_MAX_PROMPT_CHARS`
- `WORKSHOP_MAX_OUTPUT_TOKENS`

The font files remain subject to the separate licence text files included in `fonts/`.
