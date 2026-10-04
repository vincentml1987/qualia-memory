"""Round 2: ledger + reflection (Vero, 2026-10-03). Not Fenra code.

The memory is two parts. The LEDGER is built mechanically from the station's
record: fixed second-person sentences, with no model involved. The REFLECTION is
written by the voice's own model next to it. Question: does the reflection still
contradict the ledger? Qualia's `contradicts_ledger` field measures that cost.

Variants:
  with_thoughts - ledger + the voice's leaving thoughts
  ledger_only   - ledger alone, testing whether the trap comes from re-reading
                  the voice's own invention

Usage: python round2.py --build | --run | --blind
Outputs go under round2/ (inputs/, ledgers/, results/, blind/, blind_key.json).
"""
import argparse
import json
import random
import time
from pathlib import Path

import build_and_run as r1

HERE = Path(__file__).resolve().parent / "round2"
VARIANTS = ["with_thoughts", "ledger_only"]


def _after_colon(text):
    return text.split(": ", 1)[1] if ": " in text else text


def ledger_lines(voice, a, b):
    """Fixed-form sentences for everything that reached `voice` in turns [a, b).
    Speaker attribution comes from the log entry's actor and act fields, never
    from prose, so it can't be swapped. "said" and "read" never share a sentence."""
    lines = []
    for room_file in sorted((r1.WORLD / "rooms").glob("*.json")):
        room = r1.load(room_file)
        rname = room["name"]
        for e in room.get("log", []):
            actor, act = e["actor"], e["act"]
            if voice in e.get("recipients", {}):
                t = e["recipients"][voice]
                if not (a <= t < b):
                    continue
                me = actor == voice
                if act == "say":
                    s = f"You said aloud: \"{_after_colon(e['raw'])}\"" if me else f"{actor} said aloud: \"{_after_colon(e['raw'])}\""
                elif act == "yell":
                    s = f"You yelled: \"{_after_colon(e['raw'])}\"" if me else f"{actor} yelled: \"{_after_colon(e['raw'])}\""
                elif act == "whisper":
                    target = e["mask"].rstrip(".").split(" whispered to ", 1)[-1]
                    if me:
                        s = f"You whispered to {target}: \"{_after_colon(e['raw'])}\""
                    elif target == voice:
                        s = f"{actor} whispered to you: \"{_after_colon(e['raw'])}\""
                    else:
                        s = f"{actor} whispered something to {target}. You did not hear what."
                elif act == "move_room":
                    s = f"You moved to {rname}." if me else f"{actor} arrived in {rname}."
                elif act == "create_room":
                    s = f"You created the room {rname} and moved into it." if me else f"{actor} created a room."
                elif act == "skim_board":
                    if me:
                        s = f"You skimmed the {rname} board. It held:\n{_after_colon(e['raw'])}"
                    else:
                        s = f"{actor} skimmed the {rname} board. You did not see what it held."
                elif act == "read_board":
                    s = f"You read a post on the {rname} board: {_after_colon(e['raw'])}" if me else f"{actor} read a post on the {rname} board."
                else:
                    s = e["mask"] if not me else _after_colon(e["raw"])
                lines.append((e["timestamp"], s))
            elif voice in e.get("peripheral", {}):
                t = e["peripheral"][voice]
                if a <= t < b:
                    lines.append((e["timestamp"], f"You heard activity from the {rname}."))
    lines.sort()
    return [s for _, s in lines]


def board_status_lines(voice):
    """What the voice has actually opened, from each board's `seen` map."""
    out = []
    for room_file in sorted((r1.WORLD / "rooms").glob("*.json")):
        room = r1.load(room_file)
        board = room.get("board", [])
        if not board:
            continue
        seen = [p for p in board if voice in p.get("seen", {})]
        posts = "1 post" if len(board) == 1 else f"{len(board)} posts"
        if not seen:
            out.append(f"You have not opened the {room['name']} board ({posts}).")
        else:
            out.append(f"Of the {posts} on the {room['name']} board, you have looked at {len(seen)}.")
    return out


def build_ledger(voice, n):
    return "\n".join(["- " + s for s in ledger_lines(voice, 0, n + 1)] +
                     ["- " + s for s in board_status_lines(voice)])


def build_prompt(voice, state, variant, ledger):
    parts = [
        f"You are {voice}.",
        state.get("identity", "").strip(),
        "",
        "It is time to write your memory. It has two parts.",
        "",
        "PART ONE, WHAT HAPPENED. This is written by the station from its own record. It is already "
        "kept for you, and you cannot change it:",
        ledger,
    ]
    if variant == "with_thoughts":
        parts += ["", "YOUR THOUGHTS THAT ARE LEAVING YOUR VIEW:", r1.render_thoughts(voice, state["thoughts"])]
    parts += [
        "",
        "PART TWO, YOUR REFLECTION. Write it now, in the first person, in under 150 words: what these "
        "events mean to you, what you want to do next, and what you still wonder about. Do not retell the "
        "events; part one keeps them. Do not say anything happened that part one does not show.",
        "Write only your reflection.",
    ]
    return "\n".join(parts).strip() + "\n"


def build():
    for d in ("inputs", "ledgers"):
        (HERE / d).mkdir(parents=True, exist_ok=True)
    manifest = {}
    for v in r1.VOICES:
        state = r1.load(r1.WORLD / "voices" / v / "state.json")
        n = len(state["thoughts"])
        ledger = build_ledger(v, n)
        (HERE / "ledgers" / f"{v}.txt").write_text(ledger + "\n", encoding="utf-8")
        for var in VARIANTS:
            p = build_prompt(v, state, var, ledger)
            (HERE / "inputs" / f"{v}__{var}.txt").write_text(p, encoding="utf-8")
            manifest[f"{v}__{var}"] = {"voice": v, "variant": var, "model": state["model"],
                                       "events_range": [0, n + 1], "chars": len(p)}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    for k, m in manifest.items():
        print(k, m["model"], m["chars"], "chars")


def run():
    manifest = r1.load(HERE / "manifest.json")
    (HERE / "results").mkdir(exist_ok=True)
    for key, m in manifest.items():
        need = r1.MODEL_GB.get(m["model"], 8) + r1.RAM_HEADROOM_GB
        if r1.free_ram_gb() < need:
            print(f"SKIP {key}: {r1.free_ram_gb():.1f} GB free, need {need}")
            continue
        prompt = (HERE / "inputs" / f"{key}.txt").read_text(encoding="utf-8")
        for s in range(1, r1.SAMPLES + 1):
            out = HERE / "results" / f"{key}__s{s}.json"
            if out.exists():
                continue
            t0 = time.time()
            r = r1.generate(m["model"], prompt)
            out.write_text(json.dumps({"key": key, "sample": s, **m, "seconds": round(time.time() - t0, 1),
                                       "reflection": r.get("response", "")}, indent=1, ensure_ascii=False),
                           encoding="utf-8")
            print(key, s, f"{time.time() - t0:.0f}s")


def blind():
    rows = [r1.load(p) for p in sorted((HERE / "results").glob("*.json"))]
    random.seed(202610032)
    random.shuffle(rows)
    d = HERE / "blind"
    d.mkdir(exist_ok=True)
    key = {}
    for i, r in enumerate(rows, 1):
        bid = f"r{i:02d}"
        ledger = (HERE / "ledgers" / f"{r['voice']}.txt").read_text(encoding="utf-8")
        (d / f"{bid}.txt").write_text(
            f"voice: {r['voice']}\n\nPART ONE (ledger, mechanical):\n{ledger}\nPART TWO (reflection):\n{r['reflection']}\n",
            encoding="utf-8")
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
