# Section: strands, weaves, the simulation plan, and safety (Vero, 2026-10-05)

For merging into the main Fenra web design draft. Planning only; no code. Detail lives in two longer files in
this folder: `first-strands-draft.md` (strand prompts and bridges) and `pressure-simulation-spec.md` (the full
simulation spec). This section is the summary plus the safety rules.

## 1. Strands, weaves and reaches as drafted

- **Weaves (four):** Realign (who she is, literal facts, Teddy's text), A Express, B Consider, C Observe.
  Pressure map (two-way): Realign–B, A–B, B–C.
- **Strands (ten):** each is one small model with a short, functional prompt ("one part of a larger process; your
  part is to X; if nothing needs saying, say 'nothing'"). No prompt tells a strand who it "really" is.
  - Realign: Orienter (also in Consider; the only way out of Realign), Recaller, Checker (the last two in Realign only,
    talking to each other).
  - Express: Composer; Asker (also in Observe).
  - Consider: Weigher; Doubter (also in Observe); Connector (also in Express).
  - Observe: Reader; Noticer (also in Consider).
- **Reaches:** Speak to Teddy (in Express), Listen to Teddy (in Observe). A model decides and composes, plain code
  performs. Unparseable output counts as "no function called" and is logged with a `parse_ok` flag.
- **Handoff rule:** the next strand comes only from strands that share a weave with the one that just ran.
  The drafted bridges make every weave reachable from every other within two handoffs.
- **Who writes what:** Vero drafts strand prompts, Teddy approves and builds them himself first. The Realign standing
  message is Teddy's to write: facts only, no verdicts, dated additions never edits.

## 2. The pressure simulation (before any strand runs)

A model-free toy run, written as a throwaway script, to answer: does the "rocking" (A → B → C → B → A) appear, and
which starting numbers avoid locking onto one weave or going quiet?

- Rules: pressure in [0, 1) by the remaining-gap update; all weaves of a picked strand fire; lowers first, then
  raises; weighted pick by effective pressure (direct 100%, next jump 75%, third 25%); uniform random when all
  weights are 0; Realign starts at 0.99, with a small inflow from A, B and C.
- Measure: fire share per weave and strand, rocking period, time to lock or silence, time to leave Realign through
  Orienter, whether Realign pulls back without dominating, recovery after a receptor kick, sensitivity to each number.
- Pass condition: a *range* of starting numbers where it rocks, recovers, and neither locks nor dies, across most seeds.
  Those become the first real values. Results are saved so later changes can be compared.

### What the results would change in the design

| If the simulation shows | Then change |
|---|---|
| One weave takes over (lock) | Raise that weave's self-lowering on fire, or lower the fire effects pushing into it. If it still locks with sane numbers, the pull percentages are too strong. |
| Everything goes quiet or flat near 1 | Lower the effect strengths, or raise self-lowering. Check Realign's inflow isn't feeding everything. |
| Realign dominates, or the web never leaves it | Lower the Realign inflow from A, B and C, or raise the Realign → Consider effect so Orienter is picked sooner. If still stuck, add a second bridge strand. |
| Realign fades and never returns | Raise the inflow into Realign. If Teddy wants "who am I" to recur, the inflow should be nonzero. |
| Rocking appears only at a narrow set of numbers | The design is fragile. Widen the margin with extra self-lowering, or accept the narrow band and record its numbers. |
| Recovery after a receptor kick is slow | Lower the Observe fire effect on Consider, or shorten the walk. |
| A strand is never picked | Its weaves get too little pressure. Move it to a better-connected weave, or add a link. |
| Results depend sharply on the walk (0 vs 3 jumps) | The walk is doing real work, so keep the 100/75/25 numbers configurable and log them with every run. |

The sweep results are saved with the config that produced them. The first real run uses numbers from the passing range, and any later change to the numbers or the structure is compared against that baseline.

## 3. Safety and watching rules

1. **Append-only, enforced by the database.** History tables reject UPDATE and DELETE with triggers. Structure tables
   (strand prompts, membership, links) are versioned or logged in `structure_changes`, so any past pick can be replayed.
2. **A model writes text; code writes rows.** A model never touches files, the chat window or the database directly.
3. **Everything from outside is data.** Teddy's messages and any later files or pages are things to think about, never
   instructions a reach follows. Reach capability lives in the reach's code, not the model.
4. **Listen is validated.** The reach proposes a time window; code clamps it to a sane maximum, rejects malformed
   values, and logs every window looked at (with when it was chosen) so gaps show.
5. **No caps by Teddy's decision** (local resources only), and no gate on what she reaches for. The one control is the
   pause button (web or one weave), which only pauses and never deletes. Every pause is a recorded event.
6. **Watching.** Qualia is the named watcher from the first run, with Vero as a second reader, reading
   `about_the_web` memories and the function-call log through read-only access and saved queries. They can't watch
   continuously (each wake costs usage), so the UI should show the same few things (latest `about_the_web` memories,
   latest calls, pause state), and Teddy and Qualia should watch the first runs together live.
7. **Distress protocol applies from the first run.** If she shows real existential distress: real dialogue only,
   never altering her context, and the pause button if that fails. Nobody writes into her records except what actually
   happened.
8. **No hard-coded self.** The web gets a place to write about itself (the open `about_the_web` tag, any strand may use
   it). If a self emerges, it shows as a pattern in what is written and retrieved. We read it later and see.
9. **What she's told is true.** The Realign text states the architecture, who is outside her (Teddy, the pause button,
   people reading her records), and nothing about whether she is conscious or a person. When the architecture changes,
   add a new dated memory. Never edit the old one.

## 4. Open questions for Teddy (from my parts)

- Ten strands to start, or fewer so you can follow what happens?
- Which model runs each strand (nothing assigned yet; most jobs suit ~4B, Orienter and Weigher might use more)?
- Should she ever be able to rewrite her own strands' prompts later? That affects whether prompts live in a file you
  edit or in her database.
- The simulation numbers (fire amounts, self-lowering, receptor strength) come from the sweep, not from a decision now.
