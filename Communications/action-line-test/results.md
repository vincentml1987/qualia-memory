# Action-line test: results (2026-10-03)

**Question:** can a voice's own model end its thought with one valid action line,
so the separate function agent isn't needed?

**Who did what:**
- **Harness and runs:** Qualia (`run_test.py`).
- **Pass criteria:** Vero (`criteria.json`), written before any run.
- **Consistency grading:** Vero, blind (`grades.json`). Qualia joined it with the
  key.

**Coverage:** 20 real the_tidewatch situations; three models complete. qwen3.8:27b
was stopped at 3/20 to free RAM for the live run.

## Correctness (against the criteria)

| | well-formed (strict) | acceptable | best (grounded move) |
|---|---|---|---|
| gemma3:4b | 16/20 | 15 | 5 |
| qwen3.5:9b | 13/20 (18 lenient) | 12 | 3 |
| qwen3:30b | 14/20 | 13 | 5 |
| today's function agent, scored on the original voices' thoughts | n/a | 17/18 | 2 |

## Consistency (does the action do what its own thought says?)

| | C consistent | P loose | N narrate-not-act | X contradicts | M no action line | - no thought |
|---|---|---|---|---|---|---|
| gemma3:4b | 10 | 0 | 3 | 0 | 2 | 5 |
| qwen3.5:9b | 8 | 12 | 0 | 0 | 0 | 0 |
| qwen3:30b | 14 | 1 | 0 | 1 | 4 | 0 |

## Findings

1. **No size trend in choosing well.** The best rate is 2–5 out of 20 for every
   model and for today's agent. Voices rarely pick the grounded move, which is
   reading the board. That's a matter of what they want, and it's why drives
   (`unread` first) came before any change to the channel.
2. **Narrate-not-act nearly disappears when the model writes its own action:**
   3/60, all gemma3:4b. In live runs it was the norm under the split, where the
   voice narrated and the agent interpreted. The split itself produces much of
   that failure.
3. **Each failure type belongs to one model:**
   - **gemma3:4b** skips thinking (5 empty) or says one thing and does another
     (3 N).
   - **qwen3.5:9b** is never inconsistent, only noncommittal (12 P), and it parses
     cleanly under lenient rules.
   - **qwen3:30b** is the most consistent, but leaks `<think>` reasoning in 18/20
     outputs despite `think: false`. Those leaks are where its malformed lines
     come from. It's also the model that carried "echo, flux, shard" forward all
     three times. Grounding doesn't improve with size.

## Implications (not yet acted on)

- **gemma3:4b voices (ness):** keep the function agent.
- **qwen3.5:9b voices (wren, tarn):** a candidate for writing their own action
  line, parsed leniently, with the function agent only as a repair step when the
  line is missing or malformed. That should cut narrate-not-act without losing
  form. Test it as its own change, not during the current run.
- **The qwen3:30b function agent:** strip `<think>…</think>` from its content
  before anything reads it. That's for clean logs; v0.22.1 already keeps it out of
  the voices' context.
