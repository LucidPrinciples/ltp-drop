"""Drop page: triad chrome (Key after header, before coaching)."""
from __future__ import annotations

import unittest
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "public" / "index.html"


class DropPageOrderTests(unittest.TestCase):
    def test_static_markup_puts_key_before_coaching(self) -> None:
        src = HTML.read_text(encoding="utf-8")
        key = src.index('id="keyBlock"')
        coach = src.index('id="coachBlock"')
        practice = src.index('id="practiceBlock"')
        self.assertLess(key, coach)
        self.assertLess(coach, practice)

    def test_renderer_emits_key_before_coaching(self) -> None:
        src = HTML.read_text(encoding="utf-8")
        start = src.index("function renderDropInto")
        body = src[start : src.index("function renderMainPage", start)]
        key_at = body.index("Tuning key — triad chrome")
        coach_at = body.index("// Coaching")
        practice_at = body.index("// Practice")
        self.assertLess(key_at, coach_at)
        self.assertLess(coach_at, practice_at)
        self.assertEqual(body.count("ot-card ot-key"), 1)
        self.assertIn("formatProse(coaching)", body)
        self.assertIn("formatKey(keyText)", body)
        self.assertNotIn("ALIGNMENT", body)
        self.assertNotIn("' ALIGNMENT'", src)
        self.assertNotIn('" ALIGNMENT"', src)


if __name__ == "__main__":
    unittest.main()
