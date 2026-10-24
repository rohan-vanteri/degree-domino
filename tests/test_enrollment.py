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
