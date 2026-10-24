import json
import os
import tempfile
import unittest

from helpers import RULES, SKILL, all_text, dd, drop_input, pack, run_cli

BANNED = ["safe to drop", "you're fine", "you are fine", "you will lose",
          "you'll lose", "will graduate late", "definitely"]


class OutputRules(unittest.TestCase):
    def outputs(self):
        variants = [drop_input(), drop_input(other_enrolled_credits=8),
                    drop_input(target_course={"session": "A"}),
                    drop_input(planned_next_course="MAT 343")]
        return [dd.compute_drop(v, pack()) for v in variants]

    def test_no_banned_phrases(self):
        for out in self.outputs():
            for text in all_text(out):
                for phrase in BANNED:
                    self.assertNotIn(phrase, text)

    def test_never_recommends_stay(self):
        for out in self.outputs():
            self.assertNotIn("stay", out["recommended_next_step"].lower())

    def test_only_three_confidence_labels(self):
        for out in self.outputs():
            for h in out["headlines"]:
                self.assertTrue(h["status"] in ("Confirmed", "Likely")
                                or h["status"].startswith("Check with "))

    def test_output_is_compact(self):
        for out in self.outputs():
            self.assertLess(len(json.dumps(out, indent=2)), 8000)
            self.assertLess(len(json.dumps(out)), 2500)

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_cli("drop", "--sample", "--rules", RULES)[0], 0)
            self.assertEqual(run_cli("final", "--sample")[0], 0)
            self.assertEqual(run_cli("drop", "--input", os.devnull)[0], 2)
            self.assertEqual(run_cli("drop", "--sample", "--rules", os.path.join(tmp, "x.json"))[0], 3)

    def test_sample_run_writes_nothing(self):
        before = sorted(os.listdir(os.path.join(SKILL, "assets")))
        run_cli("drop", "--sample", "--rules", RULES)
        self.assertEqual(before, sorted(os.listdir(os.path.join(SKILL, "assets"))))


if __name__ == "__main__":
    unittest.main()
