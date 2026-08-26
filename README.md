# AI Agent Research Lab

A two-hour beginner workshop built around one coherent project: research NVIDIA with a live web-search agent, turn the verified research into a one-page investor briefing, then evaluate and improve both CRAFT prompts.

The workshop deliberately distinguishes two system shapes:

- **Research Agent:** Claude may choose bounded live web searches, inspect sources and continue until it can answer.
- **Briefing Editor:** one tool-free generation call transforms only the verified research. It is not presented as an autonomous agent.

This is an educational research exercise, not financial advice. It produces no recommendation, price target, personalised advice or transaction.

## Project structure

- `index.html`: interactive research-lab presentation.
- `server.py`: FastAPI server for browser calls and the research endpoint.
- `AI_AGENTS_WORKSHOP.ipynb`: participant build with two learner-owned CRAFT functions.
- `workshopkit.py`: inspectable live-search, citation, fallback and briefing helpers.
- `data/nvidia_research_fallback.md`: dated continuity snapshot used only if live research fails.
- `FACILITATOR_GUIDE.md`: exact 120-minute run sheet and teaching cues.
- `tests/test_workshop.py`: deck, notebook, endpoint and runtime tests.

## Run the live deck

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-live.txt
cp .env.example .env
# Add a workshop-only ANTHROPIC_API_KEY to .env
python server.py
```

Open `http://localhost:8000`. The key remains in Python and is never sent to browser JavaScript. The status badge distinguishes a ready API from fallback mode or a rejected key.

Controls: arrows or Space navigate, Home/End jump, F enters fullscreen, and Contents opens the workshop map.

## Run the notebook

```bash
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab AI_AGENTS_WORKSHOP.ipynb
```

The notebook loads `ANTHROPIC_API_KEY` from `.env`; if missing, it asks through `getpass()` without writing the key into the notebook. Learners edit only `build_research_prompt()` and `build_briefing_prompt(research)`.

Each stage follows the same learning loop: run, score five visible criteria, change one CRAFT component, and rerun.

## Live API

### `GET /api/health`

Reports configuration, credential source, selected model and the search cap. `?validate=true` checks whether Anthropic accepts the configured credential.

### `POST /api/claude/stream`

Streams visible text from one non-agentic generation call. Fields: `prompt`, optional `system`, and optional `max_tokens`.

### `POST /api/agent/research`

Input:

```json
{
  "task": "research question",
  "instructions": "CRAFT system prompt",
  "max_searches": 3
}
```

The bounded maximum is five. Output includes `ok`, `model`, observable `events`, deduplicated `sources`, `usage`, `stop_reason`, `text`, and `fallback_used`. Events are limited to user input, web searches, sources, visible final text, usage and errors. Hidden reasoning is never requested or returned.

## Search cost and fallback

Anthropic web search adds per-search charges plus ordinary token usage. The workshop defaults to at most three searches per research run and never accepts more than five.

If credentials, connectivity, search or a long-running turn fails, the runtime loads `data/nvidia_research_fallback.md`. The deck and notebook label it **DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH**. It preserves the exercise flow but must not be described as current evidence.

Use a workshop-specific API key with spending limits and disable it after the event.

## Validation and deployment

Run:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The existing `vercel.json` deploys the FastAPI project. Hosted deployments need `ANTHROPIC_API_KEY` and optionally `WORKSHOP_MODEL`, `WORKSHOP_MAX_PROMPT_CHARS`, and `WORKSHOP_MAX_OUTPUT_TOKENS` in the host environment. Verify projector layouts at 1366×768 and 1920×1080 before delivery.
