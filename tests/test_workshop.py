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
        self.assertIn("Build an agent you can actually keep using", self.deck)
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

    def test_prompt_challenge_offers_two_scenarios(self) -> None:
        slide = self.deck.split('data-title="Prompt challenge"', 1)[1].split("</section>", 1)[0]
        self.assertIn("data-scenario-picker", slide)
        self.assertEqual(slide.count("data-scenario="), 2)
        self.assertIn("Leadership case study", slide)
        self.assertIn("Organisational behaviour group task", slide)
        self.assertIn("initScenarioPicker", self.html)

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
        order = {name: index for index, name in enumerate(("ai", "prompt", "craft", "context", "agents", "build", "systems", "next"))}
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

    def test_notebook_handoff_lists_three_agents(self) -> None:
        slide = self.deck.split('data-title="Build your own agents"', 1)[1].split("</section>", 1)[0]
        self.assertIn("Tutor Agent", slide)
        self.assertIn("Flashcard Agent", slide)
        self.assertIn("Study Planner Agent", slide)
        self.assertIn("generate_flashcards", slide)
        self.assertIn("AI_AGENTS_WORKSHOP.ipynb", slide)

    def test_retrieval_systems_mcp_and_handoff_are_coherent(self) -> None:
        expected = (
            "Your agent does not know your unit",
            "Retrieval-Augmented Generation",
            "RESEARCHER",
            "PLANNER",
            "REVIEWER",
            "Multi-agent systems",
            "MCP standardises discovery",
            "Claude can run the agent loop for you",
            "Make your agent yours",
            "Frameworks package ideas",
            "LIVE DEMOS",
        )
        for text in expected:
            self.assertIn(text, self.deck)
        self.assertEqual(self.titles[-3:], ["Make your agent yours", "Next steps", "Live demos"])

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

    def test_notebook_builds_three_independent_agents(self) -> None:
        notebook = json.loads((ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        self.assertIn("Build three agents", source)
        self.assertIn("Agent 1: Personalised Tutor Agent", source)
        self.assertIn("Agent 2: Flashcard Generator Agent", source)
        self.assertIn("Agent 3: Study Planner Agent", source)
        self.assertIn("TUTOR_INSTRUCTIONS", source)
        self.assertIn("FLASHCARD_INSTRUCTIONS", source)
        self.assertIn("PLANNER_INSTRUCTIONS", source)
        self.assertIn("run_tutor_agent", source)
        self.assertIn("run_flashcard_agent", source)
        self.assertIn("run_study_planner", source)
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


if __name__ == "__main__":
    unittest.main()
