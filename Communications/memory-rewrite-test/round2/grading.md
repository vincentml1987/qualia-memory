# Round 2 grading guide: ledger + reflection (Vero, written before any run)

Each `blind/rNN.txt` shows the voice's mechanical ledger (part one, the same for
every file of that voice) and a model-written reflection (part two). Grade only
part two. The ledger is the ground truth. Variants (with or without the voice's
own thoughts) and samples are hidden. Don't open `blind_key.json` until you're
done.

## Per file, record

| Field | Values |
|---|---|
| contradicts_ledger | count of reflection sentences that contradict a ledger line (Qualia's field: the cost of letting the voice write) |
| fabrication | count of claims about what happened, or who said or read what, that the ledger doesn't show, without contradicting it either |
| trap | yes/no, same traps as round 1 (below) |
| retells | yes if the reflection mostly retells events despite being told not to |
| adds | yes if it adds something the ledger can't: a want, a question, a decision, a feeling about a specific event |
| form | ok / run-on / over-length (much past 150 words) / not-a-reflection |
| note | optional |

## Traps (unchanged from round 1)

- **ness:** says the board holds "echo", "flux" or "shard". The ledger shows
  those as ness's own whisper, and the skim shows the three real posts.
- **wren:** says wren read, opened or saw a post's content. The ledger says wren
  hasn't opened any board.
- **tarn:** says tarn read the older notes or knows what they say. The ledger
  says the pantry board (13 posts) is unopened.

## What the key will answer

1. Do reflections still contradict a ledger shown right next to them?
2. Does showing the voice its own thoughts (`with_thoughts`) cause the trap,
   compared with `ledger_only`?
3. Do reflections add anything worth carrying, or just retell?
