import unittest

from helpers import dd


def weighted(**kw):
    base = {"grading_method": "weighted", "final_weight": 0.4, "target_percentage": 70,
            "nonfinal_aggregate": 58, "all_other_work_finalized": True}
    base.update(kw)
    return base


class FinalNeeded(unittest.TestCase):
    def test_verified_case_is_exactly_88(self):
        self.assertEqual(dd.compute_final(weighted())["needed"], 88)

    def test_raw_canvas_score_without_aggregate_gives_no_number(self):
        out = dd.compute_final(weighted(nonfinal_aggregate=None))
        self.assertIsNone(out["needed"])
        self.assertEqual(out["missing"], "nonfinal_aggregate")

    def test_unknown_final_weight_gives_no_number(self):
        out = dd.compute_final(weighted(final_weight=None))
        self.assertIsNone(out["needed"])
        self.assertEqual(out["missing"], "final_weight")

    def test_unknown_cutoff_is_not_assumed(self):
        out = dd.compute_final(weighted(target_percentage=None))
        self.assertIsNone(out["needed"])
        self.assertEqual(out["missing"], "target_percentage")

    def test_unknown_method_asks(self):
        out = dd.compute_final(weighted(grading_method=None))
        self.assertEqual(out["missing"], "grading_method")

    def test_other_work_remaining_without_weight_asks(self):
        out = dd.compute_final(weighted(all_other_work_finalized=False))
        self.assertIsNone(out["needed"])
        self.assertEqual(out["missing"], "remaining_nonfinal_weight")

    def test_other_work_remaining_gives_scenarios_not_one_number(self):
        out = dd.compute_final(weighted(all_other_work_finalized=False,
                                        remaining_nonfinal_weight=0.2))
        self.assertIsNone(out["needed"])
        self.assertEqual(len(out["scenarios"]), 3)

    def test_case_b_with_scenario(self):
        # 0.4 done at 58 = 23.2; 0.2 remaining at 80 = 16; (70-23.2-16)/0.4 = 77
        out = dd.compute_final(weighted(all_other_work_finalized=False,
                                        remaining_nonfinal_weight=0.2,
                                        remaining_nonfinal_scenario=80))
        self.assertEqual(out["needed"], 77)

    def test_unreachable_is_flagged(self):
        out = dd.compute_final(weighted(nonfinal_aggregate=30))
        self.assertGreater(out["needed"], 100)
        self.assertIn("Above 100%", out["interpretation"])

    def test_already_met(self):
        out = dd.compute_final(weighted(nonfinal_aggregate=100, target_percentage=60))
        self.assertLessEqual(out["needed"], 0)

    def test_points_based_does_not_use_weighted_formula(self):
        # 70% of 500 = 350; 260 earned; need 90 of 100 final points
        out = dd.compute_final({"grading_method": "points", "target_percentage": 70,
                                "earned_points": 260, "total_possible_points": 500,
                                "final_possible_points": 100})
        self.assertEqual(out["needed"], 90)
        self.assertEqual(out["needed_points"], 90)

    def test_points_with_other_remaining_requires_assumption(self):
        out = dd.compute_final({"grading_method": "points", "target_percentage": 70,
                                "earned_points": 200, "total_possible_points": 500,
                                "final_possible_points": 100,
                                "other_remaining_possible_points": 100})
        self.assertEqual(out["missing"], "assumed_other_points")

    def test_never_recommends_staying(self):
        out = dd.compute_final(weighted(nonfinal_aggregate=80))
        self.assertNotIn("stay", out["interpretation"].lower().replace("stay or withdraw", ""))


if __name__ == "__main__":
    unittest.main()
