# Retrieval test results (embeddinggemma), 2026-10-05

Run by Formica for Teddy. Planning-stage test only: nothing here is Fenra's real data and no strands were run.

## What was tested
- **48 made-up memories**, written by hand in the style of strand outputs: Express 20, Consider 14, Observe 10, Realign 4 (so the weaves are different sizes on purpose). Files: `test_data.py` (all memories and questions), `run_test.py`, `summarize.py`, `results.json` (every number).
- **14 questions**, each standing in for "the last strand's output, R". 12 have 2 or 3 memories that a good lookup *should* find. 2 have no relevant memory at all (bicycles, the capital of Australia), to see what a "nothing here" score looks like.
- **The walk, as Teddy described it:** closest 3 to R (level 0), closest 3 to each of those (level 1), closest 3 to each of those (level 2). Memories already collected are skipped. Up to 39 memories.
- **Model:** `embeddinggemma` through Ollama. Run twice: once as plain text, once with the model's recommended "search query / document" labels in front of the text.

## Headline numbers (with the labels; the better run)
| | Result |
|---|---|
| Questions where a correct memory is in the top 3 | **12 of 12** |
| Correct memories found at level 0 (top 3) | **24 of 27** |
| ...after level 1 | 26 of 27 |
| ...after level 2 (all 39) | **27 of 27** |
| Top similarity score, questions with a real answer | 0.33 to 0.74 |
| Top similarity score, the 2 questions with no answer | **0.20 and 0.09** |
| Time to embed 48 memories + 14 questions | about 5 seconds (25 seconds on the first run, while the model loaded) |

Without the labels: 11 of 12, 21 of 27 at level 0, 24 of 27 at the end, and the "no answer" scores were 0.36 and 0.27, which is closer to the real ones. **Use the labels.** This is a stored setting and a one-line change.

## What it tells us
1. **The lookup works on this kind of text.** Short first-person thoughts about everyday topics are found easily, even when the wording differs (for example, "tired after work, keep it short?" found "work was long today and I am tired, so short answers are fine").
2. **The walk earns its keep.** Levels 1 and 2 rescued 3 correct memories that the first 3 missed, mostly the Realign facts. The first lookup misses vague, abstract questions, and the neighbours of what it did find pull them in.
3. **A score floor looks possible, but it is thin.** Real matches scored 0.33 and up. Unrelated questions scored below 0.21. A cut-off near 0.25 would have worked here. The weakest real match (the abstract "what do I know about what I am?" at 0.33) is close to the noise, so the cut-off should be set once there are real memories.
4. **The weave-size fix (my crude version) hurt badly.** I divided each score by the weave's size, scaled to the average. The 4 Realign memories then took all 3 slots on almost every question, including "How do bicycles stay upright?". The number of correct memories in the top 3 dropped from 24 to 10. This matches my lean in the draft: do **not** apply a fix before seeing a real crowding problem. In this test, no crowding happened without it. Big Express did not drown the small Realign weave on the questions about Realign.

## What it does *not* tell us (please read)
- **The test is small and easy.** 48 memories, written by me, with clear topics. Real strand output will be vaguer and more repetitive. Expect worse results on real data.
- **The walk returned 39 of the 48 memories.** In a database this small, level 2 just collects most of everything, so 27 of 27 is partly an artefact. The walk can only be judged properly once the database has thousands of memories.
- **No measure of "noise".** I counted correct memories found, not how many wrong ones came along. At 39 memories per call, most of what a strand sees will not be relevant. That is Teddy's design; whether a 4B model copes with it is a strand test, not an embedding test.
- **Overlaps:** when a neighbour was already collected, I took the next-closest instead, so every question returned exactly 39. If you would rather let overlaps shrink the set, results will be slightly smaller.
- **One run, one seed, one model.** There is no randomness here, but a different set of questions could shift the numbers.
- **Not tested:** speed at thousands of memories, GPU memory while a strand model is loaded, repeated memories ("nothing", "No new messages"), or very long memories.

## Suggested next steps (Teddy's call)
1. Keep the labels (query/document prefixes) as part of the embedding setting, recorded with the model name.
2. Repeat this test on real Fenra memories once she has a few hundred, and compare.
3. Skip the weave-size fix for now.
4. Decide whether the near-miss log should also record scores, so a cut-off like 0.25 can be tuned later.
