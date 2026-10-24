#!/usr/bin/env python3
"""Degree Domino deterministic engine.

Subcommands:
  drop   withdrawal preflight (deadline, enrolled credits, aid/scholarship and
         prerequisite tripwires, Stay / Withdraw / Alternate Future Fork)
  final  conditional final-exam-needed calculation

Standard library only. Never reads the machine clock: the student's local date
comes from the input's "today" field. Never writes files.

Exit codes: 0 ok, 2 missing/invalid input, 3 rule-pack failure, 4 unexpected.
"""

import argparse
import json
import os
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_CEILING

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SAMPLES = {
    "drop": os.path.join(SKILL_DIR, "assets", "sample_drop.json"),
    "final": os.path.join(SKILL_DIR, "assets", "sample_final.json"),
}

CONFIRMED = "Confirmed"
LIKELY = "Likely"
STALE_DAYS = 30
MAX_OUTPUT_CHARS = 8000

# Provenance values that count as verified against an official source.
VERIFIED_PROVENANCE = {"my_asu", "official_class_search", "official_catalog", "verified"}

STANDARD_SESSIONS = {"A", "B", "C"}


def check_with(office):
    return "Check with " + office


class InputError(Exception):
    """Missing or invalid input. `field` names what to ask the student for."""

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field
        self.message = message


class RulesError(Exception):
    """The rule pack could not be loaded."""


# ---------------------------------------------------------------- input helpers

def require(data, key, where="input"):
    if not isinstance(data, dict) or data.get(key) is None:
        raise InputError(key, "Missing %s.%s" % (where, key))
    return data[key]


def to_decimal(value, field, lo=None, hi=None):
    if isinstance(value, bool):
        raise InputError(field, "%s must be a number" % field)
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InputError(field, "%s must be a number" % field)
    if not d.is_finite():
        raise InputError(field, "%s must be a finite number" % field)
    if lo is not None and d < lo:
        raise InputError(field, "%s must be at least %s" % (field, lo))
    if hi is not None and d > hi:
        raise InputError(field, "%s must be at most %s" % (field, hi))
    return d


def parse_date(value, field):
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        raise InputError(field, "%s must be an ISO date (YYYY-MM-DD)" % field)


def num(d):
    """Render a Decimal as an int when whole, else a float, for JSON output."""
    if d == d.to_integral_value():
        return int(d)
    return float(d)


# ------------------------------------------------------------------ rule pack

