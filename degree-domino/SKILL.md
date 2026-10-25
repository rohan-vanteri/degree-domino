---
name: degree-domino
description: Answers ASU degree, major map, class registration, graduation and drop/withdraw questions from the student's DARS audit and current classes, with sourced suggestions. Use when a student asks "what should I take next semester", "what classes do I need", "help me register", "show my major map", "what is left in my degree", "when will I graduate", "what is my expected graduation", "am I on track", "how many credits do I have left", "should I drop", "what if I withdraw", "will this affect my scholarship", or "what do I need on the final". Also use for course enrollment and grade questions such as "how am I doing in CSE360". Not a generic study plan.
---

# Degree Domino

Help students understand the consequences of academic decisions; never make
an enrollment decision for them. Separate official rules from student-specific
impacts, and state uncertainty rather than guessing.

## Where student data comes from
Use only these sources for the student's own academic record:
- Current classes and grades: the student's Canvas, or their My ASU class
  schedule.
- Degree progress, major, concentration, catalog year, credits earned and
  remaining, requirements left, and expected graduation term: the student's
  DARS degree audit, opened in the browser from My ASU (see "Signing in to
  My ASU").

## Check enrollment before any named-course question
For grades, finals, course performance, or withdrawal, first read the student's
Canvas course information live. A cached sync, dashboard favorites, or a course
search result is not a complete enrollment list. Open Canvas Courses > All
Courses and inspect current and past student enrollments, course code, title,
section, term and enrollment state. If using a Canvas connector/API, retrieve
all pages and include concluded enrollments and term information. Do not infer
past enrollment from an old start date or mere access to a course. Use the
actual student enrollment and term; an earlier session in the current semester
is not a previous semester. A current retake takes priority over a past attempt.

Match exact course codes with spacing/case normalized (CSE360 = CSE 360).
Do not substitute CSE 301 for CSE 360. If a nickname or multiple sections are
ambiguous, ask for clarification using the Canvas titles/terms you found.

Write the observed data as:
```json
{
  "today": "2026-10-24",
  "target_course": {"code": "CSE360"},
  "canvas": {
    "checked_on": "2026-10-24",
    "current_complete": true,
    "current_courses": [{"code": "CSE 301", "name": "Computing Ethics", "term": "Fall 2026"}],
    "previous_courses": [{"code": "CSE 360", "name": "Introduction to Software Engineering", "term": "Spring 2026"}]
  }
}
```
Use the student's local date, actual Canvas titles/terms and only verified
student enrollments. `current_complete` is true only after the live current
roster has been fully read. Set it false on access errors or incomplete paging.
Run `python3 scripts/degree_domino.py enrollment --input <file>`.
- `current`: read grades, assignment groups and syllabus from that Canvas
  course/section; continue with the student's question.
- `not_current`: say "I do not see you currently enrolled for CSE360."
- `previous`: say "I do not see you currently enrolled for CSE360. Canvas shows
  you were enrolled in Spring 2026." Use the actual term if available;
  otherwise say "in a previous semester". Do not imply a passing grade.
- `unknown`: if the course is absent from an incomplete Canvas roster, say
  exactly "I do not see you currently enrolled for CSE360." Use the requested
  course code without spaces. This describes what is visible, not a definitive
  enrollment verdict. Do not add an incomplete-sync explanation or ask for a
  course link or Grades screenshot. If the data is stale, refresh Canvas first.

For any absent course, including `unknown` from an incomplete roster, stop
current-grade/withdrawal analysis. Do not
ask for screenshots or a course link to compensate for not checking Canvas.
On "CSE360" or "are you sure?", repeat the live lookup instead of repeating
cached results. Historical grades may be read from the past Canvas course if
the student asks, clearly labeled with its term. Never invent course details.

## Signing in to My ASU
Whenever you need My ASU or DARS:
1. Open https://webapp4.asu.edu/myasu/ in the browser. Always start from this
   link; don't search for a login page or open other ASU sign-in URLs.
2. If it shows the My ASU home page with the student's own name, they are
   already signed in; go to step 5.
3. Otherwise hand the browser to the student with one short message:
   "I opened My ASU. Take control, sign in with your ASURITE and approve
   Duo (and tick any 'Verify you are human' box), then hand control back and
   reply 'done'." Never ask for or type their password or Duo code.
4. Wait. Do not read, click or retry anything until the student replies
   "done" or hands control back. Then check that the My ASU home page shows
   their own name; a page header that says "Sparky", or a login or
   "Verify you are human" page, means they are not signed in yet: say so
   and ask them to finish signing in. After two tries, stop and say My ASU
   couldn't be reached this time.
5. From My ASU, open the degree audit (DARS) link, run or open the latest
   audit, and read it. Don't sign the student out.

Never search or read Google Drive, Docs, email, uploaded files or other
documents for the student's academic record, even if they mention graduation
dates. Never present a date from a form or document as the expected
graduation. If DARS cannot be opened, say so and offer to try again after the
student signs in; don't fall back to files.

## Degree, major map, registration and graduation questions
Use this for any question about the student's degree, major or
concentration, major map, what to take or register for, requirements left,
credits, or graduation. Drop/withdraw questions use the sections below.
1. Open the student's DARS audit (see "Where student data comes from") and
   read: major, concentration, catalog year, expected graduation term (only
   if DARS shows one), credits earned, in progress and required, completed
   courses, in-progress courses, and each unmet requirement with the course
   options DARS lists for it.
2. Read current classes from Canvas or the My ASU schedule.
3. For the course options on unmet requirements, open each in the ASU catalog
   (catalog.apps.asu.edu) and copy its "Enrollment requirements" word for
   word (Drop / withdraw questions, Gather step 5). Use `requires` for courses that are all
   needed and `requires_any_of` when any one is enough. If the student asks
   about their major map, open it on degrees.asu.edu for their major,
   concentration and catalog year and compare it with DARS.
4. Write the data to a JSON file shaped like `assets/sample_plan.json`
   (`dars`, `enrolled_courses`, `prerequisites`, `fetched_at` today, and
   `target_credits` if the student gave a load) and run:
   `python3 scripts/degree_domino.py plan --input <file>`
5. Reply in short plain text:
   - Progress: expected graduation exactly as DARS shows it, labeled "from
     your DARS audit", and credits earned of required. If DARS shows no
     term, say so and give remaining credits; never calculate a date.
   - Up to five suggested courses from `suggested_next_term`, each with the
     requirement it fills and any "if you pass ..." condition.
   - Courses that are blocked, with the missing prerequisite.
   - The registration note: check ASU Class Search for sections and seats,
     and review with an advisor before registering.
   Label items with the script's status. Never register the student.
6. If a current class is a requirement in DARS and the student is worried
   about it, offer a Drop Check.

## Drop / withdraw questions
Never ask the student for anything Canvas already shows. Send one short
"Let me check before you decide." and then gather everything below yourself,
run the script, and reply. Do not open with a judgment ("maybe", "I wouldn't
withdraw"), and never lean toward staying or withdrawing.

### Gather (from Canvas; no questions)
1. Run the enrollment check above and include its `canvas` object in the drop input. Read the student's current-term Canvas courses. For each, pass an object in
   `enrolled_courses`: `code`, `credits` (only if Canvas shows them), `start`
   and `end` dates of the course, and `current_score` for the course the
   student named. Set `enrolled_courses_source` to "canvas". Match what the
   student said ("cse240", "calc") to a course yourself; put its code in
   `target_course.code`. The script works out the session from the dates,
   the credits before and after (3 per course when Canvas shows none, and it
   says so), and whether the student is enrolled at all.
2. If the enrollment check returns `previous` or `not_current`, use its
   message and stop. For an absent course in an incomplete roster, use the
   same "I do not see you currently enrolled for <code>." wording and stop.
3. For the final-exam math, read the course's Canvas assignment groups (name,
   weight, current score, whether all its work is graded) into
   `final.canvas_groups`, mark the final exam group `is_final`, and read the
   grade cutoff for the student's target (C if they didn't say) from the
   syllabus into `final.target_percentage`. Include this even if the student
   didn't ask, so the reply can mention it when they do.
