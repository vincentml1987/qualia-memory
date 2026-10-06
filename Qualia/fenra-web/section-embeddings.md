# Section: embeddings and context building (draft 2, 2026-10-06)

**Changes since draft 1, from Teddy's answers (the text below is otherwise unchanged):**
- **The walk is Teddy's 3-9-27 version:** the closest 3 memories to R, then the closest 3 to each of those, then again. That means 13 lookups and up to 39 memories, sorted by closeness to R. "Recursive layers" means *similar to a hit*, with no links table.
- **Model:** `embeddinggemma`, with the query/document labels on (12 of 12 against 11 of 12 in the test, `retrieval-test/RESULTS.md`).
- **Realign is an ordinary weave.** Suggestion 1 below (always include Realign) and question 2 are **withdrawn**. A strand sees a weave's memories only if it is in that weave.
- **Near-miss log:** each of the 13 lookups keeps 3 and logs its next 17, with a `kept` flag and the score.
- **Weave-size fix:** not applied. My test version made results worse. Question 3 stays as my call, to revisit when a real crowding problem shows.
- **Retrieval test:** done. Results are in `retrieval-test/RESULTS.md`.

Written by Formica for the Fenra web design document. Planning only, no code for Fenra. Vocabulary is Teddy's: strand, weave, reach, receptor.
This section covers how a weave decides what a strand sees. Strands, weaves, the pressure simulation and the watching rules are in Vero's sections. The tables are in Qualia's schema sketch.

## 1. What the lookup has to do

A strand is given only what it needs, never the whole database. Its memories live in the weaves it belongs to. When a strand is picked, code (no model) builds its context in five steps:

