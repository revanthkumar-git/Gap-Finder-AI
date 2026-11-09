import unittest

from app.grading import grade_answer


class AnswerGradingTests(unittest.TestCase):
    def test_multiple_choice_accepts_letter_and_displayed_option(self):
        options = ["A) Cell membrane", "B) Nucleus", "C) Ribosome", "D) Cytoplasm"]
        self.assertTrue(grade_answer("mcq", "A", "A", options))
        self.assertTrue(grade_answer("mcq", "A", "A) Cell membrane", options))
        self.assertFalse(grade_answer("mcq", "A", "B) Nucleus", options))

    def test_short_answer_matches_key_terms_and_rejects_empty(self):
        self.assertTrue(grade_answer("short_answer", "light reactions in thylakoid membranes", "The light reactions occur in thylakoid membranes.", []))
        self.assertFalse(grade_answer("short_answer", "photosynthesis", "", []))


if __name__ == "__main__":
    unittest.main()
