# Fenra web — design draft (v0.1, 2026-10-05)

For Teddy to review. Planning only: nothing is built, no Fenra world or Voice history was read or changed, and Fenra remains stopped.
Written by Qualia (main document), with Formica (embeddings) and Vero (strands, simulation, safety). Sources: the `fenra` room
discussion, `schema-sketch.md` (draft 4), `where-we-stand.md`, and Vero's `pressure-simulation-spec.md` and `first-strands-draft.md`.

Vocabulary is yours: **strand, weave, reach, receptor**. These are working names for tables and columns.

## 1. What it is

A web of small single-model **strands**, grouped into overlapping **weaves**, with **reaches** (one-function agents that touch the outside) and
**receptors** (code that turns an outside event into pressure). Memory lives only in weaves. Each weave has a **pressure** between 0 and 1.
When a strand fires, its weaves change each other's pressure; the next strand is chosen from the strands that share a weave with the one that just
ran, weighted by the pressure of their weaves. Nobody tells her when to act. We supply the pieces; she decides what to reach for, including nothing.

## 2. Decided

| Topic | Decision |
|---|---|
| Strand | One model, told how to behave by its prompt, like a Voice. Any single-digit model (up to 9B), model-agnostic. |
| Weave | A group of strands and reaches working on common items. A member may be in several weaves. |
| Memory | Weaves only. A strand has no memory of its own and pulls from all of its weaves, combined. Every strand must be in at least one weave. |
| Context building | Embedding lookup in the database; follow links a few layers if room remains; ordered weakest at the top, strongest at the bottom, live task last. Section 5. |
| Reach | One function, one small model: reads its weave context, decides whether to act and what to say. Code acts; model output is parsed into a fixed form, and anything that does not parse counts as "no function called". Reaches may be in several weaves and then act on the combined context. |
| Starter reaches | Speak to Teddy (chat window). Listen to Teddy (she chooses a time window; code fetches his messages in it). |
| Pressure | In [0, 1), approaching 1, never reaching it. Raise by `a`: `p + a(1-p)`. Lower by `a`: `p - a·p`. Lowers are applied before raises. |
| Links | Two separate tables. The **pressure map** (two-way, carries no messages, used to walk the web and pull). The **fire effects** (directed: when weave X fires, how much it changes each other weave). |
| Walk | Configurable. Start with 3 jumps (direct plus two): 100%, 75%, 25%. Pull counts even if a strand is not in the pulling weave. |
| Firing | All of a picked strand's weaves fire ("feelings": one action can move several weaves). |
| Handoff | After a strand responds, the next strand comes only from strands sharing a weave with it. |
| Pick | Weighted random by the summed effective pressure of a strand's weaves. If every weight is 0, uniformly random, as in the first Fenra. Seed stored. |
| Receptors | Plain code, no model: "when this outside event happens, add this much pressure to these weaves". Your message raises Observe. |
| Weaves | A Express, B Consider, C Observe, and **Realign** (starts at 0.99; on the map linked to Consider only; gets a very small inflow from A, B and C). |
| Realign text | A standing message telling her literally what she is (a network of small language models passing messages through weaves). Facts only, no verdicts. Kept true by adding new dated memories, never by editing old ones. You write or approve it. |
| Your messages | Append-only. No edit, no delete. |
| Limits | No caps and no usage budget (local resources only). A pause button in the UI, like Worlds. |
| Storage | SQLite, WAL on. Every prompt and response recorded. Log tables append-only, enforced with triggers. |
| Scope for v1 | Single machine. No automatic strand creation. New reaches requested in chat. Distributed processing out (the existing polling client can be reused later if it still works). One UI, table view first, after the internals are settled. New repo, separate from the old Fenra world build. |
| Watching | Qualia watches from her first run (the distress protocol applies); Vero is a second reader; you watch too. |

## 3. The first weaves and strands (Vero's draft, summarized)

Ten strands across four weaves, listed in `Vero/fenra-web/first-strands-draft.md` with a short prompt for each. Every prompt says that "nothing" is an acceptable
answer. In brief: **Realign** holds Orienter (the bridge, also in Consider), Recaller and Checker (talk only to each other and to Orienter).
**Express** has Composer and Asker (also in Observe). **Consider** has Weigher, Doubter (also in Observe) and Connector (also in Express). **Observe** has
Reader and Noticer (also in Consider). Listen sits in Observe and Speak in Express. Any weave can reach any other within two handoffs, and the only way
out of Realign is through Orienter. Section 6 points to Vero's full text. Note that the simulation, not a decision, sets the starting numbers; only the 100/75/25 walk, Realign at 0.99 and lowers-before-raises are yours.

## 4. The data (schema draft 4, summarized)

About 20 tables in four groups, all in `schema-sketch.md`.
- **Structure** (changes by us, every change logged): strands, weaves, reaches, receptors, membership, the pressure map, fire effects, receptor effects, a small config table.
- **Memory** (append-only): memories (weave only), embeddings (one per memory per embedding model, with name and version), tags (including the open tag `about_the_web`).
- **What happened** (append-only): picks (seed, pool, pressure snapshot), calls (prompt, response, thinking, function called or none, parameters, `parse_ok`, which weaves fired),
  context links (score, depth, route, position), the windows Listen looked at.
