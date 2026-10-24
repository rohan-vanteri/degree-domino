"""Plays the demo video's conversation through the engine, beat by beat.

Inputs are only what Cubbie reads from Canvas (courses, dates, grades,
assignment groups) plus the syllabus cutoff: nothing is asked of the student.
"""
import copy
import unittest

from helpers import all_text, dd, pack, sample


def video(**kw):
    data = copy.deepcopy(sample("sample_video.json"))
    data.update(kw)
    return data


class VideoFlow(unittest.TestCase):
    def setUp(self):
        self.out = dd.compute_drop(video(), pack())

    def test_nothing_is_asked(self):
        # Credits, session and other enrolled credits all come from Canvas.
        self.assertTrue(self.out["ok"])
        self.assertTrue(self.out["enrolled"])
        self.assertNotIn("final_needed_missing", self.out)

    def test_reads_canvas_grade_and_session(self):
        self.assertEqual(self.out["canvas_score"], 58)
        self.assertEqual(self.out["session"], "C")
        self.assertTrue(self.out["session_inferred"])

    def test_deadline_nov_4_is_likely_not_confirmed(self):
        self.assertEqual(self.out["deadline"], "2026-11-04")
        self.assertEqual(self.out["deadline_status"], "Likely")
        self.assertIn("My ASU", self.out["deadline_note"])

    def test_credits_15_to_12(self):
        self.assertEqual(self.out["enrolled_credits_before"], 15)
        self.assertEqual(self.out["enrolled_credits_after"], 12)
        self.assertIn("Canvas course list", self.out["headlines"][0]["text"])

    def test_two_dominoes(self):
        texts = [h["text"] for h in self.out["headlines"]]
        aid = [t for t in texts if "30 earned credits" in t]
        prereq = [t for t in texts if "may require CSE 240" in t]
        self.assertEqual(len(aid), 1)
        self.assertEqual(len(prereq), 1)
        self.assertIn("CSE 340", prereq[0])
        self.assertNotIn("in your major", prereq[0])

    def test_three_paths(self):
        self.assertEqual([p["path"] for p in self.out["future_fork"]], ["Stay", "Withdraw", "Alternate"])

    def test_final_88_from_canvas_groups(self):
        self.assertEqual(self.out["final_needed"]["needed"], 88)
        f = dd.compute_final(video()["final"])
        self.assertEqual(f["needed"], 88)

    def test_phy_121_not_enrolled(self):
        out = dd.compute_drop(video(target_course={"code": "phy121"}), pack())
        self.assertFalse(out["enrolled"])
        self.assertIn("aren't currently enrolled in PHY 121", out["message"])
        self.assertIn("CSE 240", out["current_courses"])

    def test_no_banned_phrases(self):
        for text in all_text(self.out):
            for phrase in ("safe to drop", "you're fine", "you will lose", "definitely"):
                self.assertNotIn(phrase, text)


class CanvasInference(unittest.TestCase):
    def test_sessions_from_dates(self):
        self.assertEqual(dd.infer_session("2026-08-20", "2026-12-05"), "C")
        self.assertEqual(dd.infer_session("2026-08-20", "2026-10-09"), "A")
        self.assertEqual(dd.infer_session("2026-10-14", "2026-12-05"), "B")
        self.assertIsNone(dd.infer_session("2026-09-01", "2026-11-10"))   # odd length: no guess
        self.assertIsNone(dd.infer_session("bad", "2026-12-05"))

    def test_missing_credits_assumed_and_flagged(self):
        data = video()
        for c in data["enrolled_courses"]:
            c.pop("credits")
        out = dd.compute_drop(data, pack())
        self.assertEqual(out["enrolled_credits_before"], 15)
        self.assertEqual(len(out["credits_assumed_for"]), 5)
        self.assertIn("assuming 3 credits", out["headlines"][0]["text"])

    def test_explicit_session_wins_over_dates(self):
        out = dd.compute_drop(video(target_course={"code": "CSE 240", "session": "B"}), pack())
        self.assertEqual(out["deadline"], "2026-11-03")

    def test_unfinished_group_gives_scenarios(self):
        final = video()["final"]
        final["canvas_groups"][1]["complete"] = False
        f = dd.compute_final(final)
        self.assertIsNone(f["needed"])
        self.assertEqual(len(f["scenarios"]), 3)

    def test_no_final_group_asks_for_weight(self):
        final = video()["final"]
        final["canvas_groups"] = final["canvas_groups"][:2]
        self.assertEqual(dd.compute_final(final)["missing"], "final_weight")

    def test_weights_need_not_sum_to_100(self):
        final = video()["final"]
        for g in final["canvas_groups"]:
            g["weight"] = g["weight"] / 10
        self.assertEqual(dd.compute_final(final)["needed"], 88)


if __name__ == "__main__":
    unittest.main()
