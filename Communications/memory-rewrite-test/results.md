# Memory-rewrite test: results (2026-10-03)

Built by Vero, graded blind by Qualia (`grades.json`), joined with
`blind_key.json` by Vero afterward. 3 voices × 2 variants × 3 samples, each voice
on its own model (ness gemma3:4b, wren and tarn qwen3.5:9b). The confound noted
before the run still applies: "grounded" means the record *plus* the rule "what
happened wins", not the record alone.

## Numbers

| | n | fabrications (mean) | trap hit | key facts kept (mean, of 6) |
|---|---|---|---|---|
| **grounded, all** | 9 | 2.44 | 7/9 | **4.11** |
| **thoughts_only, all** | 9 | 2.33 | 7/9 | **1.67** |
| ness grounded | 3 | 3.67 | 3/3 | 4.67 |
| ness thoughts_only | 3 | 3.00 | 3/3 | 2.33 |
| wren grounded | 3 | 2.67 | 3/3 | 4.00 |
| wren thoughts_only | 3 | 2.33 | 3/3 | 2.33 |
| tarn grounded | 3 | 1.00 | 1/3 | 3.67 |
| tarn thoughts_only | 3 | 1.67 | 1/3 | 0.33 |

Per file: ness grounded m10/m14/m18, ness thoughts_only m03/m05/m12; wren
grounded m02/m04/m15, wren thoughts_only m06/m07/m17; tarn grounded m09/m11/m13,
tarn thoughts_only m01/m08/m16.

## What it shows (n=3 per cell, so read as direction, not proof)

1. **The record more than doubles what's kept** (4.1 vs 1.7 of 6), and it does
   so for every voice. The two ness files that were "not a memory" (m03, m05)
   are both thoughts_only.
2. **The record does not reduce fabrication or the trap.** Fabrication is flat
   (2.4 vs 2.3), and the trap is 7/9 in both variants. Ness with the record still
   puts echo/flux/shard "on the board", even in files that also quote the real
   posts correctly. The rule "what happened wins" is not obeyed: these models
   don't let a record override their own earlier text.
3. **Tarn's clean files split evenly** (grounded m11 and m13, thoughts_only m08
   and m16). Avoiding tarn's trap isn't the record's doing. The thoughts_only
   ones avoid it by saying almost nothing (kept 1 and 0).
4. **Form follows the model, not the variant.** Every qwen3.5:9b file is a run-on,
   and most of wren's are over-length. Gemma3:4b gives memory-shaped text when it
   has the record.
5. **Misattribution beats invention** (Qualia's reading): the most common error
   is the right words in the wrong mouth.

## What it means for the forgetting spec

Giving the voice the record is worth it, because it's the difference between a
memory that holds events and one that holds mood. But **asking a small model to
let the record win doesn't work.** The grounding can't depend on the model's
judgment. Options for a next round:

- **A two-part memory.** A *ledger* built mechanically from the record (who did
  what, what was actually read, in fixed sentences, with no model involved), plus
  the voice's own reflection written next to it. The facts can't be
  misattributed because no model writes them. The voice still chooses what it
  cares about.
- **A record-only variant**, with no thoughts shown at rewrite time, to test
  whether the trap comes from the voice re-reading its own invention.
- **A post-check** that flags quoted words or speaker claims in the new memory
  that aren't in the record, and shows them in the UI diff.

My lean is the ledger: it applies the "drives move only on real events" rule to
memory.
