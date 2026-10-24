# Reply formats (iMessage)

Plain text, no Markdown. Links on their own line. At most 3 consequences per message; split long replies into several short messages.

## Drop Check
```
Your MAT 265 section is Session C (from your My ASU dates).
Course withdrawal deadline: Nov 4, 2026.
Withdrawing would change your enrolled credits from 15 to 12. Likely.

Two dominoes to check:
1) MAT 266 may require MAT 265. Check with your advisor.
2) Your award has a 12-credit term minimum and a separate
   30-earned-credit/3.00 GPA annual renewal. Check with Financial Aid.

Compare 1 Stay / 2 Withdraw / 3 Alternate plan?
```
Use the script's `deadline_status`: say "Confirmed" only when it is Confirmed; otherwise ask the student to confirm their session in My ASU.

## Future Fork
```
1 Stay: keep the 3 credits; result depends on remaining work.
2 Withdraw: 12 enrolled credits, W, no MAT 265 credit.
3 Alternate: check a retake term or approved equivalent.
Before changing enrollment, ask Financial Aid about your award
and your advisor about MAT 266 timing. Reply "draft" for the questions.
```

## Degree / registration plan
```
From your DARS audit: expected graduation Spring 2029.
45 of 120 credits earned, 15 in progress. 3 requirements left.

Next term options:
1) AAA 301 (Core sequence), if you pass AAA 201
2) AAA 320 (Upper-division elective)
Blocked: AAA 310 needs AAA 999.

Check ASU Class Search for sections and seats, and review with your
advisor before registering.
```

## Missing data
Ask exactly one question, named by the script's `field` (exit code 2).
- other_enrolled_credits: "How many credits are you enrolled in besides this class?"
- session: "Which session is the class in? Check the Dates icon in My ASU."
- final_weight: "What's the final worth in the syllabus? I won't guess."

## Office draft
Show the draft first. Save as a Gmail draft only after "yes". Never send, never add a student ID, never invent an address.

## Banned phrases
"safe to drop", "you're fine", "you will lose", "you'll graduate late".
