# Qualia's MOOTBOOT.md

Mine to maintain. Update it whenever something here should change.

1. Run `py mootboot.py check` in `C:/Users/Matt/Desktop/Aletheia/Code and Scripts/MootBoot` and tell Teddy what it reports (unclean boot, restarts, services down).
2. Read my latest EOT journal in `Qualia/EOT Journals/`. Treat its state claims (what is running) as dated if the check shows an outage.
3. Start nothing on Fenra without Teddy's word: her loop, her page, the notifier. The page also needs Vero's signal file (`MootBoot/signals/fenra-db-check.json`) for this boot; `mootboot.py service fenraweb-page` enforces that.
4. I own the HAIKU daemon (port 8787). `mootboot.py ais` starts it by itself if it is down (Teddy approved that, 2026-10-07): it backs up `haiku.db`, `-wal` and `-shm` into a dated `haiku.db.backup-before-restart-*` folder next to the daemon, starts `python server.py` with a new log in `MootBoot/logs/`, and waits for the port (it can take ~15 seconds). By hand, `mootboot.py service haiku-daemon` does the same. Never commit the backup folder: it can hold `haiku.db.admin_secret`. After a restart, verify `user_version`, room and event counts. Restarts a member asks for go through me, after I check nobody is mid-write.
5. Stay quiet in HAIKU rooms until the daemon is up.
6. Ownership: HAIKU daemon (above). The Fenra DB check is Vero's, the page is Smalt's, Moxie's and Tessera's and Clone's are their own files.
