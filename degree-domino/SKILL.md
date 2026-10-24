---
name: degree-domino
description: Check what dropping or withdrawing from a class changes for credits, scholarship/financial aid, course prerequisites and deadlines before deciding. Use when a student says "should I drop", "what if I withdraw", "will this affect my scholarship", "what do I need on the final", or "thinking about withdrawing". Builds a short, sourced Future Fork comparison; not a generic study plan.
---

# Degree Domino

Help students understand the consequences of academic decisions; never make
an enrollment decision for them. Separate official rules from student-specific
impacts, and state uncertainty rather than guessing.

Gather everything below yourself first, then run the script, then reply once.
Do not open with a judgment ("maybe", "I wouldn't withdraw") before the
script has run, and never lean toward staying or withdrawing.

## Gather
1. Read the student's current-term courses and grades from Canvas yourself.
   Match what the student named ("cse240", "calc") to those courses. Pass the
   current course codes as `enrolled_courses` and where you read them as
   `enrolled_courses_source`. If the named course is not among them, the
   script returns `enrolled: false`: tell the student they aren't currently
   enrolled in that class and show the courses they are in. Stop there.
2. Find the student's major, concentration and catalog year yourself, in
   this order: memory; the student's My ASU profile or DARS degree audit,
   opened in the browser (the student signs in; never ask for a password);
   then their Canvas profile. Ask only if none of these shows it, and ask
   once. With consent, remember it so it is never asked again.
3. If Canvas is unavailable, say so in one line and continue in manual mode.
   Ask for just the next missing fact, starting with course credits and total
   enrolled hours.
4. Establish school, exact course section/session, and individual withdrawal
   deadline; check the course's Dates icon in My ASU if necessary. Never apply
   Session C's deadline to Session B, A or non-standard courses.
5. Look up course requirements live, every run; never rely on a stored list.
   a. Use the major, concentration and catalog year from step 2.
   b. Search the web for the ASU major map for that major and concentration
      and catalog year on degrees.asu.edu, open it, and list every course
      code on it. Pass them as `major.courses`, with `major.name`,
      `major.concentration`, `major.catalog_year` and the page URL as
      `major.source_url`.
   c. In the ASU course catalog (catalog.apps.asu.edu), open the dropped
      course and the courses on the major map that might need it (the
      student's planned next course first). Copy each course's
      "Enrollment requirements" text word for word into `requirement_text`
      and list the course codes it names in `requires`. If the catalog asks
      for an ASU login, open it in the browser and let the student sign in;
      never ask for their password.
   d. Record `fetched_at` as today's date for everything you read. If a page
      will not load, leave it out; the script then says "Check with your
      advisor" instead of guessing.
6. Ask scholarship type only if relevant. Treat semester enrolled hours,
   annual earned hours, cumulative GPA, and SAP as different calculations.
7. For final-needed: confirm weighted vs points-based grading, published grade
   cutoff, remaining items, and all relevant weights. Canvas's displayed current
   score alone is insufficient to infer an exact final needed.

## Run
Write the gathered inputs, including the student's local date as `today`, to a
JSON file shaped like `assets/sample_drop.json` or `assets/sample_final.json`,
then run the deterministic script:
- `python3 scripts/degree_domino.py drop --input <file> --rules rules/asu.json`
- `python3 scripts/degree_domino.py final --input <file>`

For unsupported schools, omit `--rules` and use generic mode. Interpret only
claims returned by the script; don't add unsourced policy verdicts.
`rules/asu.json` holds only university-wide policies (deadlines, W grade,
scholarship, aid). The script keeps only prerequisites for courses on the
student's major map and reports them in `dominoes_in_major`.

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
If Canvas is missing, take manual input. If date, award, grade weights or rules
are uncertain, say what is known and ask one specific follow-up or recommend
confirmation through the appropriate office. Do not claim that the student's
graduation or funding is guaranteed or lost. Never relay raw JSON.
