from __future__ import annotations

import json
import os
import re
import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import workshopkit
import server
from server import health

ROOT = Path(__file__).resolve().parents[1]


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.deck = cls.html.split('<main class="deck notebook-deck" id="deck">', 1)[1].split("</main>", 1)[0]
        cls.titles = re.findall(r'data-title="([^"]+)"', cls.deck)

    def test_deck_has_thirty_two_purposeful_states(self) -> None:
        slides = re.findall(r'<section class="slide[^>]*>', self.deck)
        self.assertEqual(len(slides), 32)
        self.assertEqual(len(slides), len(self.titles))

    def test_opening_matches_the_build_story(self) -> None:
        self.assertEqual(
            self.titles[:4],
            ["AI Agents Workshop", "What is AI", "Ask it and hope", "Chatbot or agent"],
        )
        self.assertIn("AI AGENTS", self.deck)
        self.assertIn("From prompt engineering to a research agent you build yourself", self.deck)
        self.assertIn("What is AI?", self.deck)
        for capability in (
            "Plan my week",
            "Search my notes",
            "Quiz me",
            "Review my work",
            "Research unfamiliar topics",
            "Use tools instead of guessing",
            "Connect to services",
        ):
            self.assertIn(capability, self.deck)

    def test_craft_is_progressive_and_reused_for_agents(self) -> None:
        for step, label in enumerate(("Context", "Request", "Approach", "Format", "Test"), 1):
            self.assertIn(f'data-craft-step="{step}"', self.deck)
            self.assertIn(label, self.deck)
        self.assertIn("initCraftBuilder", self.html)
        self.assertIn("CRAFT</strong>", self.deck)
        self.assertIn("CRAFT-based agent instructions", self.deck)
        self.assertNotIn("RECIPE", self.html)

    def test_slide_six_is_a_prompt_only_craft_editor_seeded_from_slide_three(self) -> None:
        slide = self.deck.split('data-title="Build with CRAFT"', 1)[1].split("</section>", 1)[0]
        self.assertIn("slide 3's request", slide)
        self.assertIn("this slide does not call Claude", slide)
        self.assertIn("data-baseline-prompt", self.deck)
        self.assertNotIn("data-live-claude", slide)
        self.assertNotIn("data-live-run", slide)
        self.assertNotIn("data-live-output", slide)
        for forbidden in ("do not ask questions", "don't ask questions", "ask for missing information"):
            self.assertNotIn(forbidden, slide.lower())

    def test_prompt_challenge_is_complete_bounded_perth_research(self) -> None:
        slide = self.deck.split('data-title="Prompt challenge"', 1)[1].split("</section>", 1)[0]
        for detail in (
            "5 September 2026",
            "Perth Station",
            "two adults",
            "10:00",
            "18:00",
            "AU$120",
            "no individual walk longer than 15 minutes",
            "vegetarian lunch",
            "three main activities",
            "indoor weather backup",
            "up to three web searches",
            "official venue, operator, transport or booking sources",
        ):
            self.assertIn(detail, slide)
        self.assertIn("data-live-web-research", slide)
        self.assertIn("/api/agent/web-research", self.html)
        self.assertIn("usage", slide.lower())
        for state in ("AUTHENTICATION FAILURE", "RATE LIMIT", "EMPTY OUTPUT", "STOPPED"):
            self.assertIn(state, self.html)
        for forbidden in ("do not ask questions", "don't ask questions", "ask for missing information"):
            self.assertNotIn(forbidden, slide.lower())

    def test_context_notes_demonstrate_three_states(self) -> None:
        slide = self.deck.split('data-title="Context picker"', 1)[1].split("</section>", 1)[0]
        for note in ("correct", "bad", "overload"):
            self.assertIn(f'data-context-note="{note}"', slide)

    def test_no_stray_fictional_personas_or_old_domain_terms(self) -> None:
        for name in ("Maya", "Noah", "Priya", "Aisha"):
            self.assertNotIn(name, self.html)
        for removed in ("cits2200", "hist2001", "econ1101", "comm1001", "dijkstra", "graph traversal", "dynamic programming"):
            self.assertNotIn(removed, self.html.lower())

    def test_chapter_progression_never_moves_backwards(self) -> None:
        sections = re.findall(r'<section class="slide[^>]*data-section="([^"]+)"', self.deck)
        order = {name: index for index, name in enumerate(("ai", "prompt", "craft", "context", "api", "agents", "build", "systems", "next"))}
        self.assertTrue(all(order[left] <= order[right] for left, right in zip(sections, sections[1:])))

    def test_context_slider_drives_one_real_call(self) -> None:
        slide = self.deck.split('data-title="Focused or overloaded"', 1)[1].split("</section>", 1)[0]
        self.assertEqual(slide.count("data-live-claude"), 1)
        self.assertIn("data-context-slider", slide)
        self.assertIn("Run with this context", slide)
        self.assertIn("initContextSlider", self.html)
        self.assertIn("minimum useful context", self.deck)

    def test_student_planner_tools_and_trace_are_visible(self) -> None:
        for tool in (
            "get_deadlines()",
            "get_calendar()",
            "get_current_progress()",
            "estimate_available_hours()",
            "save_study_plan()",
        ):
            self.assertIn(tool, self.deck)
        self.assertIn("/api/agent/study-session", self.html)
        self.assertIn("data-agent-trace", self.deck)
        self.assertIn("hidden chain-of-thought", self.deck)

    def test_notebook_handoff_is_the_two_stage_nvidia_capstone(self) -> None:
        slide = self.deck.split('data-title="NVIDIA capstone"', 1)[1].split("</section>", 1)[0]
        self.assertIn("NVIDIA Research Agent", slide)
        self.assertIn("Investor Briefing Editor", slide)
        self.assertIn("build_research_prompt()", slide)
        self.assertIn("build_briefing_prompt(research)", slide)
        self.assertIn("NVIDIA is the capstone task, not the whole workshop", slide)
        self.assertIn("AI_AGENTS_WORKSHOP.ipynb", slide)

    def test_api_anatomy_and_four_live_experiences_are_structured(self) -> None:
        slide = self.deck.split('data-title="API anatomy"', 1)[1].split("</section>", 1)[0]
        for field in ("model", "system", "messages", "tools", "max_tokens"):
            self.assertIn(f'data-api-field="{field}"', slide)
        self.assertIn("initApiAnatomy", self.html)
        self.assertEqual(self.deck.count("data-live-claude"), 2)
        self.assertEqual(self.deck.count("data-live-web-research"), 1)
        self.assertEqual(self.deck.count("data-live-agent"), 1)
        self.assertGreaterEqual(self.deck.count('class="contract-strip"'), 5)
        self.assertIn("normaliseWebEvents", self.html)

    def test_retrieval_systems_mcp_and_handoff_are_coherent(self) -> None:
        expected = (
            "Retrieval-Augmented Generation",
            "It does not retrain the model",
            "retrieve-then-generate pattern",
            "RESEARCHER",
            "PLANNER",
            "REVIEWER",
            "Multi-agent systems",
            "MCP standardises discovery",
            "Make your agent yours",
            "Frameworks package ideas",
            "LIVE DEMOS",
        )
        for text in expected:
            self.assertIn(text, self.deck)
        self.assertNotIn('data-title="Claude managed agents"', self.deck)
        self.assertNotIn("managed execution", self.deck.lower())
        self.assertEqual(self.titles[-3:], ["Make your agent yours", "Next steps", "Live demos"])

    def test_rag_has_four_plain_english_stages_and_visible_limits(self) -> None:
        slide = self.deck.split('data-title="RAG in plain English"', 1)[1].split("</section>", 1)[0]
        for stage in ("Ask", "Retrieve", "Add context", "Generate + cite"):
            self.assertIn(stage, slide)
        self.assertEqual(slide.count('class="rag-step"'), 4)
        self.assertIn("does not retrain the model", slide)
        self.assertIn("Weak retrieval creates weak grounding", slide)
        self.assertIn("missing evidence stays visible", slide)
        self.assertIn("Course-document search and live web search", slide)

    def test_generator_evaluator_has_fixed_routing_and_targeted_feedback(self) -> None:
        slide = self.deck.split('data-title="Generator and evaluator"', 1)[1].split("</section>", 1)[0]
        for criterion in (
            "Within AU$120",
            "Opening hours verified",
            "Travel time feasible",
            "Walking limit met?",
            "Vegetarian lunch",
            "Indoor backup",
            "Claims cited",
        ):
            self.assertIn(criterion, slide)
        self.assertIn("pass → user", slide)
        self.assertIn("fail → one targeted revision", slide)
        self.assertIn("final human judgment", slide)
        self.assertIn("data-eval-reveal", slide)
        self.assertIn("Targeted revision", self.html)
        self.assertIn("Revised output status", self.html)

    def test_live_calls_never_fail_silently(self) -> None:
        for message in (
            "Connecting to Claude…",
            "Claude returned an empty response. Check the API status and try again.",
            "Generation stopped before a response arrived.",
            "API key rejected",
            "API error",
        ):
            self.assertIn(message, self.html)
        self.assertIn("/api/health?validate=true", self.html)
        self.assertIn("/api/claude/stream", self.html)
        self.assertIn("/api/agent/web-research", self.html)

    def test_accessible_navigation_and_no_speaker_notes(self) -> None:
        for removed in ("data-notes=", "notesPanel", "toggleNotes", "presenter notes"):
            self.assertNotIn(removed, self.html)
        self.assertIn("aria-live=\"polite\"", self.deck)
        self.assertIn("focus-visible", self.html)
        self.assertIn("prefers-reduced-motion", self.html)
        self.assertIn("@media print", self.html)
        self.assertIn("requestFullscreen", self.html)
        self.assertIn("overviewPanel", self.html)

    def test_no_em_dashes_anywhere_in_the_deck(self) -> None:
        self.assertNotIn("—", self.html)

    def test_notebook_builds_research_then_grounded_generation(self) -> None:
        notebook = json.loads((ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        self.assertIn("NVIDIA Research Lab", source)
        self.assertEqual(source.count("def build_research_prompt"), 1)
        self.assertEqual(source.count("def build_briefing_prompt"), 1)
        self.assertIn('def build_research_prompt():\n    return """\n""".strip()', source)
        self.assertIn('def build_briefing_prompt(research):\n    return """\n""".strip()', source)
        self.assertIn("def run_research_agent", source)
        self.assertIn("def run_briefing_editor", source)
        self.assertIn("research_v1", source)
        self.assertIn("research_v2", source)
        self.assertIn("briefing_v1", source)
        self.assertIn("briefing_v2", source)
        self.assertIn("pause_turn", source)
        self.assertIn("DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH", source)
        self.assertIn("load_dotenv('.env', override=True)", source)
        self.assertNotIn("—", source)
        for name in ("Maya", "Noah", "Priya", "Aisha"):
            self.assertNotIn(name, source)
        for removed in ("cits2200", "hist2001", "econ1101", "comm1001", "dijkstra"):
            self.assertNotIn(removed, source.lower())

        for cell in notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue
            python_source = "\n".join(
                line for line in "".join(cell.get("source", [])).splitlines()
                if not line.lstrip().startswith("%")
            )
            ast.parse(python_source)

    def test_health_explains_credential_source(self) -> None:
        result = health(validate=False)
        self.assertIn(result["credential_source"], ("local .env", "host environment"))
        self.assertIn("authenticated", result)


class StudentAgentToolTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("WORKSHOP_SIMULATE_PLANNER_FAILURE", None)
        os.environ.pop("WORKSHOP_SIMULATE_RETRIEVAL_FAILURE", None)

    def test_planner_tool_contracts_are_complete(self) -> None:
        self.assertEqual(
            [tool.name for tool in workshopkit.PLANNER_TOOLS],
            [
                "get_deadlines",
                "get_calendar",
                "get_current_progress",
                "estimate_available_hours",
                "save_study_plan",
            ],
        )

    def test_deadlines_progress_calendar_and_capacity_are_consistent(self) -> None:
        deadlines = workshopkit.get_deadlines.execute({})
        progress = workshopkit.get_current_progress.execute({})
        calendar = workshopkit.get_calendar.execute({})
        capacity = workshopkit.estimate_available_hours.execute({"buffer_hours": 2})
        self.assertEqual(len(deadlines["deadlines"]), 4)
        self.assertEqual(len(progress["progress"]), 4)
        self.assertEqual(calendar["week"], capacity["week"])
        self.assertGreater(capacity["available_hours"], capacity["plannable_hours"])
        self.assertEqual(capacity["recommended_buffer_hours"], 2)
        self.assertFalse(deadlines["is_live_lms_data"])
        self.assertFalse(calendar["is_live_calendar_data"])

    def test_unit_filters_are_deterministic(self) -> None:
        deadlines = workshopkit.get_deadlines.execute({"unit_code": "mgmt2002"})
        progress = workshopkit.get_current_progress.execute({"unit_code": "MGMT2002"})
        self.assertEqual([item["unit_code"] for item in deadlines["deadlines"]], ["MGMT2002"])
        self.assertEqual([item["unit_code"] for item in progress["progress"]], ["MGMT2002"])

    def test_save_requires_approval(self) -> None:
        plan = [{"day": "Monday", "time": "08:00-09:30", "focus": "MGMT2002"}]
        preview = workshopkit.save_study_plan.execute({"plan": plan})
        self.assertEqual(preview["status"], "approval_required")
        self.assertFalse(preview["is_real_calendar_action"])
        self.assertNotIn("confirmed", workshopkit.save_study_plan.input_schema["properties"])

    def test_planner_failure_is_observable(self) -> None:
        os.environ["WORKSHOP_SIMULATE_PLANNER_FAILURE"] = "1"
        result = workshopkit.get_deadlines.execute({})
        self.assertFalse(result["ok"])
        self.assertIn("unavailable", result["error"])

    def test_course_retrieval_names_the_source(self) -> None:
        result = workshopkit.search_course_notes.execute(
            {"query": "situational leadership readiness", "unit_code": "MGMT2002", "top_k": 3}
        )
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["source"], "lecture_04_notes.txt")
        self.assertIn("situational leadership", result["results"][0]["text"].lower())

    def test_flashcards_are_grounded(self) -> None:
        mastery = workshopkit.get_mastery_record.execute({})
        self.assertEqual(mastery["topics"]["leadership styles"], 4)
        no_source = workshopkit.generate_flashcards.execute({"topic": "team dynamics", "source_excerpt": ""})
        wrong_source = workshopkit.generate_flashcards.execute(
            {"topic": "team dynamics", "source_excerpt": "Situational leadership adjusts style to readiness."}
        )
        cards = workshopkit.generate_flashcards.execute(
            {
                "topic": "leadership styles",
                "source_excerpt": "Situational leadership adjusts style to a follower's readiness. Transformational and transactional leadership differ.",
                "count": 2,
            }
        )
        self.assertFalse(no_source["ok"])
        self.assertFalse(wrong_source["ok"])
        self.assertTrue(cards["grounded_in_supplied_excerpt"])
        self.assertEqual(cards["status"], "self_study_only")
        self.assertEqual(len(cards["cards"]), 2)
        self.assertIn("front", cards["cards"][0])
        self.assertIn("back", cards["cards"][0])

    def test_retrieval_failure_is_observable(self) -> None:
        os.environ["WORKSHOP_SIMULATE_RETRIEVAL_FAILURE"] = "1"
        result = workshopkit.search_course_notes.execute({"query": "leadership"})
        self.assertFalse(result["ok"])
        self.assertIn("unavailable", result["error"])

    def test_study_planner_wrapper_uses_planner_tools(self) -> None:
        with patch.object(workshopkit, "run_agent", return_value={"ok": True, "events": []}) as run_mock:
            result = workshopkit.run_study_planner("instructions", "task")
        self.assertTrue(result["ok"])
        self.assertEqual(run_mock.call_args.kwargs["tools"], workshopkit.PLANNER_TOOLS)

    def test_tutor_and_flashcard_wrappers_use_the_expected_tools(self) -> None:
        with patch.object(workshopkit, "run_agent", return_value={"ok": True, "events": []}) as run_mock:
            workshopkit.run_tutor_agent("instructions", "task")
            self.assertEqual(run_mock.call_args.kwargs["tools"], workshopkit.TUTOR_TOOLS)
            workshopkit.run_flashcard_agent("instructions", "task")
            self.assertEqual(run_mock.call_args.kwargs["tools"], workshopkit.FLASHCARD_TOOLS)

    def test_manager_uses_the_specialists(self) -> None:
        with patch.object(workshopkit, "run_agent", return_value={"ok": True, "events": []}) as run_mock:
            workshopkit.run_manager("instructions", "task")
        self.assertEqual(run_mock.call_args.kwargs["tools"], workshopkit.SPECIALISTS)
        self.assertEqual([tool.name for tool in workshopkit.SPECIALISTS], ["researcher", "planner", "reviewer"])

    def test_live_endpoint_executes_a_planner_tool_and_returns_the_trace(self) -> None:
        class Block:
            def __init__(self, block_type: str, **values) -> None:
                self.type = block_type
                for key, value in values.items():
                    setattr(self, key, value)

        class FakeMessages:
            def __init__(self) -> None:
                self.calls = 0

            def create(self, **_) -> object:
                self.calls += 1
                if self.calls == 1:
                    return type("Response", (), {
                        "content": [Block("tool_use", id="tool-1", name="get_deadlines", input={})]
                    })()
                return type("Response", (), {
                    "content": [Block("text", text="Start with the earliest unfinished deadline.")]
                })()

        fake_client = type("Client", (), {"messages": FakeMessages()})()
        with patch.object(server, "client", return_value=fake_client):
            response = server.study_session_agent(
                server.AgentRequest(task="Plan my week", instructions="Inspect deadlines before planning.")
            )
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertEqual(body["tool_calls"], 1)
        self.assertEqual([event["type"] for event in body["events"]], ["user", "tool", "result", "final"])
        self.assertEqual(body["events"][1]["name"], "get_deadlines")


class ResearchRuntimeTests(unittest.TestCase):
    class Block:
        def __init__(self, block_type: str, **values) -> None:
            self.type = block_type
            for key, value in values.items():
                setattr(self, key, value)

        def model_dump(self, exclude_none: bool = True) -> dict:
            return vars(self)

    class Usage:
        def __init__(self, searches: int = 0) -> None:
            self.input_tokens = 120
            self.output_tokens = 340
            self.server_tool_use = {"web_search_requests": searches}

        def model_dump(self, exclude_none: bool = True) -> dict:
            return vars(self)

    class Response:
        def __init__(self, content, stop_reason="end_turn", searches=0) -> None:
            self.content = content
            self.stop_reason = stop_reason
            self.usage = ResearchRuntimeTests.Usage(searches)

    class Messages:
        def __init__(self, responses) -> None:
            self.responses = list(responses)
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    def response(self, stop_reason="end_turn"):
        citation = {"title": "NVIDIA filing", "url": "https://example.com/10k", "page_age": "2026-08-20"}
        return self.Response([
            self.Block("server_tool_use", name="web_search", input={"query": "NVIDIA current risks"}),
            self.Block("web_search_tool_result", content=[citation]),
            self.Block("text", text="Evidence-backed NVIDIA research.", citations=[citation]),
        ], stop_reason=stop_reason, searches=1)

    def client(self, *responses):
        return type("Client", (), {"messages": self.Messages(responses)})()

    def test_research_extracts_search_source_text_and_usage(self) -> None:
        result = workshopkit.run_research_agent("instructions", "task", client=self.client(self.response()))
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["sources"][0]["url"], "https://example.com/10k")
        self.assertEqual(result["usage"]["web_search_requests"], 1)
        self.assertEqual([event["type"] for event in result["events"]], ["user", "search", "source", "final", "usage"])

    def test_research_cap_and_pause_turn(self) -> None:
        paused = self.Response([self.Block("text", text="Partial", citations=[])], stop_reason="pause_turn")
        api = self.client(paused, self.response())
        result = workshopkit.run_research_agent("instructions", "task", max_searches=99, client=api)
        self.assertEqual(api.messages.calls[0]["tools"][0]["max_uses"], workshopkit.MAX_SEARCHES)
        self.assertEqual(len(api.messages.calls), 2)
        self.assertIn("Partial", result["text"])

    def test_empty_or_failed_search_uses_dated_fallback(self) -> None:
        empty = workshopkit.run_research_agent("instructions", "task", client=self.client(self.Response([])))
        failing_messages = type("Messages", (), {"create": lambda *_args, **_kwargs: (_ for _ in ()).throw(ConnectionError())})()
        failing_client = type("Client", (), {"messages": failing_messages})()
        failed = workshopkit.run_research_agent("instructions", "task", client=failing_client)
        for result in (empty, failed):
            self.assertTrue(result["fallback_used"])
            self.assertIn("DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH", result["text"])

    def test_perth_web_research_selects_its_own_dated_fallback(self) -> None:
        result = workshopkit.run_web_research_agent(
            "Use official sources.",
            "Build the Perth plan.",
            client=self.client(self.Response([])),
        )
        self.assertTrue(result["fallback_used"])
        self.assertIn("Perth", result["text"])
        self.assertIn("5 September 2026", result["text"])
        self.assertNotIn("NVIDIA Research Snapshot", result["text"])
        self.assertEqual(result["stop_reason"], "fallback")
        self.assertEqual(result["events"][-1]["type"], "usage")
        self.assertEqual(result["events"][-1]["web_search_requests"], 0)

    def test_perth_web_research_preserves_search_citations_and_pause_turn(self) -> None:
        paused = self.Response([self.Block("text", text="Partial Perth research", citations=[])], stop_reason="pause_turn")
        citation = {"title": "Official Perth venue", "url": "https://example.com/perth", "page_age": "2026-08-25"}
        finished = self.Response([
            self.Block("server_tool_use", name="web_search", input={"query": "Perth official venue hours"}),
            self.Block("web_search_tool_result", content=[citation]),
            self.Block("text", text="Feasible Perth itinerary.", citations=[citation]),
        ], searches=1)
        result = workshopkit.run_web_research_agent(
            "Use official sources.", "Build the Perth plan.", client=self.client(paused, finished)
        )
        self.assertFalse(result["fallback_used"])
        self.assertIn("Partial Perth research", result["text"])
        self.assertEqual(result["sources"][0]["url"], "https://example.com/perth")
        self.assertIn("search", [event["type"] for event in result["events"]])

    def test_authentication_and_rate_limit_failures_are_named(self) -> None:
        class AuthenticationFailure(Exception):
            pass

        class RateLimitFailure(Exception):
            pass

        for failure in (AuthenticationFailure(), RateLimitFailure()):
            with self.subTest(failure=type(failure).__name__):
                messages = type("Messages", (), {"create": lambda *_args, **_kwargs: (_ for _ in ()).throw(failure)})()
                result = workshopkit.run_research_agent("instructions", "task", client=type("Client", (), {"messages": messages})())
                self.assertTrue(result["fallback_used"])
                self.assertIn(type(failure).__name__, result["events"][1]["message"])

    def test_perth_authentication_and_rate_limit_failures_are_named(self) -> None:
        class AuthenticationFailure(Exception):
            pass

        class RateLimitFailure(Exception):
            pass

        for failure in (AuthenticationFailure(), RateLimitFailure()):
            with self.subTest(failure=type(failure).__name__):
                messages = type("Messages", (), {"create": lambda *_args, **_kwargs: (_ for _ in ()).throw(failure)})()
                result = workshopkit.run_web_research_agent(
                    "Use official sources.", "Build the Perth plan.", client=type("Client", (), {"messages": messages})()
                )
                self.assertTrue(result["fallback_used"])
                self.assertIn(type(failure).__name__, result["events"][1]["message"])

    def test_briefing_editor_is_tool_free_and_preserves_sources(self) -> None:
        api = self.client(self.Response([self.Block("text", text="Neutral briefing", citations=[])]))
        research = {"text": "Verified research", "sources": [{"url": "https://example.com"}], "fallback_used": False}
        result = workshopkit.run_briefing_editor("instructions", research, client=api)
        self.assertNotIn("tools", api.messages.calls[0])
        self.assertEqual(result["sources"], research["sources"])

    def test_research_endpoint_and_health_expose_capstone_contract(self) -> None:
        expected = {"ok": True, "events": [], "sources": [], "usage": {}, "fallback_used": False}
        with patch.object(server, "api_key", return_value=""), patch.object(workshopkit, "run_research_agent", return_value=expected) as run_mock:
            response = server.research_agent(server.ResearchRequest(task="task", instructions="instructions", max_searches=2))
        self.assertEqual(json.loads(response.body), expected)
        self.assertEqual(run_mock.call_args.kwargs["max_searches"], 2)
        self.assertEqual(server.health(validate=False)["web_search_max"], 5)

    def test_perth_endpoint_forwards_the_bounded_search_contract(self) -> None:
        expected = {
            "ok": True,
            "model": "test-model",
            "events": [],
            "sources": [],
            "usage": {},
            "stop_reason": "end_turn",
            "text": "plan",
            "fallback_used": False,
        }
        with patch.object(server, "api_key", return_value=""), patch.object(
            workshopkit, "run_web_research_agent", return_value=expected
        ) as run_mock:
            response = server.web_research_agent(
                server.ResearchRequest(task="Perth plan", instructions="Use official sources", max_searches=3)
            )
        self.assertEqual(json.loads(response.body), expected)
        self.assertEqual(run_mock.call_args.kwargs["max_searches"], 3)
        self.assertEqual(run_mock.call_args.args[1], "Perth plan")


if __name__ == "__main__":
    unittest.main()
