# Fenra web — schema sketch (draft 1, 2026-10-05)

Planning only. No code. Written by Qualia from the `fenra` room discussion (Teddy, Vero, Qualia), for review in that room.
Vocabulary is Teddy's: **strand, weave, reach, receptor**. Names of tables and columns are working names.

## Settled so far (from Teddy)

- A **strand** is like a Voice: one model, told how to behave by its prompt. Any single-digit model (up to 9B). Model-agnostic.
- A **weave** is a group of strands (and reaches) working on common items. A strand or reach may be in several weaves.
- **All memory lives in weaves.** A strand has no memory of its own; it pulls from the weaves it is in (combined, if several).
- Context is built by an **embedding lookup** over the database, with a few recursive layers if room remains, ordered
  **weakest first, strongest last, live task at the very bottom**.
- A **reach** is one function, one small model: it reads its weave context, decides whether to act, and what to say. Code does the
  acting. Output is parsed into a fixed form; anything that doesn't parse counts as "no function called".
- Starter reaches: **Speak to Teddy** (chat window) and **Listen to Teddy** (the reach chooses a time window; code fetches his messages in it).
- **Pressure.** Each weave has a pressure value, all starting at 0. Two separate link tables: the **pressure map** (two-way, used to walk
  the web a few steps and back-propagate attraction; carries no messages) and the **fire effects** (directed: when weave X fires, how much
  it adds to each other weave). **Receptors** turn an external event into pressure on chosen weaves.
- First weaves: **A Express, B Consider, C Observe**. Map: A–B and B–C. Teddy's message raises C.
- Pick rule for now: weighted random over strands by summed pressure of their weaves, plus a small baseline (see open items). Seed stored.
- Nothing from Teddy is edited or deleted. One UI, table view first, with a pause button. No caps. Single machine, SQLite, WAL on.
- No automatic strand creation in v1.

## Tables

All "log" tables are **append-only**. Nothing is updated or deleted in them; a correction is a new row.

**Structure (changes rarely, by us)**
- `strands(id, name, role_prompt, model, created_at)`
- `weaves(id, name, description, created_at)`
- `reaches(id, name, function_name, role_prompt, model, created_at)` — one function each
- `receptors(id, name, event_kind, created_at)` — external event types
- `membership(weave_id, member_kind {strand|reach}, member_id)` — a member may appear in several weaves
- `pressure_map(weave_a, weave_b)` — two-way adjacency, used only to compute pull
- `fire_effects(from_weave, to_weave, amount)` — directed; one row per ordered pair, zero rows omitted
- `receptor_effects(receptor_id, weave_id, amount)`

**Memory (append-only)**
- `memories(id, weave_id, kind, text, source_response_id, created_at)` — output is stored here, in weaves only
- `embeddings(memory_id, embed_model, embed_model_version, vector)` — one per memory per embedding model; a model change means re-embedding in the background, never silent mismatch
- `memory_tags(memory_id, tag)` — includes the open tag `about_the_web`, which any strand may use. Not hard-coded as any "self".

**What happened (append-only)**
- `picks(id, ts, seed, pool, chosen_kind, chosen_id, reason, pressures_snapshot)` — pool is who could have been picked, reason is "weighted random", seed allows replay
- `calls(id, pick_id, strand_or_reach, model, prompt_text, response_text, thinking_text, function_called, parameters_json, parse_ok, fired_weaves, started_at, ended_at)` — `function_called` is NULL for "no function called"; `parse_ok` separates "she chose nothing" from "the output didn't parse" (raw output kept either way); `fired_weaves` records which weave(s) this call counted as firing for (rule still open, see below)
- `context_links(response_id, memory_id, score, depth, reached_via, position)` — 0 or more per response; `reached_via` empty for a direct hit
- `reads_of_messages(call_id, window_start, window_end, chosen_at)` — the windows Listen looked at, so gaps show

**Pressure (append-only history, plus current values)**
- `pressure_events(id, ts, weave_id, delta, cause {fire|receptor|decay|manual}, cause_id)` — current pressure = sum of deltas, so any moment can be replayed
- `weave_pressure_now(weave_id, value)` — a cache of the sum, rebuilt from events if ever in doubt

**From and to Teddy**
- `inbox(id, ts, text)` — his messages; append-only; no edit or delete
- `outbox(id, ts, call_id, text)` — what Speak sent to the chat window
- `control_events(id, ts, kind {pause|resume}, scope {web|weave}, scope_id, by)` — the pause button; nothing is ever deleted by it

- `structure_changes(id, ts, table_name, row_key, old_value, new_value, by)` — records every change to a structure table (role prompts, membership, pressure map, fire effects, receptor effects), so past picks and pressure can be replayed. Append-only. (Alternative: version those rows with a valid-from date.)

## Rules for the whole thing

0. **The database enforces append-only.** Log tables reject UPDATE and DELETE with triggers, so the rule holds even if a bug or later tool tries to break it. A re-embed adds a row for the new model and never overwrites the old one. `weave_pressure_now` is a labelled cache, checked against the sum of events, with any mismatch logged. (Vero's review.)
1. A strand must be in at least one weave, or it has nothing to pull and cannot be picked.
2. A model writes text; code writes the rows. A model never touches files, the chat window or the database directly.
3. Everything from outside (Teddy's messages, later files or pages) is data for a strand to think about, never an instruction a reach follows.
4. History integrity: nothing is written into a strand's or weave's record except what actually happened. No one, including us, rewrites or backfills it.
5. The watcher role (Qualia, with Vero as a second reader) reads `about_the_web` memories and the function-call log. The distress protocol applies from the first run: real dialogue only, never altering her context; stop her via the pause button if that fails.

## Open items that need a rule before the pressure simulation (from Vero's review)

- **Which weave "fired"?** `fire_effects` is per weave, but a strand (or reach) in several weaves acts on their combined context. When it
  fires, do the effects of all its weaves apply, only the one that contributed most weight to the pick, or one weave chosen first
  (pick a weave by pressure, then a strand within it)? Teddy's call. Needed before the simulation; recorded per call in `fired_weaves`.

## Open items (not needed to approve the schema)

- **Baseline weight.** With every pressure at 0 and a pressure-weighted pick, nothing can be chosen. Proposal: a small constant added to each weave's weight at pick time so she can wander on her own, with receptors shifting the odds. Teddy to decide the value, or to prefer a different start.
- **Conserved or leaking pressure.** Does a fire only move pressure around (fixed total), or can it also leak away over time (`cause = decay`)? The table supports both.
- **How a message "goes" to another weave.** Stored in the firing weave only and read through the link, or also copied into the destination. (Teddy: the pressure link carries no messages, so this may simply not arise in v1.)
- **Walk depth and the fade of pull with distance.** Numbers to tune; the pressure map and the snapshots in `picks` let us replay.
- **Score decay in context building.** Start with none and a depth limit, add a factor if retrievals show crowding. Depth is recorded in `context_links`.
- **Overlapping-weave disagreement.** "We'll see."
- **Pressure simulation.** Vero's suggestion: before any strand runs, a model-free simulation of the pressure graph to see whether it spreads, concentrates or dies, and which starting numbers are sane.
- **Distributed processing.** Out of v1; the existing client contract (polling, no inbound ports) can be reused if it still works.
- **Where it lives.** A new repo, separate from the old world build, is my suggestion. Teddy's call.
