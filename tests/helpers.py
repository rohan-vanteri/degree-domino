"""Shared helpers: load the engine module and run the CLI."""

import copy
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "degree-domino")
SCRIPT = os.path.join(SKILL, "scripts", "degree_domino.py")
RULES = os.path.join(SKILL, "rules", "asu.json")

_spec = importlib.util.spec_from_file_location("degree_domino", SCRIPT)
dd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dd)


def sample(name):
    with open(os.path.join(SKILL, "assets", name), encoding="utf-8") as f:
        return json.load(f)


def drop_input(**overrides):
    data = copy.deepcopy(sample("sample_drop.json"))
    course = overrides.pop("target_course", None)
    if course:
        data["target_course"].update(course)
    data.update(overrides)
    return data


def pack():
    return dd.load_rules(RULES)


def run_cli(*args, input_obj=None, tmpdir=None):
    """Run the script; returns (exit_code, parsed_json_or_text)."""
    argv = [sys.executable, "-I", SCRIPT, *args]
    if input_obj is not None:
        path = os.path.join(tmpdir, "input.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(input_obj, f)
        argv += ["--input", path]
    proc = subprocess.run(argv, capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except ValueError:
        return proc.returncode, proc.stdout


def all_text(obj):
    """Every user-facing string in an output, lowercased."""
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(all_text(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(all_text(v))
    elif isinstance(obj, str):
        out.append(obj.lower())
    return out