4. Use the scholarship from memory if Cubbie knows it (pass `scholarships`);
   if not, leave it out rather than asking.
5. Prerequisite dominoes: search the web and the ASU catalog for courses that
   list the target course as a prerequisite (for CSE 240, for example, search
   "ASU prerequisite CSE 240"). Pass each as an entry in `prerequisites` with
   `course`, `requires` (or `requires_any_of`), the requirement text copied
   word for word, `source_url` and `fetched_at` (today). Unverified ones come
   back as "may require ... Check with your advisor". If the major is already
   known (memory or DARS), also pass `major` so only courses in it are kept;
   never ask for the major.
6. Pass today's local date as `today`, `school` "ASU" and `term` (for
   example "fall-2026").

Only if Canvas isn't connected: say so in one line and ask for the single
next fact (the course, then its credits, then total enrolled credits).

### Reply (same order every time, short separate messages)
1. "You're in <course> this <term> (Session <X>), showing <score>% on Canvas."
   then the withdrawal deadline from the script and "Confirm your section's
   date in My ASU." unless the deadline status is Confirmed.
2. "Withdrawing would take you from <before> to <after> enrolled credits."
   plus any credits note the script gives.
3. "Two dominoes to check:" with the prerequisite headline and the
   scholarship headline, each ending with its "Check with ..." label.
