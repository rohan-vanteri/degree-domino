import tempfile
import unittest

from helpers import dd, drop_input, pack, run_cli


class Enrollment(unittest.TestCase):
    def test_not_enrolled_stops_with_message(self):
        data = drop_input(target_course={"code": "CSE 240"},
                          enrolled_courses=["MAT 265", "CSE 205"],
                          enrolled_courses_source="canvas")
        out = dd.compute_drop(data, pack())
        self.assertFalse(out["enrolled"])
        self.assertIn("aren't currently enrolled in CSE 240", out["message"])
        self.assertEqual(out["current_courses"], ["MAT 265", "CSE 205"])
        self.assertNotIn("future_fork", out)

    def test_enrolled_course_runs_normally(self):
        data = drop_input(target_course={"code": "cse240"}, enrolled_courses=["CSE 240", "MAT 265"])
        out = dd.compute_drop(data, pack())
        self.assertTrue(out["enrolled"])
        self.assertIn("future_fork", out)

    def test_unknown_enrollment_is_not_assumed(self):
        self.assertIsNone(dd.compute_drop(drop_input(), pack())["enrolled"])

    def test_not_enrolled_needs_no_credits(self):
        data = drop_input(target_course={"code": "CSE 240"}, enrolled_courses=["MAT 265"])
        del data["target_course"]["credits"]
        del data["other_enrolled_credits"]
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli("drop", input_obj=data, tmpdir=tmp)
        self.assertEqual(code, 0)
        self.assertFalse(out["enrolled"])

    def test_concentration_is_reported(self):
        data = drop_input()
        data["major"]["concentration"] = "Software Engineering"
        out = dd.compute_drop(data, pack())
        self.assertEqual(out["major"]["concentration"], "Software Engineering")


if __name__ == "__main__":
    unittest.main()

class CanvasLookup(unittest.TestCase):
    def data(self, current=None, previous=None, complete=True):
        return {"today": "2026-10-24", "target_course": {"code": "cse360"},
                "canvas": {"checked_on": "2026-10-24", "current_complete": complete,
                           "current_courses": current or [], "previous_courses": previous or []}}

    def test_absent_after_complete_lookup(self):
        out = dd.compute_enrollment(self.data(current=[{"code": "CSE 301"}]))
        self.assertFalse(out["enrolled"])
        self.assertEqual(out["message"], "You are not currently enrolled in CSE 360.")

    def test_previous_semester_from_canvas(self):
        out = dd.compute_enrollment(self.data(previous=[{"code": "CSE 360", "term": "Spring 2026"}]))
        self.assertEqual(out["status"], "previous")
        self.assertIn("Canvas shows you were enrolled in Spring 2026", out["message"])

    def test_current_retake_wins(self):
        out = dd.compute_enrollment(self.data(current=[{"code": "CSE 360", "term": "Fall 2026"}],
                                              previous=[{"code": "CSE 360", "term": "Spring 2026"}]))
        self.assertTrue(out["enrolled"])
        self.assertEqual(out["courses"][0]["term"], "Fall 2026")

    def test_incomplete_is_unknown_even_with_history(self):
        out = dd.compute_enrollment(self.data(previous=[{"code": "CSE 360"}], complete=False))
        self.assertIsNone(out["enrolled"])

    def test_stale_snapshot_is_unknown(self):
        data = self.data(current=[{"code": "CSE 360"}])
        data["canvas"]["checked_on"] = "2026-10-23"
        self.assertIsNone(dd.compute_enrollment(data)["enrolled"])

    def test_previous_without_term(self):
        self.assertIn("previous semester", dd.compute_enrollment(
            self.data(previous=[{"code": "CSE 360"}]))["message"])

    def test_drop_stops_before_credit_math_for_past_course(self):
        out = dd.compute_drop(self.data(previous=[{"code": "CSE 360", "term": "Spring 2026"}]), pack())
        self.assertEqual(out["status"], "previous")
        self.assertNotIn("future_fork", out)

    def test_cli_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli("enrollment", input_obj=self.data(), tmpdir=tmp)
        self.assertEqual(code, 0)
        self.assertFalse(out["enrolled"])
