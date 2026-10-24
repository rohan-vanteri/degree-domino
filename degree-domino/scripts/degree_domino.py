#!/usr/bin/env python3
"""Degree Domino deterministic engine.

Subcommands:
  drop   withdrawal preflight (deadline, enrolled credits, aid/scholarship and
         prerequisite tripwires, Stay / Withdraw / Alternate Future Fork)
  final  conditional final-exam-needed calculation
  plan   degree progress and next-term suggestions from the DARS audit

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
    "plan": os.path.join(SKILL_DIR, "assets", "sample_plan.json"),
}

CONFIRMED = "Confirmed"
LIKELY = "Likely"
STALE_DAYS = 30
MAX_OUTPUT_CHARS = 8000

# Provenance values that count as verified against an official source.
VERIFIED_PROVENANCE = {"my_asu", "official_class_search", "official_catalog", "verified"}

STANDARD_SESSIONS = {"A", "B", "C"}

# Course data is read live by Cubbie each run; only these hosts count as official.
OFFICIAL_HOSTS = {"catalog.apps.asu.edu", "degrees.asu.edu", "degrees.apps.asu.edu",
                  "catalog.asu.edu"}
LIVE_STALE_DAYS = 7


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



# -------------------------------------------------------------- final needed

def from_canvas_groups(final):
    """Turn Canvas assignment groups into the weighted inputs compute_final uses.

    `canvas_groups`: [{"name", "weight", "score", "complete", "is_final"}]
    where weight and score are percents. The final is the group marked
    is_final (or named "final"). Completed groups give the average on graded
    work; incomplete non-final groups become remaining_nonfinal_weight.
    """
    groups = final.get("canvas_groups")
    if not groups:
        return final
    final = dict(final)
    final.setdefault("grading_method", "weighted")
    total = sum(to_decimal(g.get("weight", 0), "canvas_groups.weight", 0) for g in groups)
    if total <= 0:
        raise InputError("canvas_groups", "Assignment group weights must add up to more than 0")
    fin = [g for g in groups if g.get("is_final")] or \
        [g for g in groups if "final" in str(g.get("name", "")).lower()]
    if len(fin) != 1:
        final["final_weight"] = None
        return final
    w = to_decimal(fin[0]["weight"], "canvas_groups.weight", 0) / total
    done_w = Decimal(0)
    done_pts = Decimal(0)
    remaining = Decimal(0)
    for g in groups:
        if g is fin[0]:
            continue
        gw = to_decimal(g.get("weight", 0), "canvas_groups.weight", 0) / total
        if g.get("complete") and g.get("score") is not None:
            done_w += gw
            done_pts += gw * to_decimal(g["score"], "canvas_groups.score", 0)
        else:
            remaining += gw
    final["final_weight"] = num(w)
    final["nonfinal_aggregate"] = num(done_pts / done_w) if done_w else None
    final["all_other_work_finalized"] = remaining == 0
    final["remaining_nonfinal_weight"] = num(remaining)
    final["source"] = "canvas_assignment_groups"
    return final


def compute_final(final, school_rules_used=False):
    """Conditional final-needed math (plan section 8.2).

    Returns a dict with grading_method, assumptions, status and either
    `needed` or `needed: None` plus `missing` naming the field to ask for.
    """
    if not isinstance(final, dict):
        return {"needed": None, "missing": "final",
                "reason": "No grading information supplied."}
    final = from_canvas_groups(final)

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

def _course_code(c):
    return norm_course(c.get("code") if isinstance(c, dict) else c)


def infer_session(start, end):
    """Guess an ASU A/B/C session from a Canvas course's start and end dates.

    Full-semester courses (roughly 12+ weeks) are Session C; 7.5-week courses
    starting in the first half of the term are A, later ones B. The result is
    labeled as inferred so it is never reported as Confirmed.
    """
    try:
        s, e = date.fromisoformat(str(start)[:10]), date.fromisoformat(str(end)[:10])
    except ValueError:
        return None
    length = (e - s).days
    if length >= 84:
        return "C"
    if length <= 63:
        return "A" if s.month in (1, 8) or (s.month in (2, 9) and s.day < 20) else "B"
    return None


def apply_canvas(data):
    """Fill drop-check inputs from the student's Canvas courses so Cubbie never
    has to ask: target credits and session, other enrolled credits, current
    score. Each course in `enrolled_courses` may be a code or an object
    {"code", "credits", "start", "end", "current_score"}. Missing credits are
    assumed to be 3 and flagged as an assumption.
    """
    enrolled = data.get("enrolled_courses")
    if not isinstance(enrolled, list) or not any(isinstance(c, dict) for c in enrolled):
        return data
    data = json.loads(json.dumps(data))
    course = data.setdefault("target_course", {})
    target = norm_course(course.get("code", ""))
    assumed = []
    other = Decimal(0)
    for c in data["enrolled_courses"]:
        entry = c if isinstance(c, dict) else {"code": c}
        code = norm_course(entry.get("code", ""))
        if entry.get("credits") is not None:
            cr = to_decimal(entry["credits"], "enrolled_courses.credits", 0)
        else:
            cr = DEFAULT_COURSE_CREDITS
            assumed.append(code)
        if code == target:
            course.setdefault("credits", num(cr))
            if entry.get("credits") is None:
                course.setdefault("credits_provenance", "assumed_3")
            if course.get("session") is None and entry.get("start") and entry.get("end"):
                guess = infer_session(entry["start"], entry["end"])
                if guess:
                    course["session"] = guess
                    course["session_provenance"] = "canvas_dates"
            if entry.get("current_score") is not None:
                course.setdefault("canvas_displayed_score", entry["current_score"])
        else:
            other += cr
    if data.get("other_enrolled_credits") is None:
        data["other_enrolled_credits"] = num(other)
        data.setdefault("other_credits_provenance", "canvas_course_list")
    if assumed:
        data["credits_assumed_for"] = assumed
    return data


def compute_drop(data, pack):
    data = apply_canvas(data)
    today = parse_date(require(data, "today"), "today")
    course = require(data, "target_course")
    code = require(course, "code", "target_course")
    # Enrollment check before anything else: with the student's current
    # courses (read from Canvas or My ASU), a class they aren't in stops here.
    enrolled = data.get("enrolled_courses")
    if isinstance(enrolled, list):
        current = [_course_code(c) for c in enrolled]
        if norm_course(code) not in current:
            return {"ok": True, "enrolled": False, "course": norm_course(code),
                    "today": today.isoformat(), "current_courses": current,
                    "message": "You aren't currently enrolled in %s, so there is nothing to "
                               "withdraw from." % norm_course(code),
                    "enrollment_source": data.get("enrolled_courses_source")}

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
    if credits_verified:
        note = ""
    elif data.get("credits_assumed_for"):
        note = " (assuming 3 credits for %s; check My ASU)" % ", ".join(data["credits_assumed_for"])
    elif data.get("other_credits_provenance") == "canvas_course_list":
        note = " (from your Canvas course list)"
    else:
        note = " (student-reported)"
    credit_text = "Enrolled credits: %s to %s if you withdraw from %s%s." % (
        num(before), num(after), code, note)

    out = {
        "ok": True,
        "enrolled": True if isinstance(enrolled, list) else None,
        "mode": "asu" if asu else "generic",
        "course": code,
        "today": today.isoformat(),
        "enrolled_credits_before": num(before),
        "enrolled_credits_after": num(after),
        "enrolled_credits_status": credit_status,
        "credits_assumed_for": data.get("credits_assumed_for"),
        "session": course.get("session"),
        "session_inferred": True if course.get("session_provenance") == "canvas_dates" else None,
        "canvas_score": course.get("canvas_displayed_score"),
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

    # Prerequisite tripwire, from requirements Cubbie read live this run and
    # filtered to the student's major. Nothing course-specific is hard-coded.
    live = _live_prereqs(data, code, today)
    out["major"] = live["major"]
    out["dominoes_in_major"] = live["dominoes"]
    if live["headline"]:
        headlines.append(live["headline"])

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

    for key in ("credits_assumed_for", "session_inferred", "canvas_score"):
        if out.get(key) is None:
            out.pop(key, None)
    out["source_ids"] = sources
    out["sources"] = {sid: pack["rules"][sid]["source_url"] for sid in sources} if pack else {}
    out["sources"].update(live["sources"])
    return out


def norm_course(code):
    """'mat265', 'MAT 265' and 'MAT  265' all become 'MAT 265'."""
    text = "".join(str(code).split()).upper()
    i = 0
    while i < len(text) and text[i].isalpha():
        i += 1
    return (text[:i] + " " + text[i:]).strip()


def _official_url(url):
    """True for an https URL on an official ASU catalog or degree host."""
    url = str(url or "")
    if not url.startswith("https://"):
        return False
    host = url[len("https://"):].split("/", 1)[0].lower()
    return host in OFFICIAL_HOSTS


def _fresh(stamp, today):
    try:
        d = date.fromisoformat(str(stamp)[:10])
    except ValueError:
        return False
    return d <= today and (today - d).days <= LIVE_STALE_DAYS


def _live_prereqs(data, code, today):
    """Build prerequisite dominoes from data Cubbie fetched during this run.

    `major`: {"name", "catalog_year", "source_url", "fetched_at", "courses": [...]}
        read from the student's ASU major map. Courses outside it are ignored.
    `prerequisites`: [{"course", "requires": [...], "requirement_text",
        "source_url", "fetched_at"}] read from the ASU catalog.

    A requirement is Confirmed only when it comes from an official ASU page,
    was fetched within LIVE_STALE_DAYS, and its quoted text names the course
    being dropped. Anything else is "Check with your advisor".
    """
    target = norm_course(code)
    result = {"major": None, "dominoes": [], "headline": None, "sources": {}}

    major = data.get("major")
    major_courses = None
    if isinstance(major, dict) and major.get("courses"):
        major_ok = _official_url(major.get("source_url")) and _fresh(major.get("fetched_at"), today)
        major_courses = {norm_course(c) for c in major["courses"]}
        result["major"] = {"name": major.get("name"), "concentration": major.get("concentration"),
                           "catalog_year": major.get("catalog_year"),
                           "course_count": len(major_courses), "verified": major_ok}
        if major_ok:
            result["sources"]["major_map"] = major["source_url"]

    planned = data.get("planned_next_course")
    planned = norm_course(planned) if planned else None

    for i, p in enumerate(data.get("prerequisites") or []):
        if not isinstance(p, dict) or not p.get("course"):
            continue
        course = norm_course(p["course"])
        requires = {norm_course(r) for r in (p.get("requires") or [])}
        requires |= {norm_course(r) for r in (p.get("requires_any_of") or [])}
        if target not in requires:
            continue
        # Major filter: keep only courses on the student's major map, plus the
        # course the student says they plan to take next.
        if major_courses is not None and course not in major_courses and course != planned:
            continue
        quoted = "".join(str(p.get("requirement_text") or "").split()).upper()
        verified = (_official_url(p.get("source_url")) and _fresh(p.get("fetched_at"), today)
                    and "".join(target.split()) in quoted)
        entry = {"course": course, "requires": sorted(requires),
                 "requirement_text": p.get("requirement_text"),
                 "in_major": major_courses is not None and course in major_courses,
                 "status": CONFIRMED if verified else check_with("your advisor")}
        result["dominoes"].append(entry)
        if verified:
            result["sources"]["prereq.%s" % course.replace(" ", "")] = p["source_url"]

    dominoes = result["dominoes"]
    planned_hit = [d for d in dominoes if d["course"] == planned]
    lead = planned_hit[0] if planned_hit else (dominoes[0] if dominoes else None)

    if lead:
        others = [d["course"] for d in dominoes if d is not lead]
        verb = "requires" if lead["status"] == CONFIRMED else "may require"
        text = "%s %s %s; a W earns no credit toward it." % (lead["course"], verb, target)
        if lead["status"] == CONFIRMED and lead["requirement_text"]:
            text += ' Catalog: "%s"' % str(lead["requirement_text"])[:160]
        if others:
            label = "Also in your major" if major_courses is not None else "Also"
            text += " %s: %s." % (label, ", ".join(others[:4]))
        result["headline"] = {"text": text, "status": lead["status"]}
    elif planned:
        result["headline"] = {"text": "%s may depend on %s; I couldn't confirm it in the ASU catalog."
                                      % (planned, target),
                              "status": check_with("your advisor")}
    return result


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

# ---------------------------------------------------------------------- plan

DEFAULT_COURSE_CREDITS = Decimal(3)
MAX_REQUIREMENTS = 8
MAX_OPTIONS = 3


def _asu_url(url):
    """True for an https URL on asu.edu or one of its subdomains (DARS, My ASU)."""
    url = str(url or "")
    if not url.startswith("https://"):
        return False
    host = url[len("https://"):].split("/", 1)[0].lower()
    return host == "asu.edu" or host.endswith(".asu.edu")


def _prereq_index(data, today):
    """Map course -> list of fetched requirement records."""
    index = {}
    for p in data.get("prerequisites") or []:
        if isinstance(p, dict) and p.get("course"):
            index.setdefault(norm_course(p["course"]), []).append(p)
    return index


def _prereq_status(course, index, done, pending, today):
    """Decide whether a course's fetched prerequisites are met.

    Returns (state, missing, verified). state is one of: met, met_if_passing,
    blocked, unchecked. `requires` means all of; `requires_any_of` one of.
    """
    records = index.get(course)
    if not records:
        return "unchecked", [], False
    have_now = done
    have_after = done | pending
    missing = []
    met_now = met_after = True
    verified = True
    for p in records:
        all_of = {norm_course(c) for c in (p.get("requires") or [])}
        any_of = {norm_course(c) for c in (p.get("requires_any_of") or [])}
        quoted = "".join(str(p.get("requirement_text") or "").split()).upper()
        named = all_of | any_of
        verified = verified and _official_url(p.get("source_url")) and _fresh(p.get("fetched_at"), today) \
            and all("".join(c.split()) in quoted for c in named)
        if not all_of <= have_now or (any_of and not any_of & have_now):
            met_now = False
        lacking = sorted(all_of - have_after)
        if any_of and not any_of & have_after:
            lacking.append(" or ".join(sorted(any_of)))
        if lacking:
            met_after = False
            missing.extend(lacking)
    if met_now:
        return "met", [], verified
    if met_after:
        return "met_if_passing", sorted((set().union(*[
            {norm_course(c) for c in (p.get("requires") or []) + (p.get("requires_any_of") or [])}
            for p in records]) & pending)), verified
    return "blocked", missing, verified


def compute_plan(data):
    """Degree progress and next-term suggestions from the student's DARS audit.

    Everything about the student comes from `dars` (read live from DARS) and
    `enrolled_courses` (current classes). Suggestions are courses that fill an
    unmet DARS requirement and whose fetched prerequisites are met; the script
    never claims a section is offered or has seats.
    """
    today = parse_date(require(data, "today"), "today")
    dars = require(data, "dars")
    if not isinstance(dars, dict):
        raise InputError("dars", "dars must be an object read from the DARS audit")

    dars_ok = _asu_url(dars.get("source_url")) and _fresh(dars.get("fetched_at"), today)
    source_status = CONFIRMED if dars_ok else check_with("your advisor")

    done = {norm_course(c) for c in (dars.get("completed_courses") or [])}
    pending = {norm_course(c) for c in (dars.get("in_progress_courses") or [])}
    pending |= {norm_course(c) for c in (data.get("enrolled_courses") or [])}
    pending -= done

    out = {"ok": True, "today": today.isoformat(), "dars_status": source_status,
           "major": {"name": dars.get("major"), "concentration": dars.get("concentration"),
                     "catalog_year": dars.get("catalog_year")}}

    # Progress, exactly as DARS reports it. No date is calculated or guessed.
    progress = {"expected_graduation": dars.get("expected_graduation"),
                "expected_graduation_source": "DARS audit" if dars.get("expected_graduation") else None}
    if dars.get("credits_earned") is not None and dars.get("credits_required") is not None:
        earned = to_decimal(dars["credits_earned"], "dars.credits_earned", 0)
        needed = to_decimal(dars["credits_required"], "dars.credits_required", 0)
        progress.update(credits_earned=num(earned), credits_required=num(needed),
                        credits_remaining=num(max(needed - earned, Decimal(0))))
    if dars.get("credits_in_progress") is not None:
        progress["credits_in_progress"] = num(to_decimal(dars["credits_in_progress"],
                                                         "dars.credits_in_progress", 0))
    if not dars.get("expected_graduation"):
        progress["expected_graduation_note"] = "DARS shows no expected graduation term."
    out["progress"] = progress

    credits_map = {norm_course(k): to_decimal(v, "course_credits", 0)
                   for k, v in (data.get("course_credits") or {}).items()}
    index = _prereq_index(data, today)

    unmet = [r for r in (dars.get("unmet_requirements") or []) if isinstance(r, dict)]
    out["requirements_left"] = len(unmet)
    requirements = []
    suggestions = []
    seen = set()
    for req in unmet[:MAX_REQUIREMENTS]:
        options = []
        for c in req.get("course_options") or []:
            c = norm_course(c)
            if c in done or c in pending:
                continue
            state, missing, verified = _prereq_status(c, index, done, pending, today)
            options.append({"course": c, "prerequisites": state, "missing": missing,
                            "status": CONFIRMED if state in ("met", "met_if_passing") and verified
                            else check_with("your advisor")})
        rank = {"met": 0, "met_if_passing": 1, "unchecked": 2, "blocked": 3}
        options.sort(key=lambda o: rank[o["prerequisites"]])
        requirements.append({"requirement": req.get("name"),
                             "credits_needed": req.get("credits_needed"),
                             "options": options[:MAX_OPTIONS]})
        pick = next((o for o in options if o["prerequisites"] in ("met", "met_if_passing")
                     and o["course"] not in seen), None)
        if pick:
            seen.add(pick["course"])
            credits = credits_map.get(pick["course"])
            suggestions.append({"course": pick["course"], "fills": req.get("name"),
                                "credits": num(credits if credits is not None else DEFAULT_COURSE_CREDITS),
                                "credits_assumed": credits is None,
                                "condition": ("if you pass " + ", ".join(pick["missing"]))
                                if pick["prerequisites"] == "met_if_passing" else None,
                                "status": pick["status"]})
    out["requirements"] = requirements

    # Trim to the student's target load, if they gave one.
    target = data.get("target_credits")
    if target is not None:
        limit = to_decimal(target, "target_credits", 0)
        total = Decimal(0)
        kept = []
        for s in suggestions:
            c = Decimal(str(s["credits"]))
            if total + c <= limit:
                kept.append(s)
                total += c
        suggestions = kept
    out["suggested_next_term"] = suggestions
    out["suggested_credits"] = num(sum((Decimal(str(s["credits"])) for s in suggestions), Decimal(0)))
    out["registration_note"] = ("Check ASU Class Search for sections, times and seats before "
                                "registering; suggestions don't confirm a class is offered.")
    out["recommended_next_step"] = "Review these with your advisor before registering"

    sources = {}
    if dars_ok:
        sources["dars"] = dars["source_url"]
    for c, records in index.items():
        for p in records:
            if _official_url(p.get("source_url")):
                sources["prereq.%s" % c.replace(" ", "")] = p["source_url"]
    out["sources"] = sources
    return out


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
    for name in ("drop", "final", "plan"):
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
        elif args.command == "plan":
            emit(compute_plan(data))
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
