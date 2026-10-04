"""Offline check of the function agent config before a relaunch (Vero's
suggestion, 2026-10-03). Replays tarn's real function-agent input from the
21:07 run (its last function_agent call in llm_calls.jsonl) through
fenra.call_function_agent, N times per config, and records seconds, whether
a tool call came back, and whether the output hit the num_predict cap.

Run only with Fenra stopped (one Ollama model slot).
Usage: python agent_bench.py [n=3]
"""
import contextlib
import io
import json
import os
import sys
import time

FENRA = r"C:\Users\Matt\Desktop\Aletheia\Code and Scripts\Fenra"
sys.path.insert(0, FENRA)
os.chdir(FENRA)
with contextlib.redirect_stdout(io.StringIO()):
    import fenra  # noqa: E402
import requests  # noqa: E402

HOST = "http://localhost:11434"
MODEL = "qwen3:30b"
CONFIGS = [
    {"name": "think_false_cap2048", "think": False, "num_predict": 2048},
    {"name": "think_false_nocap", "think": False, "num_predict": -1},
]

calls = [json.loads(l) for l in open("worlds/the_tidewatch/voices/tarn/llm_calls.jsonl", encoding="utf-8")]
case = [c for c in calls if c["kind"] == "function_agent"][-1]
system_text = case["prompt"]
tools = fenra.build_function_agent_tools()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
print(f"case from {case['timestamp']}; original dispatch: {case['extra'].get('tool_calls')}")

RUNS = {"think_false_cap2048": n, "think_false_nocap": 1}
for cfg in CONFIGS:
    for i in range(RUNS[cfg["name"]]):
        req = {"model": MODEL, "messages": [{"role": "system", "content": system_text}],
               "tools": tools, "stream": False, "think": cfg["think"],
               "options": {"num_predict": cfg["num_predict"], "repeat_penalty": 1.3}}
        t0 = time.time()
        r = requests.post(f"{HOST}/api/chat", json=req, timeout=None).json()
        secs = time.time() - t0
        msg = r.get("message", {})
        calls_out = [(c["function"]["name"], c["function"].get("arguments")) for c in msg.get("tool_calls") or []]
        print(json.dumps({"config": cfg["name"], "run": i + 1, "seconds": round(secs, 1),
                          "eval_tokens": r.get("eval_count"), "done_reason": r.get("done_reason"),
                          "hit_cap": r.get("done_reason") == "length",
                          "tool_calls": calls_out,
                          "think_tags_in_content": "</think>" in (msg.get("content") or ""),
                          "content_head": fenra.strip_think_tags(msg.get("content") or "")[:120]},
                         ensure_ascii=False), flush=True)
