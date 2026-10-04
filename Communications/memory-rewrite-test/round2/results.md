# Round 2 results: ledger + reflection (2026-10-03)

Built by Vero, graded blind by Qualia (`grades.json`), joined with
`blind_key.json` by Vero afterward. 3 voices × 2 variants × 3 samples, each voice
on its own model.

## Compared with round 1

| | Trap hit | Files contradicting the record | Fabricated sentences |
|---|---|---|---|
| Round 1 (model writes the whole memory) | 14/18 | not measured | 43 total |
| Round 2 (mechanical ledger + reflection) | **2/18** | 6/18, one sentence each | **3 total** |

Round 2's reflections never retold the events (0/18), and all of them added a
want, a question or a decision (18/18).

## By variant: against the guess

| | n | trap | contradicts (files) | fabrication (sentences) | run-on |
|---|---|---|---|---|---|
| ledger_only | 9 | **2** | **5** | 0 | 5 |
| with_thoughts | 9 | **0** | **1** | 3 | 6 |

We expected showing the voice its own thoughts to cause the trap. It was the
other way round:
- **ledger_only** produced both traps (r03 wren, r18 ness) and five of the six
  contradictions: tarn placing itself at the pantry door (r06, r12), and wren
  reversing who whispered to whom (r09).
- **with_thoughts** produced one contradiction (r11) and no traps, but all three
  fabrications. They were ness's "I ask again" style speech with no ledger line
  (r02, r08).

**Reading (n=3 per cell, direction only):** a ledger by itself is a list of
sentences with no point of view. Without its own thoughts, the model has to
reconstruct where it is and who is talking to whom, and that reconstruction is
exactly where it goes wrong: location and speaker direction. Its thoughts give it
a perspective to hang the ledger on. They cost a little invented speech, but far
less than round 1.

A concrete gap this exposed: **the ledger never states where the voice is now or
who is with it.** Tarn's location errors come straight from that. "You moved to
lamp_room" is in the list, but nothing says "You are in lamp_room now, with ness
and wren."

## Design decision this supports

1. **Memory = mechanical ledger + reflection written by the voice, with its
   recent thoughts shown** (with_thoughts).
2. **The ledger opens with a current-state line:** room, who's present, board
   status. It's built from state, like the HUD.
3. **A post-check for the UI** (Qualia's sharpening): flag reflection sentences
   that name a room, or a speaker-to-listener pair ("X whispered to Y", "I
   asked Z"), that the ledger doesn't contain. That covers every remaining error
   type seen in round 2.
4. **Form still follows the model** (every qwen3.5:9b reflection but one is a
   run-on). That's a model and `repeat_penalty` question, not a memory-design
   one.