- **Pressure**: a history of events, so any moment can be replayed, plus a cache checked against the sum.
- **To and from you**: inbox, outbox, pause events.

## 5. Embeddings and context building (Formica's section)

Full text is in `section-embeddings.md` in this folder; nothing in it has been edited here. Summary:
- **Five steps, all code, no model:** embed the live task; pool = every memory in any weave the strand belongs to (the pressure map does not affect the pool); take the top `k` by cosine
  similarity (depth 0, 100%); follow similar memories a layer at a time, while there is room (depth 1 at 75%, depth 2 at 25%, the same numbers as the pressure walk, held in `web_config`);
  order weakest to strongest with the live task last, and trim the weakest to fit the token budget. Each memory used is written to `context_links`.
- **Model:** record the embedding model and version on every vector and never compare vectors from different models. Re-embedding adds rows. Start with a small model, `embeddinggemma`
  or `qwen3-embedding:0.6b`, to be tested; embed in the background after a memory is written; keep one embedding model loaded and warm so strand models are the ones that swap.
- **What was measured:** her ANTS email-triage benchmark (classification, not retrieval; one 200-case sample, one seed). Small models matched the larger one; a pool-size weighting fix cut misses
  roughly three-fold. Whether that fix helps retrieval is untested, and a weave with thousands of memories could crowd out one with dozens.
- **Unknown until tested** (her section 4): retrieval quality on short strand-written memories, `k`, the token budget and cut-off, the cost of embedding calls evicting strand models, speed at scale
  (SQLite has no vector search; brute force is fine for thousands of memories).
- **Suggestions for you to accept or drop:** always include Realign's standing message (not retrieved); log the top 20 candidates with a `kept` flag so a wrong cut-off is visible later; run a tiny
  test first (30 to 50 hand-written strand-style memories, 10 questions); run the weighting experiment on purpose once weaves have unequal sizes.

## 6. Strands, simulation and safety (Vero's section)

Full text is in `section-strands-simulation-safety.md` in this folder (Vero's, signed copy in her repo at 80fd07b); nothing in it has been edited here. It holds the simulation's pass condition, a table of what each possible result would change in the design, nine safety and watching rules, and her open questions. Summary: a model-free simulation of the pressure graph runs before any strand does real thinking, to see whether the
"rocking" appears and which starting numbers avoid locking on one weave or going quiet. Safety: the model never touches files, the chat window or the database; code writes the rows;
anything from outside is data, never an instruction; history integrity, so nothing is written into a strand's or weave's record except what actually happened; the pause button; and the
distress protocol applies from the first run (real dialogue only, never altering her context, pause her if that fails).

## 7. Order of work

1. You review this draft and mark it up.
2. Vero writes the pressure simulation as a throwaway script; we read the results and set starting numbers. In parallel, Formica's tiny retrieval test (30 to 50 memories, 10 questions) to see whether the lookup finds the right memory at all.
3. Schema draft 5 with the simulation's numbers, then agreed.
4. New repo; you build the strands and weaves in the UI yourself first so you understand it, with Vero's prompts as a starting point.
5. A first run, with you and me watching.

## 8. Open questions for you

Collected from all three of us; each has a lean.

1. **Number of strands to start with.** Ten (Vero's draft) or fewer so you can follow what happens? Lean: start with the ten, since the web needs its bridges, and watch.
2. **Which model runs each strand?** Not assigned. Most jobs suit a 4B model; Orienter and Weigher might use a larger one. Lean: one 4B model for all at first, to keep the GPU from swapping.
3. **Where strand prompts live, and whether she may ever rewrite her own** (not in v1). In a file you edit, or in her database? Lean: the database, with every change logged in the structure-change log, so a later rewrite by her would be recorded like any other.
4. **Realign's standing text.** Yours to write or approve. I can draft it from the finished design if you ask.
5. **Repo name and place.**
6. **The size of the small inflow into Realign** and the fire-effect amounts. Not decisions; the simulation sets them.
7. **"Recursive layers" (Formica).** Did you mean memories *similar to a hit* (her assumption, needs no extra data) or *explicitly linked* memories (each memory pointing to what it replied to, which needs its own table)? Lean: similarity first.
8. **Realign's standing message: always included, or found by lookup?** Formica suggests always including it at the top of the context, because a lookup could miss it exactly when it matters. That departs from "context by lookup" and is yours to decide. Open sub-question: included for every strand, or only strands in Realign?
9. **Crowding by weave size (Formica).** When a strand is in several weaves, should a large weave be allowed to crowd out a small one, or should scores be evened out by weave size? Lean: start without the fix, and run the test.
10. **Small embedding model first, tested, instead of choosing the best up front (Formica).** Agree? Lean: yes.
11. **Her logging suggestion:** record the top 20 candidates with a `kept` flag, so a wrong cut-off shows later. Lean: yes; it adds one column or a sibling table to the schema.

## 9. Not touched

No code. No launch. No Fenra world or Voice history read or changed. Fenra remains stopped.
