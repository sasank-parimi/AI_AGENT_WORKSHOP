# Facilitator guide

## Workshop promise

Learners move from a vague request through prompt engineering, CRAFT, context engineering and clean API structure; inspect a genuine Student Planner tool loop; build a bounded NVIDIA Research Agent and grounded Briefing Editor; then connect that build to retrieval, multi-agent systems, evaluation, MCP and managed execution.

NVIDIA is one applied capstone. It does not replace the wider workshop curriculum.

## Mental models

```text
CRAFT + TOOLS + LOOP = AGENT
```

```text
VERIFIED RESEARCH + CRAFT = GROUNDED GENERATION
```

CRAFT means Context, Request, Approach, Format and constraints, and Test.

## Exact 120-minute run sheet

| Time | Slides/segment | Audience action |
|---|---|---|
| 0:00–0:07 | AI, vague request, chatbot or agent | Predict what Claude must guess; classify the interaction |
| 0:07–0:16 | CRAFT and live build | Add CRAFT layers and run the complete version |
| 0:16–0:23 | Prompt challenge and structure | Rewrite one request in pairs; name the success test |
| 0:23–0:29 | Prompt versus context and picker | Select useful context, then reveal correct, bad and overloaded presets |
| 0:29–0:35 | Focused or overloaded | Drag the context slider and run one contrasting call |
| 0:35–0:42 | API anatomy | Assemble model, system, messages, tools and max tokens |
| 0:42–0:49 | Why agents and planning tools | Predict which tools the planner needs |
| 0:49–0:55 | Live Student Planner | Run it and identify evidence for each planning decision |
| 0:55–0:59 | Loop and workflow versus agent | Reconstruct the loop and classify three tasks |
| 0:59–1:04 | Tool contracts and approval | Improve one contract and decide which actions must pause |
| 1:04–1:09 | Notebook setup | Open the notebook and run setup; pair credential failures |
| 1:09–1:22 | NVIDIA Research Agent v1 | Write CRAFT, run, inspect searches and sources |
| 1:22–1:29 | Evaluate research | Score five checks and identify the weakest criterion |
| 1:29–1:34 | Research v2 | Change one CRAFT line and rerun |
| 1:34–1:43 | Briefing Editor v1 | Write the second CRAFT prompt and generate from verified research |
| 1:43–1:48 | Evaluate briefing | Score traceability, balance, uncertainty, shape and safety |
| 1:48–1:51 | Briefing v2 | Change one CRAFT line and rerun |
| 1:51–1:57 | Retrieval, multi-agent, evaluator, MCP, managed execution | Use the compressed capability map; connect each idea to the capstone |
| 1:57–2:00 | Architecture, personal direction, exit check | Reconstruct the system and state one next build |

The advanced tail is deliberately rapid because the workshop has already demonstrated the underlying patterns. Use it as a map, not a second lecture.

## Live-call routine

The deck contains five live experiences:

1. vague baseline through `/api/claude/stream`;
2. completed CRAFT prompt through `/api/claude/stream`;
3. editable prompt challenge through `/api/claude/stream`;
4. focused/overloaded context through `/api/claude/stream`;
5. Student Planner through `/api/agent/study-session`.

Each workbench exposes the goal, system instructions, context, tools and success-test status. Run the baseline, complete CRAFT call, one context call and Student Planner. Treat the prompt-challenge API run as optional if time is tight.

Never describe observable traces as hidden reasoning. Discuss user goals, searches, tool requests, tool results, sources, final responses, stop reasons and usage only.

## Teaching cues

- Prompt engineering specifies the job. Context engineering selects what matters for this decision.
- On API anatomy, remove `tools` verbally and ask what behaviour is no longer possible.
- On workflow versus agent, ask who chooses the next step.
- A clear tool contract states what the tool does, accepts and returns.
- Preparing an action is not approval to execute it.
- The notebook Research Agent is agentic because it can choose searches. The Briefing Editor is not autonomous because its next step and context are fixed.
- Require one controlled CRAFT change between versions. Rewriting everything makes improvement impossible to attribute.
- Retrieval, specialists and MCP are extensions of context and tools, not unrelated buzzwords.

## Safety boundaries

- Student examples may organise, retrieve, explain, quiz and review student-owned work, but must not create submission-ready assessed answers.
- The NVIDIA capstone may compare evidence, cite sources, surface risks and create a neutral watchlist brief.
- It must not provide a recommendation, price target, fabricated figures or personalised financial advice.
- Any account access, calendar mutation, message send, deletion or trade requires explicit human approval and remains outside the model’s authority.

## Before learners arrive

1. Start `server.py` and open the HTTP URL rather than the HTML file directly.
2. Confirm `/api/health?validate=true` reports the intended model and accepted credential.
3. Run all four prompt/context workbenches and the Student Planner.
4. Verify planner results contain fictional deadlines, calendar, progress and capacity.
5. Run both notebook stages from a clean kernel.
6. Remove the key temporarily and confirm the NVIDIA research stage visibly loads the dated fallback; then restore the key.
7. Test arrows, Space, Home, End, fullscreen, Contents, deep links, stop controls and print.
8. Check 1366×768, 1920×1080 and a narrow mobile layout.
9. Confirm the workshop key has an appropriate spending limit.

## Failure handling and cut list

- Prompt call failure: use the explicit error state and continue with editable prompts and deterministic interactions.
- Planner failure: inspect the visible failure and continue with the loop diagram.
- Research authentication, network, rate-limit, empty-output or repeated-pause failure: use the visibly dated classroom snapshot.
- If behind, remove extra API reruns first, then skip the second prompt-challenge scenario. Never cut prompt versus context, the Student Planner trace, the notebook improvement cycles, human approval, or the agent-versus-generation distinction.

## Exit check

Every learner should be able to complete these statements:

1. “Prompt engineering changed…”
2. “Context engineering changed…”
3. “The Research Agent was agentic because…”
4. “The Briefing Editor was fixed generation because…”
5. “This source supports this claim because…”
