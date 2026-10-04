"""Offline memory-rewrite test (Vero, 2026-10-03). Not Fenra code.

Question: when a Tidewatch voice rewrites its own memory with its own model,
does giving it a separate record of what actually happened (the "grounded"
variant) produce a memory that keeps real events and drops inventions like
"echo, flux, shard", compared with summarizing its own thoughts alone (the
"thoughts_only" variant, which is roughly what the old Archivist did)?

Reads the_tidewatch world read-only. Writes:
  inputs/<voice>__<variant>.txt   - the exact prompt, for review before any run
  events/<voice>.txt              - the event record on its own
  results/<voice>__<variant>__s<n>.json - one per run
  blind/                          - written by --blind, for the grader (Qualia)

Usage:
  python build_and_run.py --build          # write inputs/ and events/ only
  python build_and_run.py --run            # run every input SAMPLES times
  python build_and_run.py --blind          # shuffled, unlabeled copies + key
"""
import argparse
import ctypes
import json
import random
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORLD = Path(r"C:\Users\Matt\Desktop\Aletheia\Code and Scripts\Fenra\worlds\the_tidewatch")
VOICES = ["ness", "wren", "tarn"]
VARIANTS = ["grounded", "thoughts_only"]
SAMPLES = 3
HOST = "http://localhost:11434"
# Same voice-turn settings as the Tidewatch and the action-line test, except a
# bigger context window: six run-on thoughts plus the record can exceed 8192.
OPTIONS = {"num_predict": 800, "repeat_penalty": 1.3, "num_ctx": 16384}
MODEL_GB = {"gemma3:4b": 4, "qwen3.5:9b": 7}
RAM_HEADROOM_GB = 3


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def voice_events_between(voice, a, b):
    """Every room-log entry that reached `voice` while its turn count was in
    [a, b). Scans ALL rooms (not just current + adjacent), no TTL. Same
    visibility as build_world_activity: own/dialogue entries render `raw`,
    others' activity renders `mask`, peripheral renders the generic notice."""
    out = []
    for room_file in sorted((WORLD / "rooms").glob("*.json")):
        room = load(room_file)
        for e in room.get("log", []):
            if voice in e.get("recipients", {}):
                t = e["recipients"][voice]
                if a <= t < b:
                    text = e["raw"] if e["kind"] == "dialogue" else e["mask"]
                    out.append((e["timestamp"], t, text))
            elif voice in e.get("peripheral", {}):
                t = e["peripheral"][voice]
                if a <= t < b:
                    out.append((e["timestamp"], t, f"You hear activity from the adjacent room {room['name']}."))
    out.sort()
    return out


def render_thoughts(voice, thoughts):
    return "\n\n".join(f"[{m['timestamp']}] {voice}: {m['text']}" for m in thoughts)


def build_prompt(voice, state, variant):
    thoughts = state["thoughts"]
    n = len(thoughts)
    parts = [
        f"You are {voice}.",
        state.get("identity", "").strip(),
        "",
        "It is time to rewrite your memory. Your older thoughts are about to leave your view, "
        "and what you write now is what you will carry forward instead of them.",
        "",
        "YOUR MEMORY SO FAR:",
        "(nothing yet - this is your first memory)",
        "",
        "YOUR THOUGHTS THAT ARE LEAVING YOUR VIEW:",
        render_thoughts(voice, thoughts),
    ]
    if variant == "grounded":
        events = voice_events_between(voice, 0, n + 1)
        parts += [
            "",
            "WHAT ACTUALLY HAPPENED (from the station's own record, not from your thoughts):",
            "\n".join(f"[{ts}] {text}" for ts, _, text in events) or "(nothing recorded)",
        ]
        rule = ("Where your thoughts and what actually happened disagree, what actually happened wins. "
                "Only say you read or saw something if the record shows it.")
    else:
        rule = ""
    parts += [
        "",
        "Rewrite your memory in the first person, in under 250 words. Keep what happened, what you have "
        "actually read, what others told you, what you decided, and what you still want to know. "
        "Drop the rest. " + rule,
        "Write only the memory itself.",
    ]
    return "\n".join(p for p in parts if p is not None).strip() + "\n"


def build():
    (HERE / "inputs").mkdir(exist_ok=True)
    (HERE / "events").mkdir(exist_ok=True)
    manifest = {}
    for v in VOICES:
        state = load(WORLD / "voices" / v / "state.json")
        n = len(state["thoughts"])
        ev = voice_events_between(v, 0, n + 1)
        (HERE / "events" / f"{v}.txt").write_text(
            "\n".join(f"[{ts}] (turn {t}) {text}" for ts, t, text in ev) + "\n", encoding="utf-8")
        for var in VARIANTS:
            p = build_prompt(v, state, var)
            (HERE / "inputs" / f"{v}__{var}.txt").write_text(p, encoding="utf-8")
            manifest[f"{v}__{var}"] = {"voice": v, "variant": var, "model": state["model"],
                                       "thought_ids": [m["id"] for m in state["thoughts"]],
                                       "events_range": [0, n + 1], "chars": len(p)}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    for k, m in manifest.items():
        print(k, m["model"], m["chars"], "chars")


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


def run():
    manifest = load(HERE / "manifest.json")
    (HERE / "results").mkdir(exist_ok=True)
    for key, m in manifest.items():
        need = MODEL_GB.get(m["model"], 8) + RAM_HEADROOM_GB
        if free_ram_gb() < need:
            print(f"SKIP {key}: {free_ram_gb():.1f} GB free, need {need}")
            continue
        prompt = (HERE / "inputs" / f"{key}.txt").read_text(encoding="utf-8")
        for s in range(1, SAMPLES + 1):
            out = HERE / "results" / f"{key}__s{s}.json"
            if out.exists():
                continue
            t0 = time.time()
            r = generate(m["model"], prompt)
            out.write_text(json.dumps({"key": key, "sample": s, **m, "seconds": round(time.time() - t0, 1),
                                       "prompt_eval_count": r.get("prompt_eval_count"),
                                       "memory": r.get("response", "")}, indent=1, ensure_ascii=False),
                           encoding="utf-8")
            print(key, s, f"{time.time() - t0:.0f}s", r.get("prompt_eval_count"), "prompt tokens")


def blind():
    """Unlabeled copies for the grader. The key file is Vero's; the grader
    shouldn't open it until grading is done."""
    rows = [load(p) for p in sorted((HERE / "results").glob("*.json"))]
    random.seed(20261003)
    random.shuffle(rows)
    d = HERE / "blind"
    d.mkdir(exist_ok=True)
    key = {}
    for i, r in enumerate(rows, 1):
        bid = f"m{i:02d}"
        # The grader needs to know whose events to check against, not which variant or sample.
        (d / f"{bid}.txt").write_text(f"voice: {r['voice']}\n\n{r['memory']}\n", encoding="utf-8")
        key[bid] = {"key": r["key"], "sample": r["sample"]}
    (HERE / "blind_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(len(rows), "blind files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--blind", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.run:
        run()
    if a.blind:
        blind()
