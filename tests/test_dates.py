import unittest

from helpers import dd, drop_input, pack


class SessionDeadlines(unittest.TestCase):
    def deadline(self, session, **extra):
        out = dd.compute_drop(drop_input(target_course=dict(session=session, **extra)), pack())
        return out

    def test_session_b_is_nov_3(self):
        self.assertEqual(self.deadline("B")["deadline"], "2026-11-03")

    def test_session_c_is_nov_4(self):
        self.assertEqual(self.deadline("C")["deadline"], "2026-11-04")

    def test_session_a_is_past(self):
        out = self.deadline("A")
        self.assertEqual(out["deadline"], "2026-09-09")
        self.assertTrue(out["deadline_passed"])
        self.assertIn("passed", out["deadline_note"])

    def test_nonstandard_session_has_no_assumed_deadline(self):
        out = self.deadline("DYN")
        self.assertIsNone(out["deadline"])
        self.assertIn("My ASU", out["deadline_status"])

    def test_nonstandard_uses_verified_individual_date(self):
        out = self.deadline("DYN", individual_deadline="2026-10-30", deadline_provenance="my_asu")
        self.assertEqual(out["deadline"], "2026-10-30")
        self.assertEqual(out["deadline_status"], "Confirmed")

    def test_missing_session_asks_instead_of_guessing(self):
        data = drop_input()
        del data["target_course"]["session"]
        out = dd.compute_drop(data, pack())
        self.assertIsNone(out["deadline"])

    def test_unverified_session_is_not_confirmed(self):
        self.assertEqual(self.deadline("C")["deadline_status"], "Likely")

    def test_verified_session_is_confirmed(self):
        out = self.deadline("C", session_provenance="my_asu")
        self.assertEqual(out["deadline_status"], "Confirmed")

    def test_uses_input_date_not_machine_clock(self):
        out = dd.compute_drop(drop_input(today="2026-11-05"), pack())
        self.assertTrue(out["deadline_passed"])
        self.assertEqual(out["days_left"], -1)

    def test_other_term_has_no_fall_deadline(self):
        out = dd.compute_drop(drop_input(term="spring-2027"), pack())
        self.assertIsNone(out["deadline"])


if __name__ == "__main__":
    unittest.main()
