# Reply formats (iMessage)

Plain text, no Markdown. Links on their own line. At most 3 consequences per message; split long replies into several short messages.

## Drop Check (no questions; all from Canvas)
```
Let me check before you decide.
```
```
You're in CSE 240 this fall (Session C), showing 58% on Canvas.
Withdrawal deadline: Nov 4. Confirm your section's date in My ASU.
```
```
Withdrawing would take you from 15 to 12 enrolled credits.
```
```
Two dominoes to check:
1) CSE 340 and CSE 360 may require CSE 240. A W earns no credit toward it. Check with your advisor.
2) Your scholarship needs 12 enrolled credits this term, but renewal is separate: 30 earned credits and a 3.00 GPA this year. Check with Financial Aid.
```
```
Compare 1 Stay / 2 Withdraw / 3 Alternate?
```
Use the script's `deadline_status`: say "Confirmed" only when it is Confirmed. If the script assumed 3 credits for any class, add its note.

## Final exam (from Canvas assignment groups)
```
Your Canvas syllabus says the final is 40% and a C is 70%. With 58% on everything else, you'd need 88% on the final. That's a scenario, not advice to stay.
```

## Not enrolled
```
You aren't enrolled in PHY 121 this term, so there's nothing to withdraw from.
Your classes: CSE 240, CSE 230, MAT 265, ENG 102, HST 100.
```

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
