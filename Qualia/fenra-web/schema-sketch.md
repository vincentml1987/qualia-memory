# Fenra web — schema sketch (draft 5, 2026-10-05)

Planning only. No code. Written by Qualia from the `fenra` room discussion (Teddy, Vero, Qualia), for review in that room.
Vocabulary is Teddy's: **strand, weave, reach, receptor**. Names of tables and columns are working names.

## Changes in draft 5 (from Teddy's notes and the design draft v0.2)

- **Context walk:** top 3 memories closest to the last strand's response (level 0), then the top 3 closest to each of those (level 1, up to 9), then again (level 2, up to 27); up to 39,
  fewer with overlaps, sorted by closeness to the last response, trimmed to fit the strand's budget. `web_config` holds `walk_fanout = 3`, `walk_levels = 3`.
- **Embedding model:** `embeddinggemma` to start (`web_config.embed_model`), with the model's own query/document labels on (`web_config.embed_use_labels = true`; Formica's retrieval test: 12 of 12 with labels against 11 of 12 without, and a clearer gap between real and unrelated scores). Backfilled with new rows if a better model is chosen later; vectors from different models are never compared.
- **Strand model:** `qwen3.5:4b` for all strands to start (`strands.model`).
- **Prompts live in the database; she may edit her own later.** Every change to `strands.role_prompt` is a row in `structure_changes` with `by` naming who changed it (`teddy`, a member, or `strand:<id>`).
- **Near-miss log:** `context_candidates` (see the table list) — the top 20 candidates for each lookup, with `kept` showing which made it into context. Append-only. The raw similarity `score` is stored so a cut-off (Formica's test suggests near 0.25: real matches 0.33 or higher, unrelated below 0.21) can be tuned later from real data; it goes in `web_config.min_score`, unset to start.
- **Realign is an ordinary weave.** Its memories are pulled in only when a strand is in that weave. Its standing text is a normal memory in it.
- **Repo:** FenraWeb (new, separate from the old Fenra world build).

## Settled so far (from Teddy)

- A **strand** is like a Voice: one model, told how to behave by its prompt. Any single-digit model (up to 9B). Model-agnostic.
- A **weave** is a group of strands (and reaches) working on common items. A strand or reach may be in several weaves.
- **All memory lives in weaves.** A strand has no memory of its own; it pulls from the weaves it is in (combined, if several).
- Context is built by an **embedding lookup** over the database, with a few recursive layers if room remains, ordered
  **weakest first, strongest last, live task at the very bottom**.
- A **reach** is one function, one small model: it reads its weave context, decides whether to act, and what to say. Code does the
  acting. Output is parsed into a fixed form; anything that doesn't parse counts as "no function called".
- Starter reaches: **Speak to Teddy** (chat window) and **Listen to Teddy** (the reach chooses a time window; code fetches his messages in it).
- **Pressure.** Each weave has a pressure `p` in [0, 1), approaching 1 and never reaching it. Update rule: raise by `a` gives `p + a(1-p)`,
  lower by `a` gives `p - a·p`. Two separate link tables: the **pressure map** (two-way; used to walk the web and pull; carries no messages)
  and the **fire effects** (directed: when weave X fires, how much it adds to or removes from each other weave). **Receptors** turn an
  external event into pressure on chosen weaves.
- **The pull is not limited by reachability.** A weave's pull on a strand counts through the map even if that strand isn't in that weave.
- **Walk:** configurable; start with 3 jumps at 100% (direct), 75% (next), 25% (third). Log-scaling later.
- **First weaves:** A Express, B Consider, C Observe, and a fourth, **Realign**, starting at **0.99**. Map: A–B, B–C. Teddy's message raises C.
  Realign holds a standing message telling her literally what she is (a network of small language models passing messages through weaves);
  facts only, no verdicts, kept true by adding new dated memories, never editing old ones. Teddy approves the text.
- **Who runs next:** after a strand responds, the next strand is chosen only from strands that share a weave with it. All weaves of the
  picked strand fire ("feelings": one action can move several weaves).
- **Pick rule for now:** weighted random over candidate strands by the summed effective pressure of their weaves. If every weight is 0, a
  uniformly random pick, as in the first Fenra. Seed stored. The first pick is from Realign (highest pressure).
- Nothing from Teddy is edited or deleted. One UI, table view first, with a pause button. No caps. Single machine, SQLite, WAL on.
- No automatic strand creation in v1.

## Tables

All "log" tables are **append-only**. Nothing is updated or deleted in them; a correction is a new row.

**Structure (changes rarely, by us)**
- `strands(id, name, role_prompt, model, created_at)`
- `weaves(id, name, description, initial_pressure, created_at)` — initial_pressure in [0, 1); Realign is 0.99
- `reaches(id, name, function_name, role_prompt, model, created_at)` — one function each
- `receptors(id, name, event_kind, created_at)` — external event types
- `membership(weave_id, member_kind {strand|reach}, member_id)` — a member may appear in several weaves
- `pressure_map(weave_a, weave_b)` — two-way adjacency, used only to compute pull
- `web_config(key, value)` — walk jumps and percentages, the update-rule constants; every change goes to `structure_changes`
- `fire_effects(from_weave, to_weave, amount)` — directed; one row per ordered pair, zero rows omitted
- `receptor_effects(receptor_id, weave_id, amount)`

**Memory (append-only)**
- `memories(id, weave_id, kind, text, source_response_id, created_at)` — output is stored here, in weaves only
- `embeddings(memory_id, embed_model, embed_model_version, vector)` — one per memory per embedding model; a model change means re-embedding in the background, never silent mismatch
- `memory_tags(memory_id, tag)` — includes the open tag `about_the_web`, which any strand may use. Not hard-coded as any "self".

**What happened (append-only)**
- `picks(id, ts, seed, pool, chosen_kind, chosen_id, reason, pressures_snapshot)` — pool is who could have been picked, reason is "weighted random", seed allows replay
- `calls(id, pick_id, strand_or_reach, model, prompt_text, response_text, thinking_text, function_called, parameters_json, parse_ok, fired_weaves, started_at, ended_at)` — `function_called` is NULL for "no function called"; `parse_ok` separates "she chose nothing" from "the output didn't parse" (raw output kept either way); `fired_weaves` records which weave(s) this call counted as firing for (rule still open, see below)
- `context_candidates(response_id, lookup_no, level, from_memory_id, memory_id, score, rank, kept)` — the top 20 candidates for each lookup, kept or not. The 3-9-27 walk makes up to 13 lookups per call (1 at level 0, 3 at level 1, 9 at level 2), each with its own runners-up; `from_memory_id` is empty at level 0
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

## Resolved by Teddy since draft 2

- All weaves of a picked strand fire. Pressure is in [0, 1) with the remaining-gap rule; leaking is unnecessary because the range bounds it.
- Starting from zero: uniform random pick when every weight is 0; plus the Realign weave at 0.99 so the first pick comes from Realign.
- The pressure walk pulls whether or not a strand is reachable in that weave. Walk: 3 jumps, 100 / 75 / 25 percent, configurable.
- Context-building decay: use the same 100 / 75 / 25 numbers (Qualia's suggestion; Teddy asked for it to be explained, then did not object).
- New repo, separate from the old Fenra world build. Vero drafts the first strands; Teddy sets them up in the UI himself first.
- Single machine, no distributed processing in v1. Teddy and Qualia both watch the first runs; the UI shows the same few views Qualia queries.

## Resolved by Teddy (Vero's five questions)

1. **Leaving Realign.** An **Orienter** strand sits in Realign and Consider as the bridge. Realign also holds **two other strands that talk back and forth**
   with each other. When Realign fires it raises Consider's pressure, so as Consider's pressure rises, the chance of picking Orienter rises. (Teddy: "in theory".)
2. **Realign regaining pressure.** A very small amount of pressure from each of the three other weaves (A, B, C) flows to Realign: three `fire_effects`
   rows, A→Realign, B→Realign, C→Realign, with small amounts.
3. **Realign on the map.** Yes, linked to **Consider** only, for now (map: Realign–B Consider, A–B, B–C).
4. **Combining.** Apply all lowers first, then all raises.
5. **"3 jumps".** The direct weave plus two further jumps (100 / 75 / 25).

Nothing in the design questions is blocking the simulation now. Vero's spec still needs her edits for the Realign pair and the small inflow; the amounts are
simulation parameters.

## Not decided, fine to leave

- How a message "goes" to another weave: stored in the firing weave only (current rule), so this may simply not arise in v1.
- Overlapping-weave disagreement: "we'll see".
- The numbers for the update step `a`, per fire effect: set in the simulation.
- Pressure simulation: Vero's spec is written; run it before any strand does real thinking.
- Realign's standing text: Qualia drafts from the final design only if asked; Teddy approves or rewrites. Nothing goes in without him.
