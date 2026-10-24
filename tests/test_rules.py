import json
import unittest

from helpers import RULES, dd, drop_input, pack


class RulePack(unittest.TestCase):
    def test_every_rule_has_provenance(self):
        with open(RULES, encoding="utf-8") as f:
            rules = json.load(f)["rules"]
        for r in rules:
            for key in ("id", "school", "applies_to", "rule", "status", "source_url", "checked_at"):
                self.assertIn(key, r, r.get("id"))
            self.assertIn(r["status"], ("confirmed", "verify"))
            self.assertTrue(r["source_url"].startswith("https://"))

    def test_no_course_rules_are_hard_coded(self):
        self.assertFalse(any(rid.startswith("asu.prereq.") for rid in pack()["rules"]))

    def test_stale_rule_degrades(self):
        out = dd.compute_drop(drop_input(today="2026-12-31", term="fall-2026"), pack())
        self.assertIsNone(out["deadline"])
        self.assertIn("Check with", out["deadline_status"])

    def test_missing_rules_file_is_exit_3(self):
        with self.assertRaises(dd.RulesError):
            dd.load_rules("/nonexistent/asu.json")

    def test_non_asu_school_gets_no_asu_rules(self):
        out = dd.compute_drop(drop_input(school="UCLA"), pack())
        self.assertEqual(out["mode"], "generic")
        self.assertIsNone(out["deadline"])
        self.assertEqual(out["source_ids"], [])


if __name__ == "__main__":
    unittest.main()
