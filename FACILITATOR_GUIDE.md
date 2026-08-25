# Facilitator guide

## Workshop promise

By the end, a beginner should be able to decide whether a student task needs a better prompt, better context, retrieval, a deterministic workflow, an agent, several agents or a human decision. They should also have run real model and tool calls without handing assessed thinking to the system.

The room should make a prediction, edit something, inspect a trace or discuss a decision every 5–8 minutes.

## The three recurring stories

- **Maya — deadline triage:** use for prompting, evaluation and context.
- **Noah — group-project coordination:** use for tools, failures, agent loops and approval.
- **Priya — research and revision:** use for retrieval, orchestration, cost and academic integrity.

Do not introduce unrelated enterprise examples. When someone offers one, translate the underlying idea back into one of these student situations.

## 120-minute run sheet

| Time | Segment | Audience activity |
|---|---|---|
| 0:00–0:08 | Cold open and student stories | Inspect the live deadline response and name its assumptions |
| 0:08–0:26 | Prompting | Build Maya's request, define success and complete prompt surgery |
| 0:26–0:38 | Context | Choose what belongs on Maya's desk and discuss signal |
| 0:38–0:48 | First notebook call | Complete Mission 1 |
| 0:48–1:04 | Tools and trace | Run the study-room agent and explain each observable event |
| 1:04–1:19 | Toolbox and failure | Complete Mission 2, compare traces and trigger the failure |
| 1:19–1:30 | Workflow, agent and approval | Classify student tasks and resolve Noah's approval |
| 1:30–1:45 | Orchestration | Explore patterns and complete Mission 3 |
| 1:45–1:55 | Retrieval | Retrieve a policy passage and complete Mission 4 |
| 1:55–2:00 | MCP and final design | Sketch Noah's smallest viable architecture |

## Key transitions

### Prompt to context

“The request describes the job. Now we need to decide which information deserves to be on the desk while the model works.”

### Context to tools

“No amount of prompt detail can tell Noah whether a room is available next Tuesday. The system needs a way to check.”

### Tool to agent loop

After the live trace, point to the observable sequence: the model requested a structured call, Python executed the simulator, and the result returned before the final answer.

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
3. Run the cold open, prompt builder and study-room agent once.
4. Trigger WORKSHOP_SIMULATE_ROOM_FAILURE=1, verify the trace, then unset it.
5. Test arrow keys, space, fullscreen, notes, contents, deep links and the approval interaction.
6. Check the deck on the venue projector.

For the live tool slide, first run the default instructions. Then weaken them and run again so the room sees that providing a tool does not guarantee appropriate use.

## If the API is unavailable

- Keep teaching from the editable prompts and prepared task text.
- Read the expected observable sequence from the trace debrief slide.
- Pair students around one working machine if only some calls fail.
- Do not imply that a simulated room result is live university data.

## If running behind

Cut in this order:

1. The second prompt-builder run.
2. The controlled room-service failure.
3. Detailed orchestration pattern comparisons; keep the evaluator example.
4. The direct retrieval inspection before Mission 4.

Do not cut the first live call, the visible tool trace, the human approval decision or the final architecture challenge.
