# Degree Domino

*Text it before you drop it.* A Cubbie Skill that answers degree, major map, registration and graduation questions from the student's DARS audit, and shows what withdrawing from a class changes (enrolled credits, the course's withdrawal deadline, scholarship and financial-aid rules, the next prerequisite) and compares Stay / Withdraw / Alternate plan in plain text.

## Install
Text Cubbie the link to the Skill folder:
```
https://github.com/rohan-vanteri/degree-domino/tree/main/degree-domino
```

## Scope and limits
- **ASU Fall 2026 only** for deadlines and scholarship rules. Other schools get credit arithmetic and a checklist, not ASU rules.
- Not an official degree audit, financial adviser or registration system. It never enrolls, withdraws, or sends anything without approval.
- University-wide policies (deadlines, W grade, scholarship, aid) come from `degree-domino/rules/asu.json`, with a source URL and check date. Unverified or stale rules are reported as "Check with [office]".
- Course prerequisites are never hard-coded. Each run, Cubbie reads the student's major map and the ASU catalog live, and the script keeps only courses in that major. A prerequisite is Confirmed only if it came from an official ASU page fetched in the last 7 days and the quoted requirement names the dropped course.
- The final-exam calculation only gives a number when the grading method, cutoff and weights are known. A Canvas total alone is not enough.
- Named-course grade and withdrawal questions first check live Canvas current and past student enrollments. The `enrollment` command distinguishes current, previous (with term), not current, and unverified enrollment; Cubbie supplies the live Canvas data.
- Works without Canvas: the student can type in course credits and grades.
- All data in this repository is synthetic.

## Layout
```
degree-domino/   Skill folder installed by Cubbie (SKILL.md, scripts, rules, references, assets)
tests/           unit tests (python3 -m unittest)
docs/            demo script, device checklist, roadmap, source review log
```

## Run locally
```
cd degree-domino
python3 scripts/degree_domino.py drop --sample --rules rules/asu.json
python3 scripts/degree_domino.py final --sample
python3 scripts/degree_domino.py plan --sample
python3 -m unittest discover -s ../tests -p "test_*.py" -v
```
Exit codes: 0 ok, 2 missing input, 3 rules unavailable, 4 unexpected error.
