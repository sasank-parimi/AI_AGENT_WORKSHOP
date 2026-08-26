from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import workshopkit
from server import find_study_room, health

ROOT = Path(__file__).resolve().parents[1]


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.deck = cls.html.split('<main class="deck notebook-deck" id="deck">', 1)[1].split("</main>", 1)[0]
        cls.titles = re.findall(r'data-title="([^"]+)"', cls.deck)

    def test_deck_has_forty_two_titled_states(self) -> None:
        slides = re.findall(r'<section class="slide[^>]*>', self.deck)
        self.assertEqual(len(slides), 42)
        self.assertEqual(len(slides), len(self.titles))

    def test_opening_and_revised_sequence(self) -> None:
        self.assertEqual(self.titles[:2], ["AI Agent Workshop", "What is AI?"])
        self.assertIn("AI AGENT WORKSHOP", self.deck)
        self.assertIn('What <span class="question-emphasis">IS</span> AI?', self.deck)
        self.assertLess(self.titles.index("RECIPE prompt framework"), self.titles.index("Prompt builder"))
        self.assertLess(self.titles.index("The loop"), self.titles.index("Build an adaptive revision coach"))
        self.assertIn("What changes when the model sees an example?", self.deck)
        self.assertIn("Context engineering", self.titles)
        self.assertIn("Working context", self.titles)

    def test_recipe_is_clickable_and_clearly_attributed(self) -> None:
        for ingredient in ("role", "examples", "context", "instructions", "parameters", "examine"):
            self.assertIn(f'data-recipe="{ingredient}"', self.deck)
        self.assertIn("initRecipeFramework", self.html)
        self.assertIn("workshop mnemonic, not an official Anthropic acronym", self.deck)

    def test_audience_deck_contains_no_speaker_notes(self) -> None:
        for removed in ("data-notes=", "notesPanel", "toggleNotes", "presenter notes", "legacyDeck"):
            self.assertNotIn(removed, self.html)

    def test_student_scenarios_remain_authentic_and_linked(self) -> None:
        for name in ("Maya", "Noah", "Priya", "Aisha"):
            self.assertIn(name, self.deck)
        for unrelated in ("cybersecurity", "recruitment", "startup", "weather", "Jira"):
            self.assertNotIn(unrelated.lower(), self.deck.lower())
        self.assertNotIn("Claude Projects", self.deck)
        self.assertNotIn("scheduled task", self.deck.lower())

    def test_chapter_progression_never_moves_backwards(self) -> None:
        sections = re.findall(r'<section class="slide[^>]*data-section="([^"]+)"', self.deck)
        order = {name: index for index, name in enumerate(("prompt", "context", "tools", "agents", "knowledge", "mcp"))}
        self.assertTrue(all(order[left] <= order[right] for left, right in zip(sections, sections[1:])))

    def test_live_interfaces_and_observable_trace_are_present(self) -> None:
        self.assertIn("/api/claude/stream", self.html)
        self.assertIn("/api/agent/study-session", self.html)
        self.assertIn("data-agent-trace", self.deck)
        self.assertIn("hidden chain-of-thought", self.deck)
        self.assertIn("/api/health?validate=true", self.html)
        self.assertIn("API KEY REJECTED", self.html)

    def test_notebook_is_valid_and_uses_three_prompt_study_build(self) -> None:
        notebook = json.loads((ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        self.assertIn("load_dotenv('.env', override=True)", source)
        self.assertIn("from workshopkit import *", source)
        self.assertIn("Leadership in Organisations", source)
        self.assertIn("AGENT_INSTRUCTIONS", source)
        self.assertIn("STUDENT_REQUEST", source)
        self.assertIn("QUALITY_PROMPT", source)
        self.assertIn("run_study_coach", source)
        self.assertNotIn("NOAH_INSTRUCTIONS", source)
        self.assertNotIn("MAYA_REQUEST", source)

    def test_health_explains_credential_source(self) -> None:
        result = health(validate=False)
        self.assertIn(result["credential_source"], ("local .env", "host environment"))
        self.assertIn("authenticated", result)


class SimulatedToolTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("WORKSHOP_SIMULATE_ROOM_FAILURE", None)
        os.environ.pop("WORKSHOP_SIMULATE_STUDY_DATA_FAILURE", None)

    def test_accessible_room_match(self) -> None:
        result = find_study_room(
            date="next Tuesday",
            time="15:00",
            group_size=5,
            duration_minutes=120,
            accessibility_required=True,
        )
        self.assertFalse(result["is_live_booking_data"])
        self.assertEqual(result["matches"][0]["room"], "Bayliss 2.24")
        self.assertTrue(result["matches"][0]["accessible"])

    def test_no_match_is_explicit(self) -> None:
        result = find_study_room(
            date="Monday",
            time="09:00",
            group_size=30,
            accessibility_required=True,
        )
        self.assertEqual(result["matches"], [])
        self.assertIn("suggestion", result)

    def test_room_failure_is_observable(self) -> None:
        os.environ["WORKSHOP_SIMULATE_ROOM_FAILURE"] = "1"
        result = workshopkit.find_study_room.execute(
            {"date": "Tuesday", "time": "15:00", "group_size": 5}
        )
        self.assertFalse(result["ok"])
        self.assertIn("unavailable", result["error"])

    def test_weak_mixed_and_strong_mastery_profiles(self) -> None:
        profiles = {
            name: workshopkit.get_mastery_record.execute({"profile": name})
            for name in ("weak", "mixed", "strong")
        }
        self.assertLess(profiles["weak"]["scores"]["motivation"], profiles["strong"]["scores"]["motivation"])
        self.assertEqual(profiles["mixed"]["scores"]["psychological safety"], 5)
        self.assertEqual(profiles["mixed"]["source"], "fictional workshop mastery data")

    def test_study_data_failure_is_observable(self) -> None:
        os.environ["WORKSHOP_SIMULATE_STUDY_DATA_FAILURE"] = "1"
        mastery = workshopkit.get_mastery_record.execute({"profile": "mixed"})
        search = workshopkit.search_leadership_notes.execute({"query": "motivation"})
        self.assertFalse(mastery["ok"])
        self.assertFalse(search["ok"])
        self.assertIn("unavailable", mastery["error"])

    def test_leadership_search_and_study_tools_are_grounded(self) -> None:
        search = workshopkit.search_leadership_notes.execute({"query": "motivation autonomy competence"})
        self.assertTrue(search["results"])
        self.assertEqual(search["source"], "leadership_revision_notes.txt")
        excerpt = search["results"][0]["text"]
        cards = workshopkit.draft_flashcards.execute({"topic": "motivation", "source_excerpt": excerpt, "count": 3})
        questions = workshopkit.draft_practice_questions.execute({"topic": "motivation", "source_excerpt": excerpt})
        self.assertEqual(cards["source_section"], "Motivation")
        self.assertEqual(len(cards["cards"]), 3)
        self.assertEqual(questions["status"], "formative_practice_only")
        self.assertTrue(questions["questions"])

    def test_study_generation_requires_retrieval(self) -> None:
        cards = workshopkit.draft_flashcards.execute({"topic": "motivation", "source_excerpt": ""})
        self.assertFalse(cards["ok"])
        self.assertIn("retrieved source", cards["error"])

    def test_run_study_coach_appends_quality_event(self) -> None:
        agent_result = {
            "ok": True,
            "model": "test-model",
            "events": [
                {"type": "user", "text": "Study motivation"},
                {"type": "final", "text": "A source-grounded study pack"},
            ],
        }
        with patch.object(workshopkit, "run_agent", return_value=agent_result) as run_mock, patch.object(
            workshopkit, "ask_claude", return_value="PASS — grounded and appropriately scoped"
        ):
            result = workshopkit.run_study_coach("instructions", "task", "quality criteria")
        self.assertTrue(result["ok"])
        self.assertEqual(result["events"][-1]["type"], "quality")
        self.assertEqual(run_mock.call_args.kwargs["tools"], workshopkit.STUDY_COACH_TOOLS)

    def test_quality_check_failure_is_observable(self) -> None:
        agent_result = {
            "ok": True,
            "model": "test-model",
            "events": [{"type": "final", "text": "Study pack"}],
        }
        with patch.object(workshopkit, "run_agent", return_value=agent_result), patch.object(
            workshopkit, "ask_claude", side_effect=RuntimeError("simulated evaluator failure")
        ):
            result = workshopkit.run_study_coach("instructions", "task", "quality criteria")
        self.assertFalse(result["ok"])
        self.assertIn("Quality check failed", result["events"][-1]["message"])

    def test_retrieval_names_sources(self) -> None:
        result = workshopkit.search_student_docs.execute(
            {"query": "extension before deadline", "top_k": 2}
        )
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["source"], "assessment_policy.txt")


if __name__ == "__main__":
    unittest.main()