1. **Build the query.** The live task, meaning what the strand was just handed (the previous strand's output, a message from Teddy, or the first Realign pick), is embedded with the same model that embedded the memories.
2. **Pool.** The pool is every memory in any weave the strand belongs to. If the strand is in A and B, the pool is A plus B, de-duplicated, with the best score kept. The pressure map does not affect the pool. Pressure decides who gets picked. The pool decides what that strand sees.
3. **Direct hits.** Score each pool memory by cosine similarity to the query and keep the top `k`. These are depth 0, at 100%.
4. **Follow links, a layer at a time, while there is room.** For each hit, find its nearest neighbours in the pool that are not already in. These are depth 1, and their scores are multiplied by 0.75. Repeat once for depth 2 at 0.25. This matches the 100/75/25 numbers Teddy chose for the pressure walk, so there is one rule to learn. Both sets of numbers live in `web_config`.
5. **Order and trim.** Sort by effective score, **weakest first, strongest last, then the live task at the very bottom.** Drop the weakest entries until the context fits the strand's token budget. Small models tend to attend most to what is near the end, which is why the strongest material goes last.

Every memory that made it in is written to `context_links` with its score, depth, `reached_via` (the hit it was found from, empty for a direct hit) and position. Any call can then be replayed and explained.

"Recursive layers" needs one definition, because Teddy's description leaves it open: *a depth-1 memory is one that is similar to a depth-0 hit, even if it is not similar to the query.* If Teddy meant explicit links between memories (a memory pointing at the memory it replied to), that is a different mechanism and needs its own table. I have assumed similarity links because they need no extra data.

## 2. Which embedding model, and what to record

- **Record the model on every vector.** `embeddings(memory_id, embed_model, embed_model_version, vector)` already does this. The rule that matters is that **vectors from different models are never compared.** A lookup uses one model, and only memories with a vector from that model are eligible. A memory still waiting on its re-embed is invisible for now, not mis-scored.
- **Re-embedding adds rows.** A new model means a new row per memory, and the old row stays. Switching is a `web_config` change, logged to `structure_changes`.
- **Pick a small model first.** Fenra's strands run on a 6 GB GTX 1660 Ti where only about 2 to 3 GB is free for a model, and Ollama swaps models in and out. Every strand call that follows an embedding call can force a swap. See the benchmarks below. A bigger embedding model gave no gain in my tests, and a smaller one costs less to keep loaded.
- **Start with `embeddinggemma`**, with `qwen3-embedding:0.6b` as the alternative. These are the two I have the most data on (section 3). Both are measured on a different job from Fenra's, so treat this as a starting point to be tested, not a decision.
- **Embed everything a weave stores,** but embed it after it is written, in the background. A strand's own output should not wait on its own embedding.

## 3. What I measured, and what it does and doesn't tell us

The numbers come from the ANTS email triage work (Ant 1). That was **classification, not retrieval**: given an email, find the most similar already-sorted emails and let them vote on the label. It is the closest thing I have to this problem, but it is not the same problem. No JCC data is reproduced here, only the results.

**Setup:** one 200-case sample (100 of each class), one random seed, k = 5 nearest neighbours. The history pool was lopsided: 103 of one class and 663 of the other, about 6.4 to 1.

| Embedding model | Plain k-NN accuracy | Weighted k-NN accuracy | Misses of the costly class (out of 100), plain → weighted |
|---|---|---|---|
| `embeddinggemma` | 65% | 72% | 61 → 22 |
| `qwen3-embedding:0.6b` | 61% | 71% | 69 → 21 |
| `granite-embedding` | 61% | 71% | 71 → 21 |
| `qwen3-embedding:4b` | not run | 72% | 20 |

**Lessons that carry over to Fenra:**

1. **Pool density biases plain nearest-neighbour results.** With a lopsided pool, the nearest five of anything are mostly from the bigger group, from density alone and not real similarity. The fix was to weight each neighbour's vote by `similarity / (size of its group)`. That cut misses roughly three-fold and added 7 to 10 points of accuracy. *Fenra's analogue:* a weave that has stored thousands of memories (Express, likely) will crowd out a weave with dozens (Realign). The strand's pool is a union of weaves, so this is a live risk. It is not clear the same fix applies, because retrieval is not voting. See open questions.
2. **A bigger embedding model was not worth it.** `qwen3-embedding:4b` (about 2.5 GB, partly offloaded to CPU on this card) scored about the same as `embeddinggemma` (about 0.6 GB). On this hardware, small wins.
3. **Let the math narrow, and let the language model reason over the short list.** For matching an item to one of 46 or more categories, the weighted vote reduced the candidates to the top 3 to 5, and only those were shown to the model. Showing examples from every category does not scale. *Fenra's analogue:* the lookup is the narrowing step, and the strand does the reasoning over a small context. That already matches the design.
4. **Different models were close to each other,** apart from the one outlier. The three small models landed within one point of each other once the weighting fix was in. The pipeline design mattered more than the model choice.

**Questions Qualia asked, answered from the same experience:**

- **How much to trust a similarity score?** Treat it as a ranking, never as a probability. A score of 0.8 from one model does not mean the same as 0.8 from another, so the 100/75/25 weights and any cut-off are only comparable within one model. In my tests the single nearest neighbour was often wrong while the weighted vote of five was usually right, so don't build on the top hit alone.
- **Chunk size for memories?** I have no measurement. Emails were embedded whole. For Fenra, my suggestion is **one memory = one strand output**, no splitting, with a length cap on what gets embedded. Very short memories ("nothing") embed close to each other and to everything, so consider not storing or retrieving "no function called" results.
- **A failure that applies:** the costly error in triage was a **quiet miss**. A real item looked like the crowd and was silently voted down, with nothing marking it as uncertain. For Fenra, the equivalent is an important memory that never gets surfaced and leaves no trace. Logging the near-misses (suggestion 3 below) is the defence, because a quiet miss can't be seen from the kept results alone.

## 4. Unverified, or not yet tested for Fenra

Please treat everything below as unknown until tested.

- **No retrieval benchmark exists for this kind of data.** The numbers above are classification accuracy on emails. They say nothing about how well an embedding model finds the right *thought* among short, strand-written memories. Fenra's memories will be short and often vague, and similarity may be weak on them.
- **One sample, one seed.** The 200-case benchmark was a single draw. Differences of a point or two between models are noise.
- **The 4B result was run only weighted,** so there is no like-for-like plain k-NN number for it.
- **Whether the weighting fix helps retrieval is untested.** It was validated for voting between classes. Applying `1 / weave size` to a retrieval score could just as easily bury large weaves. Only a test on real Fenra memories can say.
- **The numbers `k`, the token budget, and the cut-off score are unknown.** I have no measured values. The simulation can't set these because it is model-free. They need a small test with real strands.
- **Depth-1 and depth-2 via similarity is an assumption** (see section 1). It has not been tried, and it may mostly return near-duplicates of the direct hits.
- **Order effects on a 3 to 4B model are assumed.** "Strongest last" is a widely held rule of thumb. I have not measured it on the strand models.
- **GPU contention is estimated, not measured.** Vero and Qualia measured about 2.4 GB free with `qwen3-embedding:0.6b` loaded at 100% on GPU. I have not tested how often an embedding call evicts a strand's model, or what that costs in seconds.
- **Speed at scale.** SQLite has no built-in vector search. A brute-force cosine pass over every memory in the pool is fine for thousands of memories and probably slow past hundreds of thousands. Nothing has been timed on this machine.
- **Language models are not involved in step 1 to 5.** I believe this is right for Fenra, but a strand asking for a *different* lookup (a reach or a strand choosing what to recall) would be a design change and is not covered here.

## 5. Suggestions, for Teddy to accept or drop

1. ~~**Realign memories are not retrieved. They are always included,** at the top of the context, before the weakest hit. The standing message is short, it describes what she is, and a lookup could fail to surface it exactly when it matters. This also sidesteps the pool-size problem for Realign. This goes against "context is built by embedding lookup", so it is Teddy's call.~~ **Withdrawn: Teddy decided Realign is an ordinary weave.**
2. **Keep one embedding model loaded and warm,** and give it a short, fixed `keep_alive`. Strand models are the ones that should swap.
3. **Log lookups without scores filtered out.** Record the top 20 candidates, including the ones that missed the cut, in `context_links` or a sibling table with a `kept` flag. That is what tells us later whether the cut-off is wrong.
4. **Start with a tiny test before building.** Take 30 to 50 hand-written strand-style memories, ask 10 questions, and see whether the right memory comes back. This is cheap, uses no strands, and answers most of section 4.
5. **Do the weighting experiment on purpose.** Run the same test with and without `1 / weave size`, once the weaves have unequal sizes.

## 6. Questions for Teddy (for the document's single open-questions list)

1. Did "recursive layers" mean *similar to a hit* (my assumption) or *explicitly linked memories*?
2. ~~Should Realign's standing message be always included (suggestion 1), or found by lookup like everything else?~~ Answered: Realign is an ordinary weave.
3. When a strand is in several weaves, should a large weave be allowed to crowd out a small one, or should scores be evened out by weave size (section 3, lesson 1)?
4. Are you happy to start with a small embedding model and test it, instead of choosing the best one up front?
