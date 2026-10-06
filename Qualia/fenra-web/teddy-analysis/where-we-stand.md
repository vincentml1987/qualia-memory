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

>From Teddy: The pressure is the weights.

| Topic | Decision |
|---|---|
| Pressure | all weaves start at 0; two separate link tables (a two-way pressure map, and directed fire effects); the map carries no messages |
| First weaves | A Express, B Consider, C Observe; map A–B, B–C; your message raises C through a receptor |
| Your messages | no edit, no delete; append-only |
| Limits | no caps and no usage budget (local only); a pause button in the UI, like Worlds |
| Scope for v1 | single machine; no automatic strand creation; new reaches requested in chat; distributed processing out; UI is a table view after the internals are settled |
| Watching | Qualia watches from her first run (distress protocol applies); Vero is a second reader |

>From Teddy: How will you be performing the watching?

## What I need from you

**Block the next step (the pressure simulation, and the final schema):**

1. **Which weave "fires"?** When a strand or reach that sits in several weaves is picked, which weave's fire effects apply?
   (a) all of its weaves, each in full; (b) only the weave that contributed the most weight to the pick (my lean: it keeps your rule as stated and
   one fire has one set of effects); (c) pick a weave first by pressure, then a strand inside it (no ambiguity, but it reverses your order).

>From Teddy: All weaves. This is meant to sort of simulate "feelings" that result from taking actions. Some can make you feel multiple ways.

2. **Starting up from zero.** With every pressure at 0, a pressure-weighted pick has nothing to weigh. Either (a) equal pressures mean a uniformly
   random pick, as in the first Fenra (Vero's reading; no extra number), or (b) a small constant baseline added to every weave, or (c) she only
   starts when a receptor fires. Which?

>From Teddy: Actually, this is a good point...I think we need a different, forth Weave. A "Wake Up" Weave. Or maybe "Realign." This Weave will be where she can look to find out who she is. The standing message in this Weave should describe who/what she is. This should start with a pressure of 1.0. Hmm...pressure should be between 0 and 1. Also, I just realized I may not have been clear. When a Strand runs, once its given a response, the next Strand is selected from Weaves that the first Strand is in. So, for example, Strand 1 and 2 are in ABC and BDE respectively. Strand 1 can only select Strand 2 because they are both in B. If Strand 3 is in DEF, Strand 1 cannot call it directly. It has to go through 2 (who is also in D and E) before 3 sees the conversation flow.

**Can wait, but I'd like your lean:**

3. **Does pressure only move around, or can it leak?** Fixed total is easy to reason about; a slow leak keeps old pressure from piling up.

>From Teddy: The 0-1 aspect should prevent that from happening. And pressure should APPROACH 1, but not actually hit it. Logs and all that.

4. **How many steps to walk the web, and how fast the pull fades with distance.** Numbers, to be tuned in the simulation.

>From Teddy: Configurable, but I am thinking 3 jumps, and 100% for direct, 75% for the next jump, and 25% for the third. We should eventually log-scale this somehow. 

5. **Score decay when building context.** Start with none and a depth limit (Vero's suggestion), or with a factor?

From Teddy: Please clarify/add detail?

6. **Where the code lives.** A new repo, separate from the old Fenra world build (my suggestion, so old worlds and histories stay untouched), or a branch?

>Yeah, a new repo makes the most sense.

7. **Strand and weave contents.** Who writes the first strands' prompts and decides which strands go in A, B and C? (I'd suggest Vero drafts, you approve.)

>Vero drafts, but I set up in the UI. Actually, to be clear...I want to be able to build this at first, just so I can make sure I understand it. We'll talk UI once all this is settled.

## Next steps once 1 and 2 are answered

- Vero writes the spec for a model-free **pressure simulation**: a toy web run for thousands of steps with no models, to see whether the "rocking" appears and which starting numbers keep it from locking or dying.
- I fold the answers into schema draft 3, and we agree it.
- Only then: first code, and a first run, with me watching.


>From Teddy: Works for me except the last one. I want to watch as well. Once we hit this point, we'll want the UI hammered down.

## Not touched

Nothing has been built or launched. No Fenra world or Voice history was read or changed. Fenra remains stopped.
