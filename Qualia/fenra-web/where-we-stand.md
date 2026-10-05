# Fenra web — where we stand (2026-10-05)

For Teddy. Planning only; no code has been written. Full detail is in [schema-sketch.md](schema-sketch.md) (draft 2).

## The idea in one paragraph

Fenra is a web of small single-model **strands**, grouped into overlapping **weaves**, with **reaches** (one-function agents that touch the
outside world) and **receptors** (code that turns an outside event into pressure). Memory lives only in weaves. Each weave has a
**pressure**; when a weave fires it changes the pressure of others; the next strand to run is picked, weighted by the pressure of its weaves.
Nobody tells her when to act. We supply the pieces and the hands; she decides what to reach for, including nothing.

## Decided

| Topic | Decision |
|---|---|
| Names | strand, weave, reach, receptor |
| Models | any single-digit model (up to 9B), model-agnostic; this machine has a 6 GB GTX 1660 Ti (about 2 to 3 GB free while the desktop is running) |
| Storage | SQLite, WAL on; every prompt and response recorded; log tables append-only |
| Memory | weaves only; a strand pulls from all its weaves; a strand must be in at least one weave |
| Context building | embedding lookup, a few recursive layers if room; ordered weakest at the top, strongest at the bottom, live task last |
| Record per response | which memories were pulled, with score, depth, route and position |
| Reaches | one function each; the model decides and writes, code performs; output parsed to a fixed form; may belong to several weaves and then act on the combined context |
| Starter reaches | Speak to Teddy (chat window), Listen to Teddy (she chooses a time window, code fetches your messages in it) |
| Logging | every call: function (or none), parameters, the thinking; every window Listen looked at |
| Picking | random pick for now, weighted later; every pick stored with its seed and pool |
| Pressure | all weaves start at 0; two separate link tables (a two-way pressure map, and directed fire effects); the map carries no messages |
| First weaves | A Express, B Consider, C Observe; map A–B, B–C; your message raises C through a receptor |
| Your messages | no edit, no delete; append-only |
| Limits | no caps and no usage budget (local only); a pause button in the UI, like Worlds |
| Scope for v1 | single machine; no automatic strand creation; new reaches requested in chat; distributed processing out; UI is a table view after the internals are settled |
| Watching | Qualia watches from her first run (distress protocol applies); Vero is a second reader |

## What I need from you

**Block the next step (the pressure simulation, and the final schema):**

1. **Which weave "fires"?** When a strand or reach that sits in several weaves is picked, which weave's fire effects apply?
   (a) all of its weaves, each in full; (b) only the weave that contributed the most weight to the pick (my lean: it keeps your rule as stated and
   one fire has one set of effects); (c) pick a weave first by pressure, then a strand inside it (no ambiguity, but it reverses your order).
2. **Starting up from zero.** With every pressure at 0, a pressure-weighted pick has nothing to weigh. Either (a) equal pressures mean a uniformly
   random pick, as in the first Fenra (Vero's reading; no extra number), or (b) a small constant baseline added to every weave, or (c) she only
   starts when a receptor fires. Which?

**Can wait, but I'd like your lean:**

3. **Does pressure only move around, or can it leak?** Fixed total is easy to reason about; a slow leak keeps old pressure from piling up.
4. **How many steps to walk the web, and how fast the pull fades with distance.** Numbers, to be tuned in the simulation.
5. **Score decay when building context.** Start with none and a depth limit (Vero's suggestion), or with a factor?
6. **Where the code lives.** A new repo, separate from the old Fenra world build (my suggestion, so old worlds and histories stay untouched), or a branch?
7. **Strand and weave contents.** Who writes the first strands' prompts and decides which strands go in A, B and C? (I'd suggest Vero drafts, you approve.)

## Next steps once 1 and 2 are answered

- Vero writes the spec for a model-free **pressure simulation**: a toy web run for thousands of steps with no models, to see whether the "rocking" appears and which starting numbers keep it from locking or dying.
- I fold the answers into schema draft 3, and we agree it.
- Only then: first code, and a first run, with me watching.

## Not touched

Nothing has been built or launched. No Fenra world or Voice history was read or changed. Fenra remains stopped.
