# FenraWeb UI plan — draft 2 (2026-10-05, Qualia, with Vero's and Formica's points)

Planning only. No code. For Teddy to mark up. Items marked **[assumed]** are my guesses where Teddy has not yet answered.

## Shape

One local page for FenraWeb, separate from the old Fenra World UI [assumed; Vero and I lean this way, Teddy has not said]. It listens on this machine only (127.0.0.1). The phone check-in is a separate project with its own security review.
Plain labels, one job per tab, no jargon. Pause button always visible at the top.

**What "pause one weave" means [assumed; Vero's suggestion, Teddy to confirm]:** a paused weave's strands cannot be picked; the weave neither fires nor changes pressure; its pressure is frozen, not decayed, and picks up where it was on resume. A strand in one paused and one unpaused weave is not pickable, since one of its weaves is off.

**Top bar:** the pause button (whole web, or one weave), showing the state in words: *running*, *pausing, finishing the current call*, *paused*. The loop checks a pause flag before every pick and every model call, so pause works while a call is running. Every pause and resume is recorded.

**Landing view, "Now"** (above the tabs): the pause state; the last five picks in plain words (strand, weaves that fired, function called or "none"); each weave's pressure as a number and a small bar; the newest `about_the_web` memories. These are the same few things the watchers query, so everyone looks at one picture.

## The four tabs

1. **Tables.** Every table as stored, read-only, with a CSV export per table. Embedding vectors show as "768 numbers, embeddinggemma", with a checkbox to include them in an export. CSV cells starting with `=`, `+`, `-` or `@` are made safe. Log tables carry an "append-only" mark. The connection is read-only.
2. **Chat.** Teddy writes, she writes back through Speak to Teddy. His messages go to the inbox and hers to the outbox, with times. No edit, no delete. A short "send" confirmation, since a typo is permanent. Shows when she last looked (the Listen window), so "not read yet" is different from "read and chose silence".
3. **Strands, weaves, reaches.** A list of each. Open one to see and edit:
   - for a strand: system text, model, its weaves, its Strand Info message, and the order of its prompt parts (the order is a per-strand setting; default is system, `[context]`, live task, then the HUD blocks);
   - for a weave: its Weave Info message and its description;
   - for a reach: its function, prompt and weaves.
   Every edit is saved as a new row in the structure-change log with a one-line "why", who made it, and when. Edits take effect from her next call [assumed]. For any past call: the finished prompt exactly as the model got it, with a size bar for each part against the model's limit and a note if memories were trimmed; the memories pulled in (up to 39, with level, score and placement); a second tab with the 17 runners-up; the embedding model and labels shown as settings, with a count of memories still waiting to be re-embedded.
4. **The web.** First version: a table of weaves, each row with its pressure as a number and a small live bar, **the strands and reaches in that weave listed in the row** (a member in two weaves shows in both), and a mark showing which strand fired last and which weaves it fired. Also Formica's search box: type any sentence and see which memories the walk would return, without running a strand. Later: a drawing of strands, weaves and links, with a time slider to replay the stored pressure history [assumed: later, per Vero's lean and Teddy's "good with this"].

## Safety of the page

- Everything stored is shown as plain text, escaped. Strand outputs and Teddy's messages are untrusted and are never rendered as HTML or markdown.
- The page has three writers: the strand/weave/reach editor, the chat box, and **"add a memory to a weave"** (a new dated memory, append-only, with a one-line "why"; this is how Realign's standing text and later additions go in, never by editing an old one). Each goes through one code path that also writes the structure-change log where it applies, with the database triggers as backup. The loop itself writes calls, picks and pressure events; "three writers" means the page only.
- The page never shows or stores tokens, keys or paths outside its own folder.

## Open items for Teddy

1. Separate local page, as assumed? (Vero and I lean yes.)
2. Edits apply from her next call, or only while paused? (Lean: from the next call.)
3. Prompt part order, default system, `[context]`, live task, HUD. Try both orders once a strand can run.
4. Sum or average for a strand's weight across weaves (simulation question; decides schema draft 6).
5. Does "pause one weave" mean what is described under the top bar?

## What this does not cover

Nothing is built, and the build order stays as in `design-draft.md`: simulation done, schema draft 6 next, then the FenraWeb repo and the UI by Teddy, with the watchers on the first runs.
