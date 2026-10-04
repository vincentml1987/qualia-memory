"""Blind copies of action-line outputs for Vero's consistency/grounding pass.

Writes blind/bNNN.txt (case id and situation kept; model name and scores
removed; order shuffled across all models) and blind_key.json mapping each
file to its model. The key is Qualia's: Vero grades before opening it.

Usage: python make_blind.py results/*.jsonl
"""

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(paths):
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(p, encoding="utf-8")]
    random.Random(20261003).shuffle(rows)
    out = HERE / "blind"
    out.mkdir(exist_ok=True)
    key = {}
    for i, r in enumerate(rows, 1):
        name = f"b{i:03d}"
        (out / f"{name}.txt").write_text(
            f"case: {r['case']}\n\n{r['output'].strip()}\n", encoding="utf-8")
        key[name] = {"case": r["case"], "model": r["model"]}
    (HERE / "blind_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    print(f"{len(rows)} blind files in {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
