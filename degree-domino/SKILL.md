---
name: degree-domino
description: Check what dropping or withdrawing from a class changes for credits, scholarship/financial aid, course prerequisites and deadlines before deciding. Use when a student says "should I drop", "what if I withdraw", "will this affect my scholarship", "what do I need on the final", or "thinking about withdrawing". Builds a short, sourced Future Fork comparison; not a generic study plan.
---

# Degree Domino

Help students understand the consequences of academic decisions; never make
an enrollment decision for them. Separate official rules from student-specific
impacts, and state uncertainty rather than guessing.

## Gather
1. Reuse already authorized Canvas, memory and student course context where
   current; ask once for any new permission needed.
2. If Canvas is unavailable, continue in manual mode. Ask for just the next
   missing fact, starting with course credits and total enrolled hours.
3. Establish school, exact course section/session, and individual withdrawal
   deadline; check the course's Dates icon in My ASU if necessary. Never apply
   Session C's deadline to Session B, A or non-standard courses.
4. Identify the next course the student plans to take and verify its
   prerequisite from an official current catalog before claiming it is blocked.
5. Ask scholarship type only if relevant. Treat semester enrolled hours,
   annual earned hours, cumulative GPA, and SAP as different calculations.
6. For final-needed: confirm weighted vs points-based grading, published grade
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
