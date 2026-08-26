# Facilitator guide

## Workshop promise

By the end, a beginner should be able to decide whether a student task needs a better prompt, better context, retrieval, a deterministic workflow, an agent, several agents or a human decision. They should also have run real model and tool calls without handing assessed thinking to the system.

The room should make a prediction, edit something, inspect a trace or discuss a decision every 5–8 minutes.

## The three recurring stories

- **Maya — deadline triage:** use for prompting, evaluation and context.
- **Noah — group-project coordination:** use for tools, failures, agent loops and approval.
- **Priya — research and revision:** use for retrieval, orchestration, cost and academic integrity.

Do not introduce unrelated enterprise examples. When someone offers one, translate the underlying idea back into one of these student situations.

The participant notebook adds **Aisha — adaptive revision** as a deliberate new build. She is studying the fictional commerce elective *Leadership in Organisations*. Her coach selects formative study support from simulated mastery data and supplied notes.

## 120-minute run sheet

| Time | Segment | Audience activity |
|---|---|---|
| 0:00–0:07 | Opening discussion | Ask “What is AI?” and collect the room's current definitions |
| 0:07–0:15 | Cold open and student stories | Inspect the live deadline response and name its assumptions |
| 0:15–0:33 | Prompting | Reveal RECIPE with Maya, then build and test Priya's source-grounded research request |
| 0:33–0:45 | Context engineering | Identify what enters Maya's working context, what remains useful and what should leave |
| 0:45–1:02 | Tools and trace | Run the study-room agent and explain each observable event |
| 1:02–1:10 | Agent loop | Reconstruct the model → action → result loop with the room |
| 1:10–1:27 | First agent build | Complete Aisha's adaptive study-coach Mission 1 and compare traces |
| 1:27–1:38 | Workflow, failure and approval | Classify student tasks and resolve Noah's approval |
| 1:38–1:50 | Orchestration | Explore patterns and complete Priya's Mission 2 |
| 1:50–1:57 | Retrieval | Retrieve a policy passage and complete Mission 3 |
| 1:57–2:00 | MCP and final design | Sketch Noah's smallest viable architecture |

## Key transitions

### Prompt to context

“The prompt describes the job. Context engineering decides what the model can see at this step, how that information changes, and what should stay out.”

### Context to tools

“No amount of prompt detail can tell Noah whether a room is available next Tuesday. The system needs a way to check.”

### Tool to agent loop

After the live trace, point to the observable sequence: the model requested a structured call, Python executed the simulator, and the result returned before the final answer.

### Agent loop to notebook

“You have now seen the whole loop. In the notebook, the code and tools are ready; your three prompts determine how Aisha's coach behaves, what it is trying to achieve and how its study pack is checked.”

### Single agent to orchestration

Ask whether Priya's evidence search and rubric review are distinct enough to justify separate calls. Treat “one careful call” as a valid design answer.

### Retrieval to MCP

“Retrieval got the right text into context. MCP addresses a different problem: how a host discovers tools and resources from many services in a consistent way.”

## Academic integrity language

Keep this boundary stable throughout the workshop:

- The system may plan, explain, ask questions, retrieve permitted material and give feedback.
- The student remains responsible for claims, interpretation and submitted prose.
- The assistant must not invent circumstances, evidence, policy or citations.
- Current unit and university rules take precedence over fictional workshop material.

## Live presentation routine

Before students arrive:

1. Start server.py.
2. Confirm the status label appears on a live slide and reports the expected model.
3. Click every RECIPE ingredient and run the cold open, prompt builder and study-room agent once.
4. Run Aisha's notebook mission with the mixed profile and confirm the quality check appears.
5. Trigger WORKSHOP_SIMULATE_ROOM_FAILURE=1, verify the trace, then unset it.
6. Test arrow keys, space, fullscreen, contents, deep links and the approval interaction.
7. Check the deck on the venue projector.

For the live tool slide, first run the default instructions. Then weaken them and run again so the room sees that providing a tool does not guarantee appropriate use.

## Facilitation cues kept outside the audience deck

- On “What is AI?”, accept conflicting definitions and return to them after the agent loop.
- On the cold open, ask what the model organised and what it had to guess.
- On RECIPE, ask the room to predict the effect before each click. On the live builder, ask them to choose the evidence, gaps and next-search output they would need before they run it.
- On prompt surgery, give pairs 90 seconds and debrief the research question, available evidence, desired output and academically appropriate help.
- On context selection, keep the distracting options plausible so the discussion is about signal rather than trivia.
- On the live tool call, weaken the instructions on a second run to show that tool availability does not guarantee appropriate use.
- On workflow versus agent, require students to explain who controls the next step.
- On the final challenge, start from the student outcome before anyone draws an agent.

## If the API is unavailable

- Keep teaching from the editable prompts and prepared task text.
- If a live call returns nothing, point out the on-slide API status and explicit error message before moving to the prepared comparison.
- Read the expected observable sequence from the trace debrief slide.
- Pair students around one working machine if only some calls fail.
- Do not imply that a simulated room result is live university data.

## If running behind

Cut in this order:

1. The second prompt-builder run.
2. The controlled room-service failure.
3. Detailed orchestration pattern comparisons; keep the evaluator example.
4. The direct retrieval inspection before Mission 3.

Do not cut the first live call, the visible tool trace, Aisha's first agent build, the human approval decision or the final architecture challenge.
