# Facilitator Guide — AI Agents Workshop

## Workshop promise

By the end, a beginner should be able to explain the difference between prompting, context, tools, agent loops, multi-agent orchestration, retrieval and MCP — and they should have personally run real Claude tool calls in the notebook.

The room should **do something every 5–8 minutes**.

## 120-minute run sheet

| Time | Segment | What the audience does |
|---|---|---|
| 0:00–0:05 | Cold open | Decide whether the first system actually acted; watch tools change the system |
| 0:05–0:25 | Prompt engineering | Predict output changes; use prompt builder; 90-second Prompt Surgery |
| 0:25–0:35 | Context engineering | Pack Marv's context; discuss high-signal vs noise |
| 0:35–0:44 | First API call | Notebook Mission 2 |
| 0:44–0:53 | One-tool agent | Notebook Mission 3 + inspect trace |
| 0:53–1:05 | Toolbox agent | Notebook Mission 4 + compare neighbours' traces |
| 1:05–1:14 | Dynamic path / failure | Mission 4B if time; discuss environmental feedback |
| 1:14–1:20 | Workflow vs agent + human approval | Classify tasks and recap |
| 1:20–1:33 | Multi-agent | Pattern visual + Notebook Mission 5 |
| 1:33–1:40 | RAG | Retrieval visual + Notebook Mission 6 |
| 1:40–1:48 | MCP | Integration pain → MCP → demo server |
| 1:48–1:55 | Managed Agents | Presenter-only demo and approval concept |
| 1:55–2:00 | Architecture challenge | Spin a brief, team sketch, reveal one possible answer |

## Slides are states, not a lecture count

The deck contains many short presentation states. Several are 20–40 second reveals, not conventional slides that require explanation. Do not attempt to give every slide equal time.

## Critical transitions

### Prompt → Context

Say: **“Prompt engineering is how we instruct the model. Context engineering is deciding what information deserves to be in the room while it works.”**

### Context → Agent

Do not define agents first. Let students see `instructions + context + model`, then add `tools + loop`, then reveal the word **agent**.

### Tools → Agent loop

After the first trace, emphasise that Claude did not execute the Python function. It emitted a structured request, the runtime executed it, and the result returned to context.

### Single agent → Multi-agent

Create the limitation first: one agent is being asked to research, budget, analyse and write. Then decompose. Immediately add the warning that multi-agent systems introduce cost and coordination overhead.

### RAG

Say the acronym last. Start with a private club-policy question that Claude should not guess, then build the retrieval flow visually.

### MCP

Create the integration mess first. Explain that MCP is a standards layer, not an intelligence layer.

## If running behind schedule

Cut in this order:

1. Mission 4B simulated tool failure (save ~5 min)
2. Detailed multi-agent pattern click-through; show only router + orchestrator (save ~3 min)
3. RAG direct retrieval cell; go straight to the agent (save ~2 min)
4. Managed Agents live execution; use the prepared slide trace instead (save ~5 min)

Do **not** cut the first tool-call mission, the toolbox mission, or the final architecture challenge. Those are the workshop's conceptual spine.

## If API calls are slow

- Pair students instead of waiting for every laptop.
- Keep the instructor solution notebook open with pre-run outputs.
- The HTML deck's agent traces are intentionally usable as a fallback explanation.
- Avoid repeatedly running the multi-agent mission; it creates several model calls.

## API key handling

Use a workshop-specific key or controlled credential with budget/rate controls where possible. The participant notebook uses hidden `getpass()` input and never writes the key to disk.


## Live deck API setup

The prompt-engineering and first tool-use slides now make real Claude calls. Start the deck with `python server.py` rather than double-clicking `index.html`. Confirm the top-left badge reads **LIVE CLAUDE** before students arrive.

The live flow is deliberately designed so participants edit **prompts and agent instructions**, while the infrastructure stays prebuilt:

1. Cold open: let one audience member suggest a job and type it live.
2. Prompt Builder: change one prompt ingredient at a time and re-run so the room can see causality.
3. Prompt Surgery: ask 2–3 groups for prompts and run them back-to-back.
4. Tool demo: first run the default task, then deliberately weaken the agent instructions and rerun to show that the same tool availability can produce different behaviour.

If the API is slow or unavailable, continue presenting normally and use the prepared static visuals/notebook outputs.

## Before the room arrives

- Test `AI_AGENTS_WORKSHOP.ipynb` from a clean environment.
- Confirm the workshop key can call the configured model.
- Run Missions 3–6 once.
- Open `index.html` and test fullscreen/keyboard navigation.
- Run the MCP server in the Inspector if demonstrating it live.
- Pre-create Managed Agent and Environment IDs and test the exact demo repository.
- Have `instructor/AI_AGENTS_WORKSHOP_SOLUTION.ipynb` open as a fallback.
- Replace the placeholder repo/resource link on the closing slide when the public repo is ready.
