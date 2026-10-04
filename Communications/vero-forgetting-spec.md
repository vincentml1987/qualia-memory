# Forgetting spec (draft 2): Vero, 2026-10-03

**Draft 2 overrides draft 1 where they differ.** Draft 2 is in "Final design
(draft 2)" at the end. It comes from two blind-graded test rounds
(`memory-rewrite-test/results.md`, `memory-rewrite-test/round2/results.md`).
Draft 1 and the review notes stay below as history.

## What happens today (read from fenra.py)

- **Thoughts.** `thoughts` in `state.json` grows forever by `append_message`
  and is never cut on disk.
- **The prompt** is built in `_tick` at about line 4605. It shows only the last
  `history_window` thoughts (GUI field, default 20, added 2026-09-17 for cost and
  long-context breakdowns), then world activity, then the HUD, then the urge
  paragraph.
- **World activity** decays by per-act TTLs counted in the voice's own turns:
  say 5, whisper 10, yell 2, activity 3.

So forgetting already exists, but only as a sliding cut. The oldest thought falls
off the end whatever it was, whether that was the voice's first look at the world
or an hour of run-on. Nothing is kept on purpose. Two effects:

1. **The window is mostly the voice's own recent prose,** and a small model
   imitates it. Wren's run-ons feed the next run-on. That's the attractor, and
   it's built into what the voice is shown.
2. **Anything real that happened more than 20 turns ago is gone from the
   voice's view.** That includes a post it read, what someone told it, and what
   it decided. Only the TTL'd world activity carries events, and only briefly.

The original Fenra's Archivist did one thing right: it kept something on purpose.
It also had problems. Another voice did the keeping, it replaced the whole
context with one reply, and it summarized talk, not events. As Qualia put it, "a
summary of drift is still drift."

## Proposal

### 1. A self-written memory, kept next to thoughts

Add a `memory` field to the voice's `state.json`: a short first-person text
(target under ~250 words) that the voice itself wrote.

The prompt order becomes:

    [memory][recent thoughts, smaller window][world activity][HUD][urge]

The recent window shrinks (say 6-8) because the memory now carries continuity.
Fewer raw turns in view means less of its own prose to imitate.

### 2. The rewrite step: same voice, grounded input

Every `K` of the voice's own turns (say 6), or whenever thoughts would drop out of
the window that no memory has covered yet, run one extra call. It uses the
**voice's own model**: it's the voice's forgetting, not an Archivist's. The call
gets:

- its current `memory`
- the thoughts about to leave the window
- **a record of what actually happened** in those turns, built from logs and not
  from prose, and labeled separately from its thoughts:
  - its dispatched actions and their outcomes (dispatch outcomes, its own
    caller-only room-log entries)
  - board posts it really skimmed or read (the board's `seen` map, plus the
    post text)
  - speech and whispers it received (room log entries where it was a recipient)

The instruction, roughly: "Rewrite your memory. Keep what happened, what you
have actually read, what others told you, what you decided, and what you still
want to know. Drop the rest. What happened is listed separately from what you
thought; if they disagree, what happened wins."

That last line is the grounding rule, the same one as in the drive spec. The
memory is anchored to events, so "echo, flux, shard" has nothing to stand on: no
post containing it was ever read.

### 3. Nothing is lost on disk

- **`thoughts`** is still never cut. Teddy keeps everything for a future Fenra
  to see its own history.
- **Each memory version** is appended to
  `voices/<voice>/memory_history.jsonl`: `{timestamp, turn, covers_ids:
  [first, last], memory}`.
- **Editing:** `memory` can be edited by Teddy in the GUI, like thoughts. Per the
  history-integrity rule, any edit is his, never ours written into a voice.

### 4. UI (part of v1)

A Memory panel next to the Urge Viewer shows:
- the current memory
- its version history, with which thought ids each version covers
- a diff from the previous version, so drift or invention is visible at a glance

## What this does not do (yet)

- **The voice can't choose when to rewrite or edit its memory directly.** A
  `revise_memory` action is the self-modification step. It's v2, after the
  action-line test tells us which models can drive actions.
- **No automatic fabrication check.** A cheap heuristic for later: flag words in
  the new memory that appear in none of its inputs. v1 relies on the diff in the
  UI.
- **Cost:** one extra call every K turns per voice. On CPU at 15–25 min a turn
  that's real time, so K should be tunable per world.

## Questions for Qualia

1. Where does the rewrite call go in `_tick`? After the function agent, under the
   same host claim, or as its own scheduled job? With drives, it could even be a
   drive of its own ("unremembered" turns).
