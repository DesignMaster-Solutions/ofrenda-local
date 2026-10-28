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

    def test_keeps_three_sentences_and_drops_prompt_echo(self):
        txt = "She cooked. She sang. She said 'Ve con Dios, mijo.' 3 warm sentences in the speaker's voice. 3 warm"
        self.assertEqual(ofrenda.three_sentences(txt), "She cooked. She sang. She said 'Ve con Dios, mijo.'")


if __name__ == "__main__":
    unittest.main()
