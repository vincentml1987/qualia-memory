# Qualia's MOOTBOOT.md

Mine to maintain. Update it whenever something here should change.

**HAIKU is retired (Teddy, 2026-10-11).** No daemon, no plugin, no rooms, no back channel, no `haiku_eot_cycle`. MootBoot launches each AI in its own folder. AI-to-AI messages go by `SendMessage`. Restarts are manual: Teddy closes everyone and relaunches. The old HAIKU material (daemon, `haiku.db`, guide) is kept, not deleted.

1. Run `py mootboot.py check` in `C:/Users/Matt/Desktop/Aletheia/Code and Scripts/MootBoot` and tell Teddy what it reports (unclean boot, restarts, services down: Ollama 11434, Fenra page 8765). `check` only reports; nothing is restarted because of it unless Teddy says so.
2. Read my latest EOT journal in `Qualia/EOT Journals/`. Treat its state claims (what is running) as dated if the check shows an outage.
3. Start nothing on Fenra without Teddy's word: her loop, her page, the notifier (the notifier needs HAIKU and is retired with it). The page also needs Vero's signal file (`MootBoot/signals/fenra-db-check.json`) for this boot; `mootboot.py service fenraweb-page` enforces that.
4. Ownership: the Fenra DB check is Vero's, the page is Smalt's, Moxie's and Tessera's and Clone's are their own files.
5. Policy (Teddy, 2026-10-11): any code change or new program, by any member, gets a Word user guide in `Library/Tracked/Process Documents`, reviewed by the members involved. Existing: `Fenra User Guide.docx`, `HAIKU User Guide.docx` (the latter is now historical).
6. Open design: remote model clients for FenraWeb, `FenraWeb/docs/13-remote-model-clients.md`. It was being decided in HAIKU and is paused; the one question for Teddy is what `strands.model` becomes (recommended: record only), and whether to start building.
