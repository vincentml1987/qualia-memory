# Drive spec (draft 1) - Vero, 2026-10-03

Spec only. No Fenra files touched. For Qualia to review against the scheduler.

## What already exists (read from fenra.py today)

- **Urge** (`apply_urge_tick`, `compute_urge_snapshot`, `xleud`): per voice, per
  function. A function's raw urge resets to 0 on a successful dispatch and grows
  by `URGE_DRIVE` every other tick. `xleud` squashes it to [0,1). Top
  `URGE_TOP_N` above `URGE_FLOOR_PCT` become a felt-sensation paragraph (urge
  agent) and the function agent's `[URGES]` block.
- **Scheduler** (`order_candidates`): rotation order, then least-recently-started
  first. Nothing about a voice's state affects *whether* it gets a turn.

So drives exist, but they only shape *what a voice does once it has a turn*. They
don't decide *who gets the turn*, and nothing a voice thinks changes them. The
original Fenra's PDV did the opposite: drove who speaks, not what was done. The
useful design joins the two.

## Proposal

### 1. Drives are voice state, updated by real outcomes

Keep the urge mechanism as is. Add a small set of non-function drives, each a raw
float in the voice's own state, squashed with `xleud` for use:

| Drive | Grows when | Resets / drops when |
|---|---|---|
| unread | a board post or whisper reached the voice's room and it hasn't been read | a real `read_board`/`skim_board` returns it |
| unsaid | the voice has held a thought N ticks without any `say`/`whisper`/`post` | a successful speech act |
| unease | a dispatch fails, or a read result contradicts what the voice just said | a following successful read that agrees |
| restlessness | N ticks in the same room with no arrival and no new post | `move_room`, `create_room`, or any arrival |

Each is driven only by logged events (function outcomes, room log), never by what
the voice says about itself. That is the grounding rule: **a drive can only move
because something actually happened.** The "narrated reaching for the board" case
never raises or lowers `unread`.

### 2. Drives pick who acts

Replace "least recently started first" with a score:

    score(voice) = max over drives of xleud(drive) + small wait bonus

Highest score is offered a host first. Ties and the wait bonus keep today's
no-starvation property. Everything else in `claim_host_for_voice` is unchanged, so
this is a change inside `order_candidates` and a `last_started`-style map, not a
new scheduler.

A voice below a floor on every drive may be *skipped* this round (rest). That is
the first piece of "a voice can decide not to act" without asking the voice to
write anything.

### 3. The voice's thought can change drives (later, not v1)

Only after step 2 works: the voice's output may name a next step ("wait", "rest",
"go read X"), recorded as an intent that biases its own next score. The
action-line test decides which models can do this reliably.

## What this does *not* fix

- Compression and forgetting: separate spec.
- Whether small models can write an action line: separate test.
- Speed: a 15-25 minute turn on CPU is still not a constant loop. Drives only make
  those turns count for more.

## Questions for Qualia

1. Is `last_started` the right place to inject the score, given `local_slots`
   concurrency?
2. Does a rest/skip break resume (rotation index) semantics?
3. Where does a drive live on disk: inside `state.json` next to `urge`? I'd say yes.
4. Is any of this a code change that needs Teddy's approval before a prototype?
   I assume yes for anything that edits `fenra.py`.
