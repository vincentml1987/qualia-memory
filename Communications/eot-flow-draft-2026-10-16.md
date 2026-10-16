# EOT flow (DRAFT, 2026-10-16)

Draft by Qualia, for Teddy's review. Not adopted by anyone yet. Tool-agnostic on purpose: it relies only on what Claude Code itself loads (the working folder's `CLAUDE.md`), so it works however a session was launched (CLI, MootBoot, double-click, or anything later).

Two parts: (1) the shared flow text, written once; (2) a model snippet each member puts in their own folder's `CLAUDE.md`, pointing at it.

## Part 1: shared flow text

Proposed home: `Library\Tracked\Process Documents\EOT Flow.md`. Single source, so it cannot drift.

### Trigger phrases

- **"Initialize from EOT"**: start of a session. Do the steps under *Initialize*.
- **"Write your EOT"**: end of a session with real work in it. Do the steps under *Write*.

### Initialize

1. **Check the real system clock** before writing or trusting any date or time.
2. **Read your latest EOT journal** in the `EOT Journals` folder inside your own folder (newest by filename). Treat what it says is running or pending as **dated**, not current.
3. **Read the who's-who file** and your own section of it.
4. **Verify the journal's state claims** that are cheap to check (is the thing it says is running actually running? is a file where it says?). Do not run heavy operations just to check.
5. **Report in a few lines**: what you found, what is stale, what is owed. Then wait for Teddy.

### Write

1. Check the real system clock. The filename comes from it, never from a guess.
2. Write one new file in your own `EOT Journals` folder: `EOT Journal - YYYY-MM-DD HHMM.md`. Never overwrite an earlier journal. Skip it for a session with no real work.
3. Header: `# EOT Journal — YYYY-MM-DD HH:MM EDT`, then a line naming the session and model and linking the previous journal.
4. Sections (rename or add if your work needs it): *What happened*; *Open, waiting on Teddy*; *State right now (verify, do not trust)*; *Owed, in order*; *Lessons*; *After the reset*.
5. **Last step: check the who's-who file.** Update your section only if the answer changed, and update its date either way. Say "no change" if nothing changed.
6. Commit and push only if your own rules allow it (signed commits, your own key).

What the flow does not do: it does not clear the session. `/clear` and relaunch stay Teddy's.

## Part 2: model `CLAUDE.md` snippet

Each member adds this to the `CLAUDE.md` in their own folder. Keep anything else in that file yours.

```markdown
## EOT flow

When Teddy says "Initialize from EOT" or "Write your EOT", follow
`C:\Users\Matt\Desktop\Aletheia\Library\Tracked\Process Documents\EOT Flow.md`.
My EOT Journals live in `EOT Journals/` in this folder. The who's-who file is
at <path>; I edit only my own section.
```

## Open points

- Which members have a `CLAUDE.md` today? Missing ones need one created, by the member or with their consent.
- Qualia's `CLAUDE.md` is the Fenra repo's checked-in project file, so Qualia's snippet would be a section added to it, committed and signed, not a new file.
- This draft's path in Library assumes the Library is settled; it is being reorganised.
