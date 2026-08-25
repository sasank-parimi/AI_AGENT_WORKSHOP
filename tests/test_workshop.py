from __future__ import annotations

import json
import os
import re
import unittest
from pathlib import Path

import workshopkit
from server import find_study_room

ROOT = Path(__file__).resolve().parents[1]


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.deck = cls.html.split('<main class="deck notebook-deck" id="deck">', 1)[1].split("</main>", 1)[0]

    def test_deck_has_roughly_forty_titled_states(self) -> None:
        slides = re.findall(r'<section class="slide[^>]*>', self.deck)
        self.assertGreaterEqual(len(slides), 38)
        self.assertLessEqual(len(slides), 42)
        self.assertEqual(len(slides), self.deck.count("data-title="))

    def test_deck_uses_only_the_three_student_stories(self) -> None:
        for name in ("Maya", "Noah", "Priya"):
            self.assertIn(name, self.deck)
        for unrelated in ("cybersecurity", "recruitment", "startup", "weather", "Jira"):
            self.assertNotIn(unrelated.lower(), self.deck.lower())

    def test_chapter_progression_never_moves_backwards(self) -> None:
        sections = re.findall(r'<section class="slide[^>]*data-section="([^"]+)"', self.deck)
        order = {name: index for index, name in enumerate(("prompt", "context", "tools", "agents", "knowledge", "mcp"))}
        self.assertTrue(all(order[left] <= order[right] for left, right in zip(sections, sections[1:])))

    def test_live_interfaces_and_observable_trace_are_present(self) -> None:
        self.assertIn("/api/claude/stream", self.html)
        self.assertIn("/api/agent/study-session", self.html)
        self.assertIn("data-agent-trace", self.deck)
        self.assertIn("hidden chain-of-thought", self.deck)

    def test_notebook_is_valid_and_uses_local_runtime(self) -> None:
        notebook = json.loads((ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8"))
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        self.assertIn("from workshopkit import *", source)
        self.assertIn("Maya", source)
        self.assertIn("Noah", source)
        self.assertIn("Priya", source)


class SimulatedToolTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("WORKSHOP_SIMULATE_ROOM_FAILURE", None)

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

    def test_failure_is_observable(self) -> None:
        os.environ["WORKSHOP_SIMULATE_ROOM_FAILURE"] = "1"
        result = workshopkit.find_study_room.execute(
            {"date": "Tuesday", "time": "15:00", "group_size": 5}
        )
        self.assertFalse(result["ok"])
        self.assertIn("unavailable", result["error"])

    def test_retrieval_names_sources(self) -> None:
        result = workshopkit.search_student_docs.execute(
            {"query": "extension before deadline", "top_k": 2}
        )
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["source"], "assessment_policy.txt")


if __name__ == "__main__":
    unittest.main()
