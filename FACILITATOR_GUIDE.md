# Facilitator guide: AI Agent Research Lab

## Workshop promise

In exactly two hours, learners build a bounded web-search Research Agent and a grounded Briefing Editor around one NVIDIA question. They leave able to explain why the first stage is agentic, why the second is not autonomous, how a claim connects to evidence, and how one CRAFT change improves an output.

The room predicts, clicks, edits, runs, scores or discusses something every 5 to 8 minutes.

## Stable mental models

```text
CRAFT + TOOL + LOOP = AGENT
```

```text
VERIFIED RESEARCH + CRAFT = GROUNDED GENERATION
```

CRAFT means Context, Request, Approach, Format and constraints, and Test.

## Exact 120-minute run sheet

| Time | Segment | Audience action |
|---|---|---|
| 0:00–0:04 | Cover and mission | Read the shared NVIDIA question; predict what evidence is needed |
| 0:04–0:10 | Chatbot, workflow or agent | Click-classify three systems and defend the choice |
| 0:10–0:18 | CRAFT | Build the five prompt layers interactively |
| 0:18–0:25 | Observable tests | Rewrite “accurate and detailed” as scoreable criteria |
| 0:25–0:32 | API anatomy | Assemble model, system, messages, tools and max tokens |
| 0:32–0:38 | Instructions vs task | Identify which facts belong in each field |
| 0:38–0:44 | Source quality | Sort primary evidence, independent context and weak leads |
| 0:44–0:50 | Context and boundaries | Audit a decorative chart and name prohibited outputs |
| 0:50–0:58 | Agent loop | Predict the searches and define a stopping condition |
| 0:58–1:02 | Live Research Agent | Run the trace and connect one claim to one source |
| 1:02–1:07 | Notebook setup | Open notebook, run setup, pair anyone with credential trouble |
| 1:07–1:20 | Research prompt v1 | Edit `build_research_prompt()`, run and inspect sources |
| 1:20–1:27 | Research evaluation | Score five checks and identify the weakest one |
| 1:27–1:32 | Research prompt v2 | Change one CRAFT line, rerun and compare |
| 1:32–1:42 | Briefing prompt v1 | Edit `build_briefing_prompt(research)` and generate the brief |
| 1:42–1:48 | Briefing evaluation | Score traceability, balance, uncertainty, shape and safety |
| 1:48–1:52 | Briefing prompt v2 | Change one CRAFT line and rerun |
| 1:52–2:00 | Rebuild and exit check | Reconstruct the pipeline and complete four explanation sentences |

## Facilitation cues

- Keep everyone on the NVIDIA question. Consistency makes outputs comparable and problems easier to diagnose.
- Ask “who chooses the next step?” whenever the words chatbot, workflow or agent become blurry.
- Treat the CRAFT Test as a visible rubric, not a request for hidden self-reflection.
- On API anatomy, make students say what changes when `tools` is removed.
- On source quality, separate primary evidence from useful independent interpretation. Both can matter, but they serve different jobs.
- Before the live run, ask the room to predict two searches. Afterward, compare their predictions with the observable search events.
- Do not narrate hidden reasoning. Discuss only the question, searches, returned sources, visible output, stop reason and usage.
- Require one controlled prompt change between versions. If learners rewrite everything, they cannot attribute the improvement.
- Call the second stage the Briefing Editor or grounded generation stage. Do not call it an autonomous agent.

## Output checks

Research must include an executive summary, a claim/evidence/source/date/confidence table, exactly three growth drivers, exactly three material risks, disagreements or missing evidence, and a linked source ledger.

The briefing must include a neutral watchlist thesis, business snapshot, three drivers, three risks, upcoming evidence to monitor, uncertainties and inherited references. It must introduce no new facts.

Neither stage may give a buy/sell recommendation, price target, fabricated figure or personalised financial advice. Any future system that accesses an account or places a trade requires explicit human approval and is outside this workshop.

## Before learners arrive

1. Start `server.py` and open the HTTP URL, not the HTML file directly.
2. Confirm the API badge reads `API READY` and the expected model appears in `/api/health`.
3. Run the live Research Agent once and verify searches, sources, final output and usage appear.
4. Run the notebook from a clean kernel through both prompt stages.
5. Temporarily remove the API key and verify the research path visibly loads the dated fallback.
6. Restore the key and verify the generic streaming call.
7. Test arrows, Space, Home, End, fullscreen, Contents, deep links and print.
8. Check 1366×768 and 1920×1080 projectors and a narrow mobile layout.
9. Confirm the workshop key has a suitable spending limit.

## Failure handling

- Missing credential, network failure, empty research or repeated `pause_turn`: continue with the visibly labelled dated snapshot.
- Authentication rejected: replace the key; do not paste it into the notebook or browser.
- Rate limit: pair learners around a completed research result, then let each person write and evaluate their own Briefing Editor prompt.
- Search returns weak sources: treat it as the lesson. Improve the Approach or Test line and rerun once.
- Running late: keep one run and one scored change for each stage. Shorten discussion, never remove source auditing or the distinction between agentic research and grounded generation.

## Closing questions

Every learner should be able to complete these aloud:

1. “The Research Agent was agentic because…”
2. “The Briefing Editor was not autonomous because…”
3. “This source supports this claim because…”
4. “Changing this CRAFT line improved…”
