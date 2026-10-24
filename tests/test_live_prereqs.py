import unittest

from helpers import dd, drop_input, pack

URL = "https://catalog.apps.asu.edu/catalog/courses/courselist?subject=CSE&catalogNbr=310"
MAP = "https://degrees.asu.edu/major-map/ASU00/ESCSEBS/null/ALL/2026"


def live(**kw):
    """A CS student dropping CSE 240, with data as Cubbie would read it live."""
    data = drop_input(target_course={"code": "CSE 240"}, planned_next_course="CSE 360")
    data["major"] = {"name": "Computer Science, BS", "catalog_year": "2026",
                     "source_url": MAP, "fetched_at": "2026-10-24",
                     "courses": ["CSE 240", "CSE 340", "CSE 360", "CSE 310"]}
    data["prerequisites"] = [
        {"course": "CSE 360", "requires": ["CSE 240"],
         "requirement_text": "Prerequisite(s): CSE 240 with C or better",
         "source_url": URL, "fetched_at": "2026-10-24"},
        {"course": "CSE 340", "requires": ["CSE 240"],
         "requirement_text": "Prerequisite(s): CSE 240 with C or better",
         "source_url": URL, "fetched_at": "2026-10-24"},
        {"course": "EEE 333", "requires": ["CSE 240"],
         "requirement_text": "Prerequisite(s): CSE 240",
         "source_url": URL, "fetched_at": "2026-10-24"},
        {"course": "CSE 310", "requires": ["CSE 205"],
         "requirement_text": "Prerequisite(s): CSE 205",
         "source_url": URL, "fetched_at": "2026-10-24"},
    ]
    data.update(kw)
    return data


def headline(out, course):
    return [h for h in out["headlines"] if course in h["text"]][0]


class LivePrereqs(unittest.TestCase):
    def test_official_fresh_quoted_requirement_is_confirmed(self):
        out = dd.compute_drop(live(), pack())
        h = headline(out, "CSE 360")
        self.assertEqual(h["status"], "Confirmed")
        self.assertIn("requires CSE 240", h["text"])

    def test_major_filter_drops_courses_outside_the_major(self):
        courses = [d["course"] for d in dd.compute_drop(live(), pack())["dominoes_in_major"]]
        self.assertIn("CSE 340", courses)
        self.assertNotIn("EEE 333", courses)

    def test_courses_not_needing_the_dropped_class_are_ignored(self):
        courses = [d["course"] for d in dd.compute_drop(live(), pack())["dominoes_in_major"]]
        self.assertNotIn("CSE 310", courses)

    def test_planned_course_leads_and_others_are_listed(self):
        h = headline(dd.compute_drop(live(), pack()), "CSE 360")
        self.assertTrue(h["text"].startswith("CSE 360"))
        self.assertIn("CSE 340", h["text"])

    def test_without_major_every_dependent_course_is_kept(self):
        data = live()
        del data["major"]
        courses = [d["course"] for d in dd.compute_drop(data, pack())["dominoes_in_major"]]
        self.assertIn("EEE 333", courses)

    def test_unofficial_source_is_not_confirmed(self):
        data = live()
        for p in data["prerequisites"]:
            p["source_url"] = "https://www.reddit.com/r/ASU"
        self.assertNotEqual(headline(dd.compute_drop(data, pack()), "CSE 360")["status"], "Confirmed")

    def test_stale_fetch_is_not_confirmed(self):
        data = live(today="2026-11-20")
        self.assertNotEqual(headline(dd.compute_drop(data, pack()), "CSE 360")["status"], "Confirmed")

    def test_requirement_text_must_name_the_course(self):
        data = live()
        data["prerequisites"][0]["requirement_text"] = "Prerequisite(s): see advisor"
        self.assertNotEqual(headline(dd.compute_drop(data, pack()), "CSE 360")["status"], "Confirmed")

    def test_course_codes_are_normalized(self):
        data = live(planned_next_course="cse360")
        data["prerequisites"][0]["requires"] = ["CSE240"]
        self.assertEqual(headline(dd.compute_drop(data, pack()), "CSE 360")["status"], "Confirmed")

    def test_nothing_fetched_falls_back_to_advisor(self):
        data = live()
        del data["prerequisites"]
        h = headline(dd.compute_drop(data, pack()), "CSE 360")
        self.assertIn("advisor", h["status"])
        self.assertIn("couldn't confirm", h["text"])

    def test_live_sources_are_cited(self):
        out = dd.compute_drop(live(), pack())
        self.assertEqual(out["sources"]["major_map"], MAP)
        self.assertEqual(out["sources"]["prereq.CSE360"], URL)


if __name__ == "__main__":
    unittest.main()
