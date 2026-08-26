from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import server
import workshopkit

ROOT = Path(__file__).resolve().parents[1]


class Block:
    def __init__(self, block_type: str, **values) -> None:
        self.type = block_type
        for key, value in values.items():
            setattr(self, key, value)

    def model_dump(self, exclude_none: bool = True) -> dict:
        return {key: value for key, value in vars(self).items() if not exclude_none or value is not None}


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
        self.usage = Usage(searches)


class FakeMessages:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


def fake_client(*responses):
    return type("Client", (), {"messages": FakeMessages(responses)})()


def research_response(stop_reason="end_turn"):
    citation = {
        "type": "web_search_result_location",
        "title": "NVIDIA annual report",
        "url": "https://example.com/nvidia-10k",
        "page_age": "2026-08-20",
    }
    return Response(
        [
            Block("server_tool_use", name="web_search", input={"query": "NVIDIA latest 10-K risks"}),
            Block(
                "web_search_tool_result",
                content=[{"type": "web_search_result", "title": "NVIDIA annual report", "url": "https://example.com/nvidia-10k", "page_age": "2026-08-20"}],
            ),
            Block("text", text="## Executive summary\nEvidence-backed result.", citations=[citation]),
        ],
        stop_reason=stop_reason,
        searches=1,
    )


class DeckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.deck = cls.html.split('<main class="deck" id="deck">', 1)[1].split("</main>", 1)[0]
        cls.titles = re.findall(r'data-title="([^"]+)"', cls.deck)

    def test_deck_is_a_tight_research_lab(self) -> None:
        self.assertEqual(len(re.findall(r'<section class="slide', self.deck)), 24)
        self.assertEqual(self.titles[:4], ["AI Agent Research Lab", "The mission", "Classify the system", "One coherent pipeline"])
        self.assertEqual(self.titles[-2:], ["What you can now explain", "Research you can defend"])

    def test_story_is_one_nvidia_pipeline(self) -> None:
        for phrase in (
            "RESEARCH AGENT",
            "VERIFIED RESEARCH",
            "BRIEFING EDITOR",
            "What could drive or derail NVIDIA",
            "Two stages, one evidence trail",
        ):
            self.assertIn(phrase, self.deck)
        for removed in ("Tutor Agent", "Flashcard Agent", "Study Planner", "student deadlines", "mastery record"):
            self.assertNotIn(removed.lower(), self.html.lower())

    def test_craft_and_api_anatomy_are_interactive(self) -> None:
        for letter, label in zip("CRAFT", ("Context", "Request", "Approach", "Format", "Test")):
            self.assertIn(f">{letter}</b><h3>{label}</h3>", self.deck)
        for field in ("model", "system", "messages", "tools", "max_tokens"):
            self.assertIn(f'data-field="{field}"', self.deck)
        self.assertIn("initCraft", self.html)
        self.assertIn("initRequest", self.html)

    def test_requested_interactions_exist(self) -> None:
        for marker in (
            "data-classifier",
            "data-source-sort",
            "data-live-research",
            "data-trail",
            "data-checklist",
            'class="compare"',
        ):
            self.assertIn(marker, self.deck)

    def test_live_research_uses_new_endpoint_and_structured_events(self) -> None:
        self.assertIn("/api/agent/research", self.html)
        for event in ("search", "source", "final", "usage", "error"):
            self.assertIn(f"kind==='{event}'" if event in {"source", "search", "usage"} else event, self.html)
        self.assertIn("max_searches:3", self.html)
        self.assertNotIn("/api/agent/study-session", self.html)

    def test_finance_boundaries_and_fallback_are_explicit(self) -> None:
        for phrase in (
            "No recommendation or price target",
            "No personalised advice",
            "DECORATIVE ONLY · NO MARKET DATA",
            "Dated fallback loaded",
        ):
            self.assertIn(phrase.lower(), self.html.lower())

    def test_accessibility_navigation_and_responsive_rules_remain(self) -> None:
        for text in ("aria-live=\"polite\"", "focus-visible", "prefers-reduced-motion", "@media print", "requestFullscreen", "overviewList"):
            self.assertIn(text, self.html)

    def test_no_api_key_is_embedded_in_public_artifacts(self) -> None:
        notebook_text = (ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8")
        self.assertNotRegex(self.html + notebook_text, r"sk-ant-[A-Za-z0-9_-]{12,}")
        self.assertNotIn("your_workshop_key_here\nANTHROPIC", notebook_text)


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = json.loads((ROOT / "AI_AGENTS_WORKSHOP.ipynb").read_text(encoding="utf-8"))
        cls.source = "\n".join("".join(cell.get("source", [])) for cell in cls.notebook["cells"])

    def test_notebook_is_linear_and_owns_two_prompt_functions(self) -> None:
        self.assertIn("NVIDIA Research Lab", self.source)
        self.assertEqual(self.source.count("def build_research_prompt"), 1)
        self.assertEqual(self.source.count("def build_briefing_prompt"), 1)
        for helper in ("run_research_agent", "run_briefing_editor", "show_result", "score_output"):
            self.assertIn(f"def {helper}", self.source)
        for removed in ("run_tutor_agent", "run_flashcard_agent", "run_study_planner"):
            self.assertNotIn(removed, self.source)

    def test_notebook_shows_env_and_clean_api_request(self) -> None:
        self.assertIn("load_dotenv('.env', override=True)", self.source)
        self.assertIn("getpass('Anthropic API key: ')", self.source)
        self.assertIn("client = Anthropic", self.source)
        for field in ("model=MODEL", "max_tokens=1800", "system=system_prompt", "messages=messages", "tools=[WEB_SEARCH]"):
            self.assertIn(field, self.source)

    def test_notebook_requires_two_evaluation_cycles(self) -> None:
        for name in ("research_v1", "research_v2", "briefing_v1", "briefing_v2", "RESEARCH_CHECKLIST", "BRIEFING_CHECKLIST"):
            self.assertIn(name, self.source)
        self.assertGreaterEqual(self.source.count("score_output("), 5)

    def test_all_python_cells_parse(self) -> None:
        for cell in self.notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            python_source = "\n".join(line for line in source.splitlines() if not line.lstrip().startswith("%"))
            ast.parse(python_source)


class ResearchRuntimeTests(unittest.TestCase):
    def test_extracts_search_sources_text_and_usage(self) -> None:
        api = fake_client(research_response())
        result = workshopkit.run_research_agent("CRAFT instructions", "Research NVIDIA", client=api)
        self.assertTrue(result["ok"])
        self.assertFalse(result["fallback_used"])
        self.assertIn("Evidence-backed result", result["text"])
        self.assertEqual(result["sources"][0]["url"], "https://example.com/nvidia-10k")
        self.assertEqual(result["usage"]["web_search_requests"], 1)
        self.assertEqual([event["type"] for event in result["events"]], ["user", "search", "source", "final", "usage"])

    def test_search_is_bounded_in_request(self) -> None:
        api = fake_client(research_response())
        workshopkit.run_research_agent("instructions", "task", max_searches=99, client=api)
        self.assertEqual(api.messages.calls[0]["tools"][0]["max_uses"], workshopkit.MAX_SEARCHES)

    def test_pause_turn_is_continued(self) -> None:
        first = Response([Block("text", text="Partial", citations=[])], stop_reason="pause_turn")
        second = research_response()
        api = fake_client(first, second)
        result = workshopkit.run_research_agent("instructions", "task", client=api)
        self.assertEqual(len(api.messages.calls), 2)
        self.assertEqual(len(api.messages.calls[1]["messages"]), 2)
        self.assertIn("Partial", result["text"])

    def test_failures_and_empty_output_load_labelled_fallback(self) -> None:
        failing = type("Failing", (), {"messages": type("Messages", (), {"create": lambda *_a, **_k: (_ for _ in ()).throw(ConnectionError())})()})()
        failed = workshopkit.run_research_agent("instructions", "task", client=failing)
        empty = workshopkit.run_research_agent("instructions", "task", client=fake_client(Response([], searches=0)))
        for result in (failed, empty):
            self.assertTrue(result["fallback_used"])
            self.assertIn("DATED CLASSROOM FALLBACK - NOT LIVE RESEARCH", result["text"])
            self.assertEqual(result["stop_reason"], "fallback")

    def test_briefing_is_tool_free_and_preserves_sources(self) -> None:
        response = Response([Block("text", text="# Neutral watchlist briefing", citations=[])])
        api = fake_client(response)
        research = {"text": "Verified evidence", "sources": [{"title": "10-K", "url": "https://example.com"}], "fallback_used": False}
        result = workshopkit.run_briefing_editor("editor instructions", research, client=api)
        request = api.messages.calls[0]
        self.assertNotIn("tools", request)
        self.assertEqual(result["sources"], research["sources"])
        self.assertIn("Verified evidence", request["messages"][0]["content"])

    def test_fallback_file_is_dated_and_safe(self) -> None:
        text = workshopkit.FALLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("26 August 2026", text)
        self.assertIn("NOT LIVE RESEARCH", text)
        self.assertIn("not investment advice", text.lower())


class ServerTests(unittest.TestCase):
    def test_health_exposes_search_cap_and_credential_source(self) -> None:
        result = server.health(validate=False)
        self.assertEqual(result["web_search_max"], 5)
        self.assertIn(result["credential_source"], ("local .env", "host environment"))

    def test_research_endpoint_forwards_structured_request(self) -> None:
        expected = {"ok": True, "model": "model", "events": [], "sources": [], "usage": {}, "fallback_used": False}
        with patch.object(server, "api_key", return_value=""), patch.object(workshopkit, "run_research_agent", return_value=expected) as run_mock:
            response = server.research_agent(server.ResearchRequest(task="task", instructions="instructions", max_searches=2))
        body = json.loads(response.body)
        self.assertEqual(body, expected)
        self.assertEqual(run_mock.call_args.args[:2], ("instructions", "task"))
        self.assertEqual(run_mock.call_args.kwargs["max_searches"], 2)


if __name__ == "__main__":
    unittest.main()