4. "Compare 1 Stay / 2 Withdraw / 3 Alternate?"
On "compare", send the three `future_fork` paths. On "what do I need on the
final", answer from `final_needed` ("Your Canvas syllabus says the final is
<w>% and a <grade> is <cutoff>%. With <g>% on everything else, you'd need
<needed>% on the final. That's a scenario, not advice to stay."). On "draft",
follow "Act only with consent".

### Other details
- Establish the exact course section/session; the script infers it from
  Canvas dates and labels it Likely. Never apply Session C's deadline to
  Session B, A or non-standard courses.
- Treat semester enrolled hours, annual earned hours, cumulative GPA, and SAP
  as different calculations.
- Canvas's displayed current score alone is not enough for the final-exam
  math; use the assignment groups.

## Run
Write the gathered inputs to a JSON file shaped like `assets/sample_video.json`
(drop), `assets/sample_final.json` (final) or `assets/sample_plan.json` (plan),
then run the deterministic script:
- `python3 scripts/degree_domino.py drop --input <file> --rules rules/asu.json`
- `python3 scripts/degree_domino.py final --input <file>`
- `python3 scripts/degree_domino.py plan --input <file>` (degree and registration questions)

For unsupported schools, omit `--rules` and use generic mode. Interpret only
claims returned by the script; don't add unsourced policy verdicts.
`rules/asu.json` holds only university-wide policies (deadlines, W grade,
scholarship, aid).

Exit codes: 0 summarize the result; 2 ask for the named missing field (one
question); 3 rules unavailable, give generic arithmetic and say so; 4 give no
policy output, only the official source and manual arithmetic.

## Replies
Short plain text, no Markdown. Lead with the known course facts and deadline if
verified. Then show up to three key consequences, each marked Confirmed,
Likely, or Check with [office]. Provide a Future Fork: Stay / Withdraw /
Alternate plan with conditional effects, never a categorical recommendation.
Ask which option to explore or offer a precise office email draft.
If asked "sources", put official source URLs on their own lines
(see `references/sources.md`). Reply formats: `references/reply-formats.md`.
Grade math details: `references/grade-calculation.md`.

Never say "safe to drop", "you're fine", "you will lose" an award, or that
graduation will definitely be delayed.

## Act only with consent
Show an advisor/Financial Aid email draft; save as a Gmail draft only after yes;
never send. Never include student ID or invent a recipient address. Offer a
check-in only after yes, and confirm the course's own deadline and the user's
chosen check-in time and time zone.

## Missing data or errors
If Canvas is missing, take manual input. If the session, award, grade weights
or rules are still uncertain after reading Canvas, say what is known and point
to the office that can confirm it; ask the student only for something Canvas
doesn't show, and only one thing at a time. Do not claim that the student's
graduation or funding is guaranteed or lost. Never relay raw JSON.
