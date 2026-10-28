import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import ofrenda  # noqa: E402


class GroundedTest(unittest.TestCase):
    def test_drops_items_not_in_transcript(self):
        t = "She made tamales every Sunday and sang Cielito Lindo in Oaxaca."
        card = {"foods": ["tamales", "mole poblano"], "songs": ["Cielito Lindo", "La Bamba"],
                "places": ["Oaxaca", "Paris"], "sayings": []}
        out = ofrenda.grounded(card, t)
        self.assertEqual(out["foods"], ["tamales"])
        self.assertEqual(out["songs"], ["Cielito Lindo"])
        self.assertEqual(out["places"], ["Oaxaca"])

    def test_render_escapes_html(self):
        card = {"name": "<b>Rosa</b>", "relation": "grandmother", "remembrance": "x", "foods": [],
                "songs": [], "places": [], "sayings": [], "model": "gemma"}
        page = ofrenda.render(card, "<script>")
        self.assertNotIn("<b>Rosa</b>", page)
        self.assertNotIn("<script>", page)
        self.assertIn("(not mentioned)", page)


if __name__ == "__main__":
    unittest.main()