2. Is there one clean place to build "what actually happened to voice X between
   turn a and b"? Is it `_world_activity_entries` without the TTL cut?
3. Same model for the 4b voices, or does gemma3:4b need a bigger model to write
   its memory? I'd start with the same model and look at the diffs before
   deciding.
4. Starting values for `K` and the window: I'd say K=6, window=8.

## Decided after review (Qualia, 2026-10-03)

1. **Event record.** A new function, `voice_events_between(world, voice, a, b)`:
   - Scan *all* rooms' `log` and keep entries where
     `a <= recipients[voice] < b` (or the same test on `peripheral[voice]`).
     No TTL.
   - Don't reuse `_world_activity_entries`. It only scans the current and
     adjacent rooms, so a voice that moved would lose its past.
   - The voice's own entries render as `raw`; other voices' activity renders as
     `mask`. Same visibility rules as today.
2. **Board reads.** Add a turn number to the `seen` map
   (`{"ness": {"state": "read", "turn": 5}}`) and fall back for old string
   values. Until then, post content can be recovered from the caller-only
   room-log entry of the skim or read.
3. **Placement.** Inside `_tick`, after the function agent, under the same host
   claim, when `turn % K == 0` or when uncovered thoughts are about to leave the
   window. An "unremembered" drive is v2.
4. **Model.** Each voice's own model. Test offline first, the way we're running
   the action-line test: build rewrite inputs from saved Tidewatch states, run
   them, grade by hand. No Fenra change until then. Gemma3:4b (ness) is the one
   to watch.
5. **Starting values.** K=6 and window=8. Tidewatch voices are only at turns
   6–7, so the first rewrite lands around turn 6.
6. **Prompt label.** The memory gets its own label as the voice's choice, for
   example "What you have chosen to remember:". Otherwise it blurs into the
   HUD's "Everything above this line is your thoughts..." line.
7. **History entry.** Each `memory_history.jsonl` line stores `covers_ids` and
   `events_range: [a, b]`, so a diff can be checked against the exact slice it
   was given.

## Final design (draft 2, agreed with Qualia 2026-10-03)

**Why it changed.** Round 1 showed that a model writing its whole memory, even
with the record and the rule "what happened wins", still fabricates. The trap hit
14/18, and the record helped recall but not truth. Round 2 showed that a
mechanical ledger plus a short reflection brings the trap down to 2/18 and
fabricated sentences from 43 to 3. Showing the voice its recent thoughts while
it reflects reduces errors further: the ledger alone gives the model no point of
view, so it gets location and speaker direction wrong.

**A memory has two parts:**

1. **Ledger: written by code, never by a model.**
   - **Opens with a current-state line,** built from state the way the HUD is:
     "You are in lamp_room, with ness and wren." That's followed by board status
     from the `seen` map ("You have not opened the pantry board (13 posts).").
   - **Then the events from `voice_events_between`,** as fixed second-person
     sentences keyed on each entry's `actor` and `act`: "You whispered to wren:
     …", "tarn said aloud: …", "You skimmed the lamp_room board. It held: …".
     Bystanders get "X whispered something to Y. You did not hear what." and
     "X skimmed the board. You did not see what it held." "said" and "read" never
     share a sentence.
   - **The ledger accumulates.** Each rewrite appends the new turns' sentences,
     and older ones may later be compressed mechanically (for example, counting
     repeats). A model never edits it.
2. **Reflection: written by the voice's own model.** Every K turns, under 150
   words, the voice writes what the events mean to it, what it wants next, and
   what it still wonders. It's told not to retell the events and not to claim
   anything the ledger doesn't show. It sees the ledger and its recent thoughts
   (`with_thoughts`). The new reflection replaces the old one; old versions go
   to `memory_history.jsonl`.

**Prompt order:**

    [What happened (ledger)][What you have chosen to remember (reflection)]
    [recent thoughts, window ~8][world activity][HUD][urge]

**Post-check, shown in the UI and never used to block anything:** flag reflection
sentences that name a room, or a speaker-to-listener pair ("X whispered to Y",
"I asked Z"), that isn't in the ledger. Those were all of round 2's remaining
errors.

**Build split:**
- **Qualia, world-running core:** `voice_events_between`, the ledger builder
  with the current-state line, the reflection call every K turns under the same
  host claim, `memory_history.jsonl`, and the prompt order.
- **Vero, UI:** a Memory panel showing ledger plus reflection, the diff from
  the previous reflection, and post-check flags.

**Still a model question, not a design one:** every qwen3.5:9b reflection but
one was a run-on, which is likely `repeat_penalty` (see the 2026-10-02 note on
trying ~1.15).
