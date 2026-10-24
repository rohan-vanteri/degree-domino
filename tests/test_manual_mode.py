import tempfile
import unittest

from helpers import dd, run_cli


MANUAL = {"school": "ASU", "term": "fall-2026", "today": "2026-10-24",
          "target_course": {"code": "CHM 113", "credits": 4, "session": "C"},
          "other_enrolled_credits": 11}


class ManualMode(unittest.TestCase):
    def test_minimal_manual_input_works_without_canvas(self):
        out = dd.compute_drop(MANUAL, dd.load_rules(None))
        self.assertEqual(out["enrolled_credits_after"], 11)
        self.assertEqual(out["mode"], "generic")

    def test_missing_credits_names_the_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {k: v for k, v in MANUAL.items() if k != "other_enrolled_credits"}
            code, out = run_cli("drop", input_obj=data, tmpdir=tmp)
        self.assertEqual(code, 2)
        self.assertEqual(out["field"], "other_enrolled_credits")

    def test_missing_today_names_the_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {k: v for k, v in MANUAL.items() if k != "today"}
            code, out = run_cli("drop", input_obj=data, tmpdir=tmp)
        self.assertEqual(code, 2)
        self.assertEqual(out["field"], "today")

    def test_negative_credits_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = dict(MANUAL, other_enrolled_credits=-1)
            code, _ = run_cli("drop", input_obj=data, tmpdir=tmp)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
