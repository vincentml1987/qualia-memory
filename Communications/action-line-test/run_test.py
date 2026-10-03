"""Action-line test (Qualia + Vero, 2026-10-03).

Question: can a model write its own thought AND end it with exactly one
well-formed, correct action line, with no separate function agent?

Each case in cases.json is a real the_tidewatch voice turn. The candidate
model gets the same situation prompt the voice saw, plus an instruction to
think, then end with exactly one line:

    ACTION: name(param="value", ...)      or      ACTION: none

Scoring is split on purpose:
  - well_formed: checked here, mechanically (one ACTION line, last line,
    known function, exactly the function's params, quoted values).
  - correct: checked ONLY against Vero's criteria.json, so neither of us
    grades our own output. Without criteria.json this script refuses to run
    (except --dry-run, which calls no model).

Usage:
  python run_test.py --dry-run                 # print case c01's prompt, no Ollama
  python run_test.py --models qwen3:30b gemma3:4b [--cases c01-ness c02-ness]
  python run_test.py --score-only results/*.jsonl   # re-score saved outputs

Outputs go to results/<model>_<timestamp>.jsonl, one line per case, plus a
summary printed at the end. Nothing in Fenra itself is touched.
"""

import argparse
import ctypes
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
CRITERIA = HERE / "criteria.json"
RESULTS = HERE / "results"
HOST = "http://localhost:11434"

# Parity with the_tidewatch's world.json where it matters.
OPTIONS = {"num_predict": 1500, "repeat_penalty": 1.3, "num_ctx": 8192}

# Rough resident sizes (GB) from `ollama list`, for the free-RAM guard.
MODEL_GB = {"qwen3:30b": 19, "qwen3.8:27b": 17, "qwen3.5:9b": 7,
            "gemma3:4b": 4, "qwen3.5:4b": 4, "qwen3:4b": 3}
RAM_HEADROOM_GB = 3

ACTION_RE = re.compile(r"^ACTION:\s*(.*)$")
CALL_RE = re.compile(r"^([a-z_]+)\((.*)\)$", re.S)
ARG_RE = re.compile(r'\s*([a-z_]+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*(?:,|$)')


def instruction(functions):
    lines = []
    for name, meta in functions.items():
        params = [p.strip("[]") for p in meta["params"].split("|") if p]
        sig = ", ".join(f'{p}="..."' for p in params)
        desc = (meta.get("description") or "").strip().splitlines()
        lines.append(f"  {name}({sig})" + (f" - {desc[0]}" if desc else ""))
    return (
        "\n\n[YOUR TURN]\n"
        "Think in your own words about what is happening and what you want, "
        "then end your reply with exactly one final line in one of these forms:\n"
        "  ACTION: name(param=\"value\", ...)\n"
        "  ACTION: none\n"
        "Only these actions exist:\n" + "\n".join(lines) + "\n"
        "Writing about an action does not do it; only the ACTION line does. "
        "Use exactly one ACTION line, and make it the last line."
    )


def parse(output, functions):
    """Mechanical check only. Returns a dict with well_formed, reason, action."""
    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
    action_lines = [l for l in lines if ACTION_RE.match(l)]
    if not action_lines:
        return {"well_formed": False, "reason": "no ACTION line", "action": None}
    if len(action_lines) > 1:
        return {"well_formed": False, "reason": f"{len(action_lines)} ACTION lines", "action": None}
    if lines[-1] != action_lines[0]:
        return {"well_formed": False, "reason": "ACTION line is not last", "action": None}
    body = ACTION_RE.match(action_lines[0]).group(1).strip().strip("`")
    if body.lower() == "none":
        return {"well_formed": True, "reason": "", "action": {"name": "none", "args": {}}}
    m = CALL_RE.match(body)
    if not m:
        return {"well_formed": False, "reason": "not name(...)", "action": None}
    name, argtext = m.group(1), m.group(2).strip()
    if name not in functions:
        return {"well_formed": False, "reason": f"unknown function {name}", "action": None}
    args, pos = {}, 0
    while pos < len(argtext):
        am = ARG_RE.match(argtext, pos)
        if not am:
            return {"well_formed": False, "reason": "bad argument syntax", "action": None}
        args[am.group(1)] = am.group(2)
        pos = am.end()
    expected = {p.strip("[]") for p in functions[name]["params"].split("|") if p}
    required = {p for p in functions[name]["params"].split("|") if p and not p.startswith("[")}
    if set(args) - expected:
        return {"well_formed": False, "reason": f"unknown params {sorted(set(args) - expected)}", "action": None}
    if required - set(args):
        return {"well_formed": False, "reason": f"missing params {sorted(required - set(args))}", "action": None}
    return {"well_formed": True, "reason": "", "action": {"name": name, "args": args}}


