import copy
import tempfile
import unittest

from helpers import dd, run_cli, sample

DARS_URL = "https://webapp4.asu.edu/dars/audit"
CAT = "https://catalog.apps.asu.edu/catalog/courses/courselist?subject=CSE"


def plan(**kw):
    data = copy.deepcopy(sample("sample_plan.json"))
    data.update(kw)
    return data


def official():
    """The sample, as if read live from real ASU pages today."""
    data = plan()
    data["dars"]["source_url"] = DARS_URL
    for p in data["prerequisites"]:
        p["source_url"] = CAT
        p["requirement_text"] = p["requirement_text"].replace("SAMPLE ONLY: ", "Prerequisite(s): ")
    return data


def option(out, course):
    for r in out["requirements"]:
        for o in r["options"]:
            if o["course"] == course:
                return o
    return None


class Plan(unittest.TestCase):
    def test_progress_comes_from_dars(self):
        p = dd.compute_plan(plan())["progress"]
        self.assertEqual(p["expected_graduation"], "Spring 2029")
        self.assertEqual(p["expected_graduation_source"], "DARS audit")
        self.assertEqual(p["credits_remaining"], 75)

    def test_no_expected_term_is_not_guessed(self):
        data = plan()
        data["dars"]["expected_graduation"] = None
        p = dd.compute_plan(data)["progress"]
        self.assertIsNone(p["expected_graduation"])
        self.assertIn("no expected graduation", p["expected_graduation_note"])

    def test_met_prereq_is_suggested(self):
        courses = [s["course"] for s in dd.compute_plan(plan())["suggested_next_term"]]
        self.assertIn("AAA 320", courses)

    def test_any_of_prereq(self):
        self.assertEqual(option(dd.compute_plan(plan()), "AAA 320")["prerequisites"], "met")

    def test_in_progress_prereq_is_conditional(self):
        s = [s for s in dd.compute_plan(plan())["suggested_next_term"] if s["course"] == "AAA 301"][0]
        self.assertEqual(s["condition"], "if you pass AAA 201")

    def test_blocked_course_not_suggested(self):
        out = dd.compute_plan(plan())
        self.assertEqual(option(out, "AAA 310")["prerequisites"], "blocked")
        self.assertEqual(option(out, "AAA 310")["missing"], ["AAA 999"])
        self.assertNotIn("AAA 310", [s["course"] for s in out["suggested_next_term"]])

    def test_unchecked_prereq_not_suggested(self):
        out = dd.compute_plan(plan())
        self.assertEqual(option(out, "BBB 220")["prerequisites"], "unchecked")
        self.assertNotIn("BBB 220", [s["course"] for s in out["suggested_next_term"]])

    def test_completed_and_current_courses_not_suggested(self):
        data = plan()
        data["dars"]["unmet_requirements"].append(
            {"name": "x", "course_options": ["AAA 101", "AAA 201"]})
        out = dd.compute_plan(data)
        self.assertIsNone(option(out, "AAA 101"))
        self.assertIsNone(option(out, "AAA 201"))

    def test_target_credits_limits_suggestions(self):
        out = dd.compute_plan(plan(target_credits=3))
        self.assertEqual(out["suggested_credits"], 3)
        self.assertEqual(len(out["suggested_next_term"]), 1)

    def test_sample_sources_are_never_confirmed(self):
        out = dd.compute_plan(plan())
        self.assertNotEqual(out["dars_status"], "Confirmed")
        self.assertTrue(all(s["status"] != "Confirmed" for s in out["suggested_next_term"]))
        self.assertEqual(out["sources"], {})

    def test_official_fresh_sources_are_confirmed(self):
        out = dd.compute_plan(official())
        self.assertEqual(out["dars_status"], "Confirmed")
        self.assertEqual(option(out, "AAA 320")["status"], "Confirmed")
        self.assertEqual(out["sources"]["dars"], DARS_URL)

    def test_stale_dars_is_not_confirmed(self):
        data = official()
        data["today"] = "2026-12-01"
        self.assertNotEqual(dd.compute_plan(data)["dars_status"], "Confirmed")

    def test_non_asu_dars_url_is_not_confirmed(self):
        data = official()
        data["dars"]["source_url"] = "https://drive.google.com/file/abc"
        self.assertNotEqual(dd.compute_plan(data)["dars_status"], "Confirmed")

    def test_never_claims_seats_or_offerings(self):
        out = dd.compute_plan(plan())
        self.assertIn("Class Search", out["registration_note"])
        self.assertIn("advisor", out["recommended_next_step"])

    def test_cli_sample_and_missing_dars(self):
        self.assertEqual(run_cli("plan", "--sample")[0], 0)
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli("plan", input_obj={"today": "2026-10-24"}, tmpdir=tmp)
        self.assertEqual(code, 2)
        self.assertEqual(out["field"], "dars")


if __name__ == "__main__":
    unittest.main()
