# Facilitator guide

## Workshop promise

Students move from an ordinary chatbot request through structured prompting, context engineering and a full agent loop, then build three agents of their own in the notebook: a Tutor, a Flashcard Generator and a Study Planner. By the end, they should be able to explain when a task needs clearer instructions, focused context, retrieval, a deterministic workflow, a single agent, a multi-agent system, MCP-style connections or human approval.

The room should predict, edit, run, inspect or discuss something every 5 to 8 minutes. All student records, documents and actions are workshop simulations. The assistant supports planning and learning; the student remains responsible for assessed thinking and submitted work.

## The two mental models

Return to these throughout the workshop:

    CRAFT + TOOLS + LOOP = AGENT

Then, after the first build:

    AGENT + RETRIEVAL + MULTI-AGENT SYSTEMS + MCP + MANAGED EXECUTION = MORE CAPABLE SYSTEM

CRAFT means Context, Request, Approach, Format and constraints, and Test. Approach is intentionally broader than role prompting.

## Run sheet (roughly 130 minutes)

This runs a little longer than two hours because the notebook block now covers three agents instead of one. Cut list is below if you need to bring it back to 120.

| Time | Slides | Segment | Audience activity |
|---|---:|---|---|
| 0:00-0:03 | 1 | Cover | Set expectations: build, don't just watch |
| 0:03-0:08 | 2 | What is AI | Open floor. Ask the room what they think AI is and where they've used it this week |
| 0:08-0:13 | 3-4 | Ask it and hope, chatbot or agent | Run the vague request live and list what Claude guessed |
| 0:13-0:21 | 5-6 | CRAFT | Predict the effect of each new CRAFT layer, then run two stages |
| 0:21-0:28 | 7-9 | Prompt challenge, examples, takeaway | Pick a scenario, improve the request in pairs, name the success test |
| 0:28-0:33 | 10-11 | Prompt vs context, context picker | Use the clickable notes to compare correct, bad and overloaded context |
| 0:33-0:38 | 12-13 | Focused or overloaded, takeaway | Drag the slider live and watch the answer change |
| 0:38-0:44 | 14-15 | Why agents help students, what is an agent | Ask which capability they'd actually use this semester |
| 0:44-0:50 | 16-17 | Planning tools, live Student Planner | Unlock the tools, predict which are necessary, then run it |
| 0:50-0:56 | 18-21 | Agent loop, workflow or agent, tool contracts, human approval | Classify three tasks, then decide which actions must pause for approval |
| 0:56-1:26 | 22 | Build your own agents | Build and run the Tutor, Flashcard and Study Planner agents in the notebook |
| 1:26-1:32 | 23 | Architecture recap | Rebuild the architecture diagram from memory |
| 1:32-1:40 | 24-25 | Retrieval | Search the supplied documents and identify the supporting passage |
| 1:40-1:48 | 26-27 | Multi-agent systems, evaluator loop | Decide whether Researcher, Planner or Reviewer adds real value; open floor on when you would NOT want this |
| 1:48-1:54 | 28 | Tools and MCP | Connect services and name the remaining permission boundary |
| 1:54-1:59 | 29 | Claude managed agents | Match a project idea to something they could actually build |
| 1:59-2:05 | 30-31 | Make it yours, next steps | Choose a personal direction and complete the six design questions |
| 2:05-2:10 | 32 | Live demos | Recap the capability stack, then leave the deck for live demos |

## Key transitions

### Opening to prompting

"Before we touch anything, tell us what you think AI actually is. We'll come back to that."

### Baseline to CRAFT

"The model can produce a plausible answer, but we cannot yet tell whether it fits the real task. CRAFT makes the task and its success conditions visible."

### CRAFT to context

"CRAFT describes the job. Context engineering decides what the model can see for this particular decision."

### Context to agents

"We could paste deadlines and calendars into every request, or give the agent a reliable way to fetch the current information itself. That's the difference between a prompt and an agent."

### Agents to the notebook

"You've now seen the whole loop live. The notebook gives you three agents with the tools already built. Your CRAFT instructions decide what each one actually does."

### First build to retrieval

"The planner now understands the week, but it still doesn't know the unit. Retrieval adds only the course passage needed for the current question."

### Retrieval to multi-agent systems

"A multi-agent system is not a fresh story. It's optional workers under one agent, useful only when the work has genuinely distinct parts."

### Multi-agent to MCP

"Our Python tools are local. MCP gives an agent one consistent way to discover capabilities from real services, while authentication and approval stay our responsibility."

### MCP to managed agents

"Everything today ran through a small server we wrote. A managed agent runs the same loop somewhere else, so you're not the one keeping infrastructure online."

## Live presentation routine

Before students arrive:

1. Start `server.py` and open `http://localhost:8000` rather than opening `index.html` directly.
2. Confirm a live slide reports the expected model and an authenticated API.
3. Run the opening baseline, CRAFT stage 1, CRAFT stage 5, both prompt-challenge scenarios, the context slider at both ends and the live Student Planner.
4. Confirm the planning trace includes deadlines, calendar, progress and capacity results.
5. Verify `save_study_plan` is not treated as permission to create real events.
6. Run all three notebook agent builds once from a clean kernel: Tutor, Flashcards, Study Planner.
7. Set `WORKSHOP_SIMULATE_PLANNER_FAILURE=1`, confirm the failure is visible, then unset it.
8. Set `WORKSHOP_SIMULATE_RETRIEVAL_FAILURE=1`, confirm retrieval fails honestly, then unset it.
9. Test arrow keys, Space, Home, End, fullscreen, contents, deep links and print output.
10. Check the venue projector at 1366x768 and 1920x1080.

## Facilitation cues

- On "What is AI", let the room talk. Don't correct them yet, just note what comes up and return to it later if useful.
- On "Ask it and hope", collect guesses about what Claude had to invent before discussing prompt quality.
- On CRAFT, run the starting request, an intermediate stage and the complete specification. More runs add little.
- On the context picker, use the three note buttons (correct, bad, overload) before letting students click freely.
- On the slider, keep the task and system instruction fixed so context is the only thing changing. Narrate what you'd expect before you drag it.
- On the planner trace, ask students to identify evidence for each decision in the final plan.
- On workflow versus agent, require a reason based on who chooses the next step.
- On tool contracts, ask what can be validated before execution.
- On approval, distinguish preparing an action from carrying it out.
- On retrieval, reveal the acronym only after students understand the search, passage, context pattern.
- On multi-agent systems, treat "one careful call" as a valid design when delegation doesn't earn its cost. Give the room two minutes to discuss when they would NOT want this.
- On the final design, start with the useful student outcome before discussing frameworks.

## Academic-integrity language

Keep this stable throughout:

- An agent may organise, explain, ask formative questions, retrieve permitted material and review a student's own work.
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
2. The second prompt-challenge scenario; run only one.
3. The tool-contract exercise.
4. The evaluator-loop debrief.
5. In the notebook block, if time is very short, prioritise the Study Planner Agent since it's the most self-contained, and let the Tutor and Flashcard agents be a take-home.

Do not cut the live Student Planner trace, the notebook build itself, retrieval grounding, human approval, the personal design canvas or the live-demo handoff.
