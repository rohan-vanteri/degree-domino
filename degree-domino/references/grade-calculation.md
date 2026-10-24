# Final-needed calculation

The Canvas displayed total alone is never enough: it can exclude ungraded work and ignore category weights.

Before running `final`, confirm:
1. Weighted or points-based grading (from the syllabus).
2. The published cutoff for the target grade. Never assume C = 70.
3. Whether the final is the only remaining work, and its weight.
4. The average on completed work, checked against the syllabus weights.

## Weighted, only the final remains
`needed = (target - g * (1 - w)) / w`
Example: g = 58, w = 0.40, target = 70 gives 88.

## Weighted, other work remains (weight u)
`needed = (target - g * (1 - w - u) - u * x) / w`, where x is a scenario score for the remaining work.
Without x the script returns three scenarios (60 / 75 / 90). Present them as a range, not one number.

## Points-based
`needed_points = target% * total_possible - earned - assumed_other_remaining`, divided by the final's possible points.

## Reporting
- Above 100: "not reachable under these assumptions unless extra credit applies".
- 0 or below: "already met under these assumptions".
- Always label Likely and list the assumptions. A reachable score is not advice to stay.

JSON shape: see `assets/sample_final.json`. Fields: grading_method, target_percentage, final_weight, nonfinal_aggregate, all_other_work_finalized, remaining_nonfinal_weight, remaining_nonfinal_scenario, earned_points, total_possible_points, final_possible_points, other_remaining_possible_points, assumed_other_points.