def load_rules(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
        rules = {r["id"]: r for r in pack["rules"]}
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise RulesError(str(e))
    return {"school": pack.get("school"), "rules": rules}


def usable_rule(pack, rule_id, today):
    """Return the rule only if it is confirmed and checked within STALE_DAYS."""
    if not pack:
        return None
    rule = pack["rules"].get(rule_id)
    if not rule or rule.get("status") != "confirmed":
        return None
    try:
        checked = date.fromisoformat(rule["checked_at"])
    except (KeyError, ValueError):
        return None
    if (today - checked).days > STALE_DAYS or checked > today:
        return None
    return rule


def any_rule(pack, rule_id):
    """Return a rule regardless of status (used to cite a source link only)."""
    if not pack:
        return None
    return pack["rules"].get(rule_id)


# -------------------------------------------------------------- final needed

def compute_final(final, school_rules_used=False):
    """Conditional final-needed math (plan section 8.2).

    Returns a dict with grading_method, assumptions, status and either
    `needed` or `needed: None` plus `missing` naming the field to ask for.
    """
    if not isinstance(final, dict):
        return {"needed": None, "missing": "final",
                "reason": "No grading information supplied."}

    method = final.get("grading_method")
    target = final.get("target_percentage")
    result = {"grading_method": method, "assumptions": [], "status": LIKELY,
              "needed": None}

    if method not in ("weighted", "points"):
        result.update(missing="grading_method",
                      reason="Need to know if the syllabus is weighted or points-based.")
        return result
    if target is None:
        result.update(missing="target_percentage",
                      reason="Need the syllabus grade cutoff; won't assume one.")
        return result
    t = to_decimal(target, "target_percentage", 0, 100)
    result["assumptions"].append("Grade cutoff %s%% as reported" % num(t))

    if method == "weighted":
        return _final_weighted(final, t, result)
    return _final_points(final, t, result)


def _final_weighted(final, t, result):
    if final.get("final_weight") is None:
        result.update(missing="final_weight",
                      reason="Need the final's weight from the syllabus; won't guess.")
        return result
    w = to_decimal(final["final_weight"], "final_weight", Decimal(0), Decimal(1))
    if w == 0:
        raise InputError("final_weight", "final_weight must be greater than 0")

    if final.get("nonfinal_aggregate") is None:
        result.update(missing="nonfinal_aggregate",
                      reason="Need your average on the graded work, confirmed against "
                             "the syllabus weights (the Canvas total may exclude work).")
        return result
    g = to_decimal(final["nonfinal_aggregate"], "nonfinal_aggregate", 0)

    finalized = final.get("all_other_work_finalized") is True
    u_raw = final.get("remaining_nonfinal_weight")

    if finalized:
        # Case A: only the final remains.
        r = 1 - w
        needed = (t - g * r) / w
        result["assumptions"].append(
            "Only the final remains; it is worth %s%% and the other %s%% averages %s%%"
            % (num(w * 100), num(r * 100), num(g)))
        return _finish_needed(result, needed)

    if u_raw is None:
        result.update(missing="remaining_nonfinal_weight",
                      reason="Need to know whether other ungraded work remains and its weight.")
        return result

    # Case B: other ungraded work remains with weight u.
    u = to_decimal(u_raw, "remaining_nonfinal_weight", Decimal(0), 1 - w)
    done = 1 - w - u
    earned = g * done
    result["assumptions"].append(
        "Final worth %s%%, other remaining work %s%%, completed %s%% averages %s%%"
        % (num(w * 100), num(u * 100), num(done * 100), num(g)))

    x_raw = final.get("remaining_nonfinal_scenario")
    if x_raw is not None:
        x = to_decimal(x_raw, "remaining_nonfinal_scenario", 0)
        result["assumptions"].append("Remaining non-final work scored at %s%% (scenario)" % num(x))
        return _finish_needed(result, (t - earned - u * x) / w)

    scenarios = []
    for x in (Decimal(60), Decimal(75), Decimal(90)):
        n = (t - earned - u * x) / w
        scenarios.append({"remaining_work_score": num(x), "needed": num(n),
                          "reachable": n <= 100})
    result["scenarios"] = scenarios
    result["missing"] = "remaining_nonfinal_scenario"
    result["reason"] = "Other work still counts, so this is a range of scenarios, not one number."
    return result


def _final_points(final, t, result):
    for key in ("earned_points", "total_possible_points", "final_possible_points"):
        if final.get(key) is None:
            result.update(missing=key, reason="Points-based grading needs %s." % key)
            return result
    earned = to_decimal(final["earned_points"], "earned_points", 0)
    total = to_decimal(final["total_possible_points"], "total_possible_points", Decimal(0))
    fpp = to_decimal(final["final_possible_points"], "final_possible_points", Decimal(0))
    if total == 0 or fpp == 0:
        raise InputError("total_possible_points", "Possible points must be greater than 0")

    other_remaining = to_decimal(final.get("other_remaining_possible_points") or 0,
                                 "other_remaining_possible_points", 0)
    assumed_other = Decimal(0)
    if other_remaining > 0:
        if final.get("assumed_other_points") is None:
            result.update(missing="assumed_other_points",
                          reason="Other assignments remain; need an assumed score for them.")
            return result
        assumed_other = to_decimal(final["assumed_other_points"], "assumed_other_points",
                                   0, other_remaining)
        result["assumptions"].append("Assumed %s of %s points on other remaining work"
                                     % (num(assumed_other), num(other_remaining)))

    target_points = t / 100 * total
    needed_points = target_points - earned - assumed_other
    result["assumptions"].append("%s of %s total points; final worth %s points"
                                 % (num(earned), num(total), num(fpp)))
    result["needed_points"] = num(needed_points)
    return _finish_needed(result, needed_points / fpp * 100)


def _finish_needed(result, needed):
    result["needed"] = num(needed)
    result["needed_rounded_up"] = num(needed.to_integral_value(rounding=ROUND_CEILING))
    if needed > 100:
        result["interpretation"] = "Above 100% under these assumptions (unless extra credit applies)."
    elif needed <= 0:
        result["interpretation"] = "Target already met under these assumptions, if they are complete."
    else:
        result["interpretation"] = "Scenario estimate under these assumptions, not advice to stay or withdraw."
    return result


# ---------------------------------------------------------------------- drop

def compute_drop(data, pack):
    today = parse_date(require(data, "today"), "today")
    course = require(data, "target_course")
    code = require(course, "code", "target_course")
    credits = to_decimal(require(course, "credits", "target_course"), "target_course.credits", 0)
    other = to_decimal(require(data, "other_enrolled_credits"), "other_enrolled_credits", 0)

    school = str(data.get("school") or "").upper()
    asu = pack is not None and school == "ASU" and pack.get("school") == "ASU"
    sources = []

    def cite(rule):
        if rule and rule["id"] not in sources:
            sources.append(rule["id"])

    # Enrolled credits (enrollment, not earned credits).
    before = credits + other
    after = before - credits
    credits_verified = (course.get("credits_provenance") in VERIFIED_PROVENANCE
                        and data.get("other_credits_provenance") in VERIFIED_PROVENANCE)
    credit_status = CONFIRMED if credits_verified else LIKELY
    credit_text = "Enrolled credits: %s to %s if you withdraw from %s%s." % (
        num(before), num(after), code, "" if credits_verified else " (student-reported)")

    out = {
        "ok": True,
        "mode": "asu" if asu else "generic",
        "course": code,
        "today": today.isoformat(),
        "enrolled_credits_before": num(before),
        "enrolled_credits_after": num(after),
        "enrolled_credits_status": credit_status,
    }

    # Deadline: chosen by session and course type, never by semester name.
    out.update(_deadline(data, course, pack, asu, today, cite))

    headlines = [{"text": credit_text, "status": credit_status}]

    # Scholarship / aid tripwires.
    scholarships = [str(s).upper() for s in (data.get("scholarships") or [])]
    if asu and "NAMU" in scholarships:
        term = usable_rule(pack, "asu.namu.term_enrollment", today)
        annual = usable_rule(pack, "asu.namu.annual_earned", today)
        cite(term)
        cite(annual)
        sentences = []
        if term:
            minimum = Decimal(str(term["rule"]["credits"]))
            relation = "below" if after < minimum else "at or above"
            sentences.append("%s enrolled credits is %s this award's %s-credit term minimum."
                             % (num(after), relation, num(minimum)))
        if annual:
            renewal = ("Annual renewal is separate: %s earned credits and a %.2f GPA"
                       % (annual["rule"]["earned_credits"], annual["rule"]["cumulative_gpa"]))
            if data.get("annual_earned_asu_credits_so_far") is None or data.get("cumulative_asu_gpa") is None:
                renewal += "; your totals this year are unknown"
            sentences.append(renewal + ".")
        text = " ".join(sentences) or "Your scholarship rules could not be checked."
        headlines.append({"text": text, "status": check_with("Financial Aid")})
    elif scholarships:
        headlines.append({"text": "Your scholarship's credit rules aren't in my verified pack.",
                          "status": check_with("Financial Aid")})

    # Prerequisite tripwire: conditional unless the rule and plan are verified.
    nxt = data.get("planned_next_course")
    prereq = None
    if nxt:
        rid = "asu.prereq.%s_%s" % (code.replace(" ", ""), str(nxt).replace(" ", ""))
        prereq = usable_rule(pack, rid, today) if asu else None
        if prereq and data.get("next_course_rule_verified") is True:
            cite(prereq)
            headlines.append({"text": "%s requires %s (minimum %s). A W earns no credit for it."
                              % (nxt, code, prereq["rule"].get("min_grade", "grade per catalog")),
                              "status": CONFIRMED})
        else:
            cited = any_rule(pack, rid) if asu else None
            if cited:
                cite(cited)
            headlines.append({"text": "%s may require %s; withdrawing could block that plan. "
                                      "Prerequisite not yet verified in the current catalog." % (nxt, code),
                              "status": check_with("your advisor")})

    out["headlines"] = headlines[:3]

    # Future Fork: conditional paths, no recommended choice.
    w_rule = usable_rule(pack, "asu.grade.W", today) if asu else None
    sap_rule = usable_rule(pack, "asu.sap.W", today) if asu else None
    aid_rule = usable_rule(pack, "asu.aid.post_disbursement", today) if asu else None
    cite(w_rule)
    cite(sap_rule)
    cite(aid_rule)
    withdraw_bits = ["%s enrolled credits" % num(after)]
    if w_rule:
        withdraw_bits.append("W on transcript, no course credit, no GPA impact")
    else:
        withdraw_bits.append("no course credit; transcript/GPA effect per school policy")
    if sap_rule:
        withdraw_bits.append("W counts as attempted but not completed for aid pace")
    if aid_rule:
        withdraw_bits.append("aid may be recalculated")
    out["future_fork"] = [
        {"path": "Stay", "effect": "Keep %s credits; outcome depends on remaining work" % num(credits)},
        {"path": "Withdraw", "effect": "; ".join(withdraw_bits)},
        {"path": "Alternate", "effect": "Confirm retake term or approved equivalent and aid impact"},
    ]

    out["recommended_next_step"] = "Confirm award and course requirements before changing enrollment"

    # Final-needed scenario only when the grade composition is supplied.
    fin = data.get("final")
    if fin:
        f = compute_final(fin)
        out["final_needed"] = f if f.get("needed") is not None or f.get("scenarios") else None
        if out["final_needed"] is None:
            out["final_needed_missing"] = {"field": f.get("missing"), "reason": f.get("reason")}
    else:
        out["final_needed"] = None

    out["source_ids"] = sources
    if pack:
        out["sources"] = {sid: pack["rules"][sid]["source_url"] for sid in sources}
    return out


def _deadline(data, course, pack, asu, today, cite):
    session = course.get("session")
    if session is None:
        return {"deadline": None,
                "deadline_status": check_with("My ASU"),
                "deadline_note": "Session unknown. Check the class's Dates icon in My ASU."}
    session = str(session).strip().upper()

    if not asu:
        return {"deadline": None, "deadline_status": check_with("your registrar"),
                "deadline_note": "No verified deadline rules for this school."}

    if session not in STANDARD_SESSIONS:
        rule = usable_rule(pack, "asu.deadline.nonstandard", today)
        cite(rule)
        individual = course.get("individual_deadline")
        if individual and course.get("deadline_provenance") in VERIFIED_PROVENANCE:
            d = parse_date(individual, "target_course.individual_deadline")
            return _deadline_result(d, today, CONFIRMED, "Individual date from My ASU")
        return {"deadline": None, "deadline_status": check_with("My ASU"),
                "deadline_note": "Non-standard session: deadline is prorated. "
                                 "Check the class's Dates icon in My ASU."}

    term = str(data.get("term") or "").lower().replace(" ", "-")
    rid = "asu.deadline.withdraw.fa26%s" % session if term == "fall-2026" else None
    rule = usable_rule(pack, rid, today) if rid else None
    if not rule:
        return {"deadline": None, "deadline_status": check_with("My ASU"),
                "deadline_note": "No current verified deadline for this term/session."}
    cite(rule)
    d = date.fromisoformat(rule["rule"]["date"])
    session_verified = course.get("session_provenance") in VERIFIED_PROVENANCE
    status = CONFIRMED if session_verified else LIKELY
    note = "Standard Session %s date%s" % (
        session, "" if session_verified else "; verify your section's session in My ASU")
    return _deadline_result(d, today, status, note)


def _deadline_result(d, today, status, note):
    days = (d - today).days
    res = {"deadline": d.isoformat(), "deadline_status": status, "deadline_note": note,
           "days_left": days, "deadline_passed": days < 0}
    if days < 0:
        res["deadline_note"] += ". This deadline has passed; ordinary course withdrawal is closed."
    return res


# ----------------------------------------------------------------------- CLI

def emit(obj):
    text = json.dumps(obj, indent=2)
    if len(text) > MAX_OUTPUT_CHARS:
        text = json.dumps(obj, separators=(",", ":"))
    print(text)


def read_input(args):
    path = SAMPLES[args.command] if args.sample else args.input
    if not path:
        raise InputError("input", "Pass --input <file> or --sample")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise InputError("input", "Could not read input JSON: %s" % e)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Degree Domino engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("drop", "final"):
        p = sub.add_parser(name)
        p.add_argument("--input")
        p.add_argument("--sample", action="store_true")
        if name == "drop":
            p.add_argument("--rules")
    args = parser.parse_args(argv)

    try:
        data = read_input(args)
        if args.command == "drop":
            try:
                pack = load_rules(args.rules)
            except RulesError as e:
                emit({"ok": False, "error": "rules_unavailable", "detail": str(e),
                      "fallback": "generic arithmetic only"})
                return 3
            emit(compute_drop(data, pack))
        else:
            fin = data.get("final", data) if isinstance(data, dict) else data
            result = compute_final(fin)
            result["ok"] = result.get("needed") is not None or bool(result.get("scenarios"))
            emit(result)
        return 0
    except InputError as e:
        emit({"ok": False, "error": "missing_or_invalid_input", "field": e.field,
              "message": e.message})
        return 2
    except Exception as e:  # noqa: BLE001 - last-resort guard, no fabricated output
        emit({"ok": False, "error": "unexpected", "detail": type(e).__name__})
        return 4


if __name__ == "__main__":
    sys.exit(main())
