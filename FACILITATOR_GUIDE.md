# Facilitator guide

## Workshop promise

Students progressively build one Student Agent rather than meeting a collection of disconnected demos. By the end, they should be able to explain when a task needs clearer instructions, focused context, retrieval, a deterministic workflow, one agent, specialist agents, MCP-style connections or human approval.

The room should predict, edit, run, inspect or discuss something every 5–8 minutes. All student records, documents and actions are workshop simulations. The assistant supports planning and learning; the student remains responsible for assessed thinking and submitted work.

## The two mental models

Return to these throughout the workshop:

    CRAFT + TOOLS + LOOP = AGENT

Then, after the first build:

    AGENT + RETRIEVAL + SPECIALISTS + MCP = MORE CAPABLE SYSTEM

CRAFT means Context, Request, Approach, Format & constraints, and Test. Approach is intentionally broader than role prompting.

## 120-minute run sheet

| Time | Slides | Segment | Audience activity |
|---|---:|---|---|
| 0:00–0:05 | 1–2 | What we are building | Choose the capability they would most want to keep using |
| 0:05–0:10 | 3–4 | Baseline and agent distinction | Run the vague request and list what Claude guessed |
| 0:10–0:18 | 5–6 | CRAFT | Predict the effect of each new CRAFT layer, then run two stages |
| 0:18–0:25 | 7–9 | Prompt challenge | Improve “Help me study” in pairs and name the success test |
| 0:25–0:30 | 10–11 | Prompt versus context | Select only the context needed for tonight's decision |
| 0:30–0:35 | 12–13 | Focused versus overloaded | Run both contexts and compare specificity, assumptions and noise |
| 0:35–0:42 | 14–15 | From CRAFT to an agent | Unlock the planning tools and predict which ones are necessary |
| 0:42–0:50 | 16–17 | Live planning loop | Run the Student Planner and reconstruct its observable loop |
| 0:50–1:10 | 18 | Notebook Mission 1 | Build the Student Planner, inspect traces and revise CRAFT instructions |
| 1:10–1:18 | 19–20 | Architecture and scope | Rebuild the architecture, then classify three tasks |
| 1:18–1:25 | 21–22 | Tool contracts and approval | Improve a tool contract and decide which actions must pause |
| 1:25–1:33 | 23–24 | Private course knowledge | Search the supplied documents and identify the supporting passage |
| 1:33–1:40 | 25 | Revision upgrade | In the notebook, run the same agent with mastery, retrieval and quiz tools |
| 1:40–1:48 | 26–27 | Specialists and evaluator loop | Decide whether Researcher, Planner or Reviewer adds real value |
| 1:48–1:54 | 28 | MCP | Connect services and name the remaining permission boundary |
| 1:54–1:59 | 29–30 | Make it yours and next steps | Choose a personal direction and complete the six design questions |
| 1:59–2:00 | 31 | Live-demo handoff | Recap the capability stack, then leave the deck |

## Key transitions

### Baseline to CRAFT

“The model can produce a plausible answer, but we cannot yet tell whether it fits the real week. CRAFT makes the task and its success conditions visible.”

### CRAFT to context

“CRAFT describes the job. Context engineering decides what the model can see for this particular decision.”

### Context to tools

“We could paste deadlines and calendars into every request, or give the Student Agent a reliable way to fetch the current information.”

### Tools to the loop

Point only to observable events: the user goal, structured tool request, deterministic result and final plan. Do not imply the trace exposes hidden reasoning.

### Agent loop to notebook

“You have seen the whole loop. The notebook gives you the same tools; your CRAFT instructions determine what the Student Agent checks, how it plans and where it stops.”

### First build to retrieval

“The planner now understands the week, but it still does not know the unit. Retrieval adds only the course passage needed for the current question.”

### Retrieval to specialists

“Specialists are not a fresh story. They are optional workers under the same Student Agent, useful only when the work has genuinely distinct parts.”

### Specialists to MCP

“Our Python tools are local. MCP provides a consistent way for an AI host to discover capabilities from real services, while authentication and approval remain our responsibility.”

## Live presentation routine

Before students arrive:

1. Start `server.py` and open `http://localhost:8000` rather than opening `index.html` directly.
2. Confirm a live slide reports the expected model and an authenticated API.
3. Run the baseline, CRAFT stage 1, CRAFT stage 5, both context comparisons and the Student Planner.
4. Confirm the planning trace includes deadlines, calendar, progress and capacity results.
5. Verify `save_study_plan` is not treated as permission to create real events.
6. Run notebook Missions 1–3 once from a clean kernel.
7. Set `WORKSHOP_SIMULATE_PLANNER_FAILURE=1`, confirm the failure is visible, then unset it.
8. Set `WORKSHOP_SIMULATE_RETRIEVAL_FAILURE=1`, confirm retrieval fails honestly, then unset it.
9. Test arrow keys, Space, Home, End, fullscreen, contents, deep links and print output.
10. Check the venue projector at 1366×768 and 1920×1080.

## Facilitation cues

- On the capability slide, ask for a show of hands rather than explaining every item.
- On the baseline, collect guesses before discussing prompt quality.
- On CRAFT, run the starting request, an intermediate stage and the complete specification. More runs add little.
- On the context comparison, keep the task and system instruction fixed so context is the only changed variable.
- On the planner trace, ask students to identify evidence for each decision in the final plan.
- On workflow versus agent, require a reason based on who chooses the next step.
- On tool contracts, ask what can be validated before execution.
- On approval, distinguish preparing an action from carrying it out.
- On retrieval, reveal the acronym only after students understand the search → passage → context pattern.
- On specialists, treat “one careful call” as a valid design when delegation does not earn its cost.
- On the final design, start with the useful student outcome before discussing frameworks.

## Academic-integrity language

Keep this stable throughout:

- The Student Agent may organise, explain, ask formative questions, retrieve permitted material and review a student's own work.
- It must not invent student circumstances, course content, policy or citations.
- It must not create submission-ready assessed answers.
- Current unit and university instructions take precedence over fictional workshop material.

## If an API call fails

- Use the explicit on-slide status or error; a failed call should never look like an unresponsive button.
- Continue with the editable prompt, context selection and deterministic tool data.
- Pair students around a working machine if only some credentials fail.
- A deployed site needs `ANTHROPIC_API_KEY` in the hosting environment. The local root `.env` is used by `server.py` and the notebook only when running locally.

## If running behind

Cut in this order:

1. The intermediate CRAFT API run; keep the baseline and complete CRAFT run.
2. The overloaded-context API run; still discuss the comparison.
3. The tool-contract exercise.
4. The evaluator-loop debrief.

Do not cut the Student Planner trace, Notebook Mission 1, retrieval grounding, human approval, personal design canvas or live-demo handoff.