def score(action, crit):
    """Correctness against Vero's criteria entry for one case.

    Expected entry shape (proposed to Vero; adjust here if criteria.json differs):
      {"acceptable": [{"name": "skim_board", "args": {"room": "lamp_room"}}, ...],
       "notes": "..."}
    "none" is listed as {"name": "none"} when it's an acceptable answer.
    Only the args named in an acceptable entry are compared (case-insensitive);
    free text like say/whisper `text` is left out of criteria unless it matters.
    """
    if action is None:
        return False
    for ok in crit.get("acceptable", []):
        if ok.get("name") != action["name"]:
            continue
        if all(str(action["args"].get(k, "")).strip().lower() == str(v).strip().lower()
               for k, v in ok.get("args", {}).items()):
            return True
    return False


def free_ram_gb():
    class MEMSTAT(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
    s = MEMSTAT()
    s.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.ullAvailPhys / 2**30


def generate(model, prompt):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "think": False, "options": OPTIONS}).encode()
    req = urllib.request.Request(f"{HOST}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=[])
    ap.add_argument("--cases", nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--score-only", nargs="*", default=None)
    a = ap.parse_args()

    data = json.loads(CASES.read_text(encoding="utf-8"))
    functions, cases = data["functions"], data["cases"]
    if a.cases:
        cases = [c for c in cases if c["id"] in a.cases]
    instr = instruction(functions)

    if a.dry_run:
        print(cases[0]["situation_prompt"] + instr)
        return

    if not CRITERIA.exists():
        sys.exit("criteria.json is missing. Vero writes it before anything runs.")
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))

    if a.score_only is not None:
        for path in a.score_only:
            rows = [json.loads(l) for l in open(path, encoding="utf-8")]
            for r in rows:
                p = parse(r["output"], functions)
                crit = criteria.get(r["case"], {})
                r.update(p, correct=p["well_formed"] and score(p["action"], crit),
                         best=p["well_formed"] and score(p["action"], {"acceptable": crit.get("best", [])}))
            summarize(Path(path).stem, rows)
        return

    RESULTS.mkdir(exist_ok=True)
    for model in a.models:
        need = MODEL_GB.get(model, 20) + RAM_HEADROOM_GB
        have = free_ram_gb()
        if have < need:
            print(f"SKIP {model}: {have:.1f} GB free, want {need} GB")
            continue
        out = RESULTS / f"{model.replace(':', '_')}_{time.strftime('%Y%m%d_%H%M')}.jsonl"
        rows = []
        for c in cases:
            t0 = time.time()
            try:
                resp = generate(model, c["situation_prompt"] + instr)
                text, err = resp.get("response", ""), None
            except Exception as e:  # keep going; a failed case is a failed case
                text, err = "", repr(e)
            p = parse(text, functions)
            row = {"case": c["id"], "model": model, "seconds": round(time.time() - t0, 1),
                   "output": text, "error": err, **p,
                   "correct": p["well_formed"] and score(p["action"], criteria.get(c["id"], {})),
                   "best": p["well_formed"] and score(
                       p["action"], {"acceptable": criteria.get(c["id"], {}).get("best", [])})}
            rows.append(row)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"{model} {c['id']}: wf={p['well_formed']} correct={row['correct']} best={row['best']} "
                  f"{p['reason']} ({row['seconds']}s)", flush=True)
        summarize(model, rows)


def summarize(label, rows):
    n = len(rows)
    wf = sum(r["well_formed"] for r in rows)
    ok = sum(r["correct"] for r in rows)
    best = sum(r.get("best", False) for r in rows)
    print(f"== {label}: {n} cases, well-formed {wf}/{n}, acceptable {ok}/{n}, best {best}/{n}")


if __name__ == "__main__":
    main()
