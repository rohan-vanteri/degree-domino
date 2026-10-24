import unittest

from helpers import dd, drop_input, pack


class DropCheck(unittest.TestCase):
    def test_enrolled_credits_15_to_12(self):
        out = dd.compute_drop(drop_input(), pack())
        self.assertEqual(out["enrolled_credits_before"], 15)
        self.assertEqual(out["enrolled_credits_after"], 12)

    def test_student_reported_credits_are_likely(self):
        self.assertEqual(dd.compute_drop(drop_input(), pack())["enrolled_credits_status"], "Likely")

    def test_verified_credits_are_confirmed(self):
        out = dd.compute_drop(drop_input(target_course={"credits_provenance": "my_asu"},
                                         other_credits_provenance="my_asu"), pack())
        self.assertEqual(out["enrolled_credits_status"], "Confirmed")

    def test_12_enrolled_does_not_claim_annual_renewal(self):
        out = dd.compute_drop(drop_input(), pack())
        aid = [h for h in out["headlines"] if "Financial Aid" in h["status"]]
        self.assertEqual(len(aid), 1)
        self.assertIn("30 earned credits", aid[0]["text"])
        self.assertIn("unknown", aid[0]["text"])

    def test_below_term_minimum_flagged(self):
        out = dd.compute_drop(drop_input(other_enrolled_credits=10), pack())
        aid = [h for h in out["headlines"] if "Financial Aid" in h["status"]][0]
        self.assertIn("below", aid["text"])

    def test_no_namu_assumed_when_missing(self):
        out = dd.compute_drop(drop_input(scholarships=[]), pack())
        self.assertFalse(any("Financial Aid" in h["status"] for h in out["headlines"]))

    def test_unverified_prereq_is_conditional(self):
        out = dd.compute_drop(drop_input(), pack())
        pre = [h for h in out["headlines"] if "MAT 266" in h["text"]][0]
        self.assertIn("advisor", pre["status"])
        self.assertIn("may", pre["text"])

    def test_sample_prereq_never_confirmed(self):
        out = dd.compute_drop(drop_input(), pack())
        pre = [h for h in out["headlines"] if "MAT 266" in h["text"]][0]
        self.assertNotEqual(pre["status"], "Confirmed")

    def test_at_most_three_headlines(self):
        self.assertLessEqual(len(dd.compute_drop(drop_input(), pack())["headlines"]), 3)

    def test_future_fork_has_three_paths(self):
        paths = [p["path"] for p in dd.compute_drop(drop_input(), pack())["future_fork"]]
        self.assertEqual(paths, ["Stay", "Withdraw", "Alternate"])

    def test_withdraw_path_mentions_w_and_sap(self):
        fork = dd.compute_drop(drop_input(), pack())["future_fork"]
        withdraw = fork[1]["effect"]
        self.assertIn("W on transcript", withdraw)
        self.assertIn("attempted but not completed", withdraw)

    def test_final_needed_included_when_composition_known(self):
        data = drop_input()
        data["final"].update(nonfinal_aggregate=58, all_other_work_finalized=True)
        self.assertEqual(dd.compute_drop(data, pack())["final_needed"]["needed"], 88)

    def test_final_needed_null_with_raw_canvas_only(self):
        out = dd.compute_drop(drop_input(), pack())
        self.assertIsNone(out["final_needed"])
        self.assertEqual(out["final_needed_missing"]["field"], "nonfinal_aggregate")

    def test_every_cited_source_has_url(self):
        out = dd.compute_drop(drop_input(), pack())
        self.assertEqual(set(out["source_ids"]), set(out["sources"]))
        self.assertTrue(all(u.startswith("https://") for u in out["sources"].values()))


if __name__ == "__main__":
    unittest.main()
