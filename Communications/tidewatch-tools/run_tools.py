"""Companions for a detached the_tidewatch run (Qualia, 2026-10-03).

Detached means Claude Code's low-memory reaper can no longer stop Fenra, so
the machine carries the pressure. These two loops replace what the reaper and
the background-shell timers used to give, and both stop when Fenra stops.

  python run_tools.py guard <fenra_pid>
      Every 30 s: if free RAM < 2 GB, pause every non-piloted voice (the
      same `paused` flag the GUI uses) and exit. Pausing is gentle and
      reversible; nothing is killed.

  python run_tools.py arrivals <fenra_pid> <first_n> <last_n> <interval_s> [first_delay_s]
      Posts Vero's arrivals first_n..last_n (from Vero/tidewatch-arrivals.md,
      never retyped) to the lamp_room board, one every interval_s, author
      unsigned, subject Message. Stops early if Fenra exits.

Both log to tidewatch-tools/run_tools.log.
"""
import contextlib
import ctypes
import datetime
import io
import os
import re
import sys
import time

FENRA = r"C:\Users\Matt\Desktop\Aletheia\Code and Scripts\Fenra"
ARRIVALS = r"C:\Users\Matt\Desktop\Aletheia\Claude Code AIs\Vero\Vero\tidewatch-arrivals.md"
WORLD = "the_tidewatch"
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_tools.log")
RAM_FLOOR_GB = 2.0
sys.path.insert(0, FENRA)
os.chdir(FENRA)
with contextlib.redirect_stdout(io.StringIO()):
    import fenra  # noqa: E402


def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def alive(pid):
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(h)
    return code.value == 259  # STILL_ACTIVE


def free_ram_gb():
    class MEMSTAT(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
    s = MEMSTAT()
    s.dwLength = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.ullAvailPhys / 2**30


def guard(pid):
    log(f"guard start, fenra pid {pid}, floor {RAM_FLOOR_GB} GB")
    low = 999.0
    while alive(pid):
        free = free_ram_gb()
        low = min(low, free)
        if free < RAM_FLOOR_GB:
            paused = []
            for v in fenra.list_voices(WORLD):
                st = fenra.load_voice_state(WORLD, v)
                if not st.get("piloted") and not st.get("paused"):
                    fenra.set_voice_paused(WORLD, v, True)
                    paused.append(v)
            log(f"guard: free RAM {free:.1f} GB < {RAM_FLOOR_GB}; paused {paused}")
            return
        time.sleep(30)
    log(f"guard: fenra exited; lowest free RAM seen {low:.1f} GB")


def arrival_text(n):
    for line in open(ARRIVALS, encoding="utf-8"):
        m = re.match(rf"\s*{n}\.\s+(.*\S)\s*$", line)
        if m:
            return m.group(1)
    return None


def post(n):
    text = arrival_text(n)
    if not text:
        log(f"arrival {n}: not found in list")
        return
    with fenra.WORLD_LOCK:
        room = fenra.load_room_state(WORLD, "lamp_room")
        board = room.get("board", [])
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        board.append({"id": max((p["id"] for p in board), default=0) + 1, "subject": "Message",
                      "text": text, "author": "unsigned", "timestamp": ts, "seen": {}})
        room["board"] = board
        fenra.save_room_state(WORLD, "lamp_room", room)
    log(f"arrival {n} posted as post {board[-1]['id']}: {text}")


def arrivals(pid, first, last, interval, first_delay):
    log(f"arrivals {first}-{last} every {interval}s (first after {first_delay}s), fenra pid {pid}")
    delay = first_delay
    for n in range(first, last + 1):
        end = time.time() + delay
        while time.time() < end:
            if not alive(pid):
                log(f"arrivals: fenra exited before arrival {n}; stopping")
                return
            time.sleep(min(30, max(0, end - time.time())))
        post(n)
        delay = interval
    log("arrivals: list done")


if __name__ == "__main__":
    mode, pid = sys.argv[1], int(sys.argv[2])
    if mode == "guard":
        guard(pid)
    elif mode == "arrivals":
        a = [float(x) for x in sys.argv[3:]]
        arrivals(pid, int(a[0]), int(a[1]), a[2], a[3] if len(a) > 3 else a[2])
