#!/usr/bin/env python3
"""studioigor autopilot — independent game development without the user (references/autopilot.md).

The scheduler is Claude Code's built-in CronCreate in the session where the autopilot was started
(`--scheduler session`, the default): on schedule it tells the session to run
`autopilot.py tick` in the background. Need to close the terminal — `--scheduler system` (launchd on
macOS, cron on Linux). A tick holds a lock (flock) until the end, checks the limits and launches
a fresh lead agent: `claude -p "<tick prompt>"` in the game folder. The agent does one
pipeline step, commits and exits. All state is on disk (.studioigor/), so
every tick starts with `studio.py status`, not with memory.

  autopilot.py start [--goal slice|game|build] [--hours 10] [--every 15] [--max-ticks 60]
                     [--tick-minutes 90] [--tick-budget USD] [--mode auto|bypass] [--model M]
                     [--brief "…"] [--scheduler session|system|none] [--no-caffeinate]
                     [--no-preflight]
  autopilot.py tick      run by the session from the CronCreate job (or by launchd/cron)
  autopilot.py status
  autopilot.py stop [--reason "…"] [--now]
  autopilot.py prompt [--cron]

The last line of `tick` is for the host session: `NEXT: now` (next tick right away),
`NEXT: wait` (wait for the schedule), `NEXT: stop` (delete the CronCreate job).
It stops by itself: the agent created .studioigor/autopilot/STOP, the goal is closed, time ran out,
ticks ran out, 3 ticks in a row with an error or without changes to the game.
stdlib only, macOS/Linux (Windows — via WSL). Does not push or publish: the prohibitions are
in --disallowedTools.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shlex
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import studio  # noqa: E402

ST = studio.ST
AP = f"{ST}/autopilot"
GOALS = {
    "slice": (7, "bring the game to a playable vertical slice (done when the gates of phases 1–7 are closed)"),
    "game": (9, "bring it to a full game with content per SCOPE.md and polish (done when phases 1–9 are closed)"),
    "build": (10, "bring it to a full game and a release build for the chosen platform, without publishing "
                  "(done when phases 1–10 are closed)"),
}
MODES = {"auto": "auto", "bypass": "bypassPermissions"}
DENY = ["AskUserQuestion", "Bash(git push:*)", "Bash(sudo:*)", "Bash(gh:*)", "Bash(npm publish:*)"]
KEEP_ENV = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "SHELL", "DISPLAY", "WAYLAND_DISPLAY",
            "XDG_RUNTIME_DIR", "STUDIOIGOR_UC", "ANDROID_HOME", "JAVA_HOME", "ANTHROPIC_BASE_URL",
            "CLAUDE_CONFIG_DIR", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy")
SECRET_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")
# internal variables of the host Claude Code session — the tick doesn't need them
SESSION_ENV = {"CLAUDECODE", "CLAUDE_PID", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_CHILD_SESSION"}
SESSION_PREFIX = ("CLAUDE_CODE_SESSION", "CLAUDE_CODE_MESSAGING")
RUNTIME = ["state.json", "lock", "lock.json", "logs/", "runner.log", "LOG.md"]
CRON_STEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30)


# ------------------------------------------------------------------ state

def ap_dir(root: Path) -> Path:
    return root / AP


def load(root: Path) -> dict:
    try:
        return json.loads((ap_dir(root) / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save(root: Path, st: dict) -> None:
    d = ap_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "state.json.tmp"
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(d / "state.json")


def ts(dt: datetime | None = None) -> str:
    return (dt or datetime.now()).isoformat(timespec="seconds")


def parse_ts(s: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


def cell(s: str, n: int = 140) -> str:
    return " ".join(str(s).split()).replace("|", "/")[:n]


def log(root: Path, row: str) -> None:
    p = ap_dir(root) / "LOG.md"
    if not p.is_file():
        p.write_text("# Autopilot — tick log\n\n| # | start | min | phase | changed | commits | $ | outcome | "
                     "what was done |\n|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as fh:
        fh.write(row.rstrip("\n") + "\n")


def log_rows(root: Path) -> list[str]:
    return [l for l in studio.read(ap_dir(root) / "LOG.md").splitlines() if re.match(r"^\|\s*(\d+|—)\s*\|", l)]


def review_rows(root: Path) -> list[str]:
    rows = [l for l in studio.read(ap_dir(root) / "REVIEW.md").splitlines() if l.startswith("|")]
    return [l for l in rows[2:] if l.strip("|").strip() and not re.fullmatch(r"[|\-\s:]+", l)]


def phase_now(root: Path) -> str:
    m = re.match(r"\s*(\d+)", studio.field(studio.read(root / ST / "STATE.md"), "PHASE") or "")
    return m.group(1) if m else "?"


def head(root: Path) -> str:
    return studio.git(root, "rev-parse", "HEAD").stdout.strip()


def goal_closed(root: Path, goal: str) -> bool:
    cp = studio.current_phase(root, studio.parse_pipeline(studio.read(root / ST / "PIPELINE.md")))
    return cp is None or cp["num"] > GOALS[goal][0]


def find_root(arg: str) -> Path:
    if arg:
        r = Path(arg).expanduser().resolve()
        if not (r / ST).is_dir():
            sys.exit(f"no {ST}/ in {r} — run studio.py init first")
        return r
    return studio.find_root()


# ------------------------------------------------------------------ processes and lock

def alive(pid) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def proc_cmd(pid) -> str:
    if not alive(pid):
        return ""
    return subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()


def is_tick_agent(pid) -> bool:
    """PIDs get reused — check that this really is our `claude -p`."""
    c = proc_cmd(pid)
    return "--disallowedTools" in c and "--permission-mode" in c


def kill_group(pid, sig=signal.SIGTERM) -> None:
    try:
        os.killpg(int(pid), sig)
    except (OSError, TypeError, ValueError):
        pass


def try_lock(root: Path):
    d = ap_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    fh = open(d / "lock", "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        fh.close()
        return None


def read_lock(root: Path) -> dict:
    try:
        return json.loads((ap_dir(root) / "lock.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tick_running(root: Path) -> bool:
    fh = try_lock(root)
    if fh is None:
        return True
    fh.close()
    return is_tick_agent(read_lock(root).get("claude_pid"))


# ------------------------------------------------------------------ scheduler

def norm_every(m: int) -> int:
    """An interval cron can express exactly: a divisor of 60 or whole hours."""
    if m < 60:
        return min(CRON_STEPS, key=lambda d: (abs(d - m), d))
    return max(1, round(m / 60)) * 60


def cron_expr(every: int) -> str:
    """Not at :00 or :30 — fewer collisions with other schedules."""
    if every < 60:
        return "* * * * *" if every == 1 else f"{3 % every}-59/{every} * * * *"
    h = every // 60
    return "7 * * * *" if h == 1 else f"7 */{h} * * *"


def session_prompt(root: Path) -> str:
    q = shlex.quote
    tick = " ".join(q(x) for x in [sys.executable, str(HERE / "autopilot.py"), "tick", "--root", str(root)])
    status = " ".join(q(x) for x in [sys.executable, str(HERE / "autopilot.py"), "status", "--root", str(root)])
    return (f"studioigor autopilot ({root.name}): run in the background (Bash, run_in_background: true):\n"
            f"{tick}\n"
            "When the command finishes, look at the last line of its output:\n"
            "- `NEXT: now` — one line to the user with the tick's outcome, then immediately run the same command "
            "again, in the background;\n"
            "- `NEXT: wait` — don't write or do anything: the schedule will do the next run;\n"
            "- `NEXT: stop` — delete this job (CronList → CronDelete) and show the user the output of\n"
            f"  {status}\n"
            "Don't touch the project yourself: the tick agent does the work.")


def label(root: Path) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-") or "game"
    return f"com.studioigor.autopilot.{slug}-{hashlib.sha1(str(root).encode()).hexdigest()[:6]}"


def plist_path(lbl: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{lbl}.plist"


def tick_argv(root: Path) -> list[str]:
    return [sys.executable, str(HERE / "autopilot.py"), "tick", "--root", str(root), "--from-scheduler"]


def install(root: Path, st: dict) -> str:
    kind, lbl = st["scheduler"], st["label"]
    if kind == "launchd":
        pp = plist_path(lbl)
        pp.parent.mkdir(parents=True, exist_ok=True)
        with pp.open("wb") as fh:
            plistlib.dump({
                "Label": lbl, "ProgramArguments": tick_argv(root), "WorkingDirectory": str(root),
                "StartInterval": st["every"] * 60, "RunAtLoad": True, "EnvironmentVariables": st["env"],
                "StandardOutPath": str(ap_dir(root) / "runner.log"),
                "StandardErrorPath": str(ap_dir(root) / "runner.log"),
            }, fh)
        dom = f"gui/{os.getuid()}"
        subprocess.run(["launchctl", "bootout", f"{dom}/{lbl}"], capture_output=True)
        p = subprocess.run(["launchctl", "bootstrap", dom, str(pp)], capture_output=True, text=True)
        return "" if p.returncode == 0 else f"launchctl bootstrap failed: {p.stderr.strip() or p.stdout.strip()}"
    if kind == "cron":
        envs = " ".join(f"{k}={shlex.quote(v)}" for k, v in st["env"].items())
        line = (f"{cron_expr(st['every'])} cd {shlex.quote(str(root))} && env {envs} "
                + " ".join(shlex.quote(x) for x in tick_argv(root))
                + f" >> {shlex.quote(str(ap_dir(root) / 'runner.log'))} 2>&1 # {lbl}")
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        keep = [l for l in cur.splitlines() if lbl not in l]
        p = subprocess.run(["crontab", "-"], input="\n".join(keep + [line]) + "\n", capture_output=True, text=True)
        return "" if p.returncode == 0 else f"crontab not written: {p.stderr.strip()}"
    return ""


def uninstall(st: dict) -> None:
    kind, lbl = st.get("scheduler"), st.get("label", "")
    if kind == "launchd" and lbl:
        plist_path(lbl).unlink(missing_ok=True)
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{lbl}"], capture_output=True)
    elif kind == "cron" and lbl:
        cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        if lbl in cur:
            keep = [l for l in cur.splitlines() if lbl not in l]
            subprocess.run(["crontab", "-"], input="\n".join(keep) + ("\n" if keep else ""), text=True)


def installed(st: dict) -> bool:
    kind, lbl = st.get("scheduler"), st.get("label", "")
    if kind == "launchd":
        return subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{lbl}"], capture_output=True).returncode == 0
    if kind == "cron":
        return lbl in subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    return True  # session: the CronCreate job lives in the session and can't be checked from outside


def notify(title: str, text: str) -> None:
    if shutil.which("osascript"):
        subprocess.run(["osascript", "-e", f"display notification {json.dumps(text)} with title {json.dumps(title)}"],
                       capture_output=True)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", title, text], capture_output=True)


# ------------------------------------------------------------------ claude

def claude_cmd(st: dict, prompt: str, preflight: bool = False) -> list[str]:
    cmd = [st["claude"], "-p", prompt, "--output-format", "json",
           "--permission-mode", MODES[st["mode"]], "--add-dir", str(SKILL)]
    if st.get("model"):
        cmd += ["--model", st["model"]]
    if preflight:
        cmd += ["--no-session-persistence", "--max-budget-usd", "1"]
    elif st.get("tick_budget"):
        cmd += ["--max-budget-usd", str(st["tick_budget"])]
    return cmd + ["--disallowedTools", *DENY]


def run_env(st: dict, minimal: bool = False) -> dict:
    """minimal — like launchd/cron: only what was saved at start."""
    env = {} if minimal else {k: v for k, v in os.environ.items()
                              if k not in SESSION_ENV and not k.startswith(SESSION_PREFIX)}
    env.update(st.get("env", {}))
    env["STUDIOIGOR_AUTOPILOT"] = "1"
    return env


def parse_out_text(text: str) -> dict:
    text = text.strip()
    for chunk in [text] + text.splitlines()[::-1]:
        try:
            d = json.loads(chunk)
            if isinstance(d, dict):
                return d
        except ValueError:
            continue
    return {"is_error": True, "result": text[-400:] or "empty output"}


LIMIT = re.compile(r"(usage|rate|session|weekly|daily|5-hour)\s+limit|limit\s+(reached|hit|exceeded)|hit your limit",
                   re.I)


def limit_until(text: str) -> datetime | None:
    """When work is possible again; None — this is not a usage limit."""
    if not LIMIT.search(text or ""):
        return None
    now = datetime.now()
    m = re.search(r"\|(\d{10})\b", text)
    if m:
        return datetime.fromtimestamp(int(m.group(1))) + timedelta(minutes=2)
    m = re.search(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text, re.I)
    if m:
        h, mi, ap = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower()
        if ap:
            h = h % 12 + (12 if ap == "pm" else 0)
        if h < 24 and mi < 60:
            t = now.replace(hour=h, minute=mi, second=0, microsecond=0)
            return (t if t > now else t + timedelta(days=1)) + timedelta(minutes=3)
    return now + timedelta(minutes=45)


def build_prompt(root: Path, st: dict) -> str:
    n = st.get("ticks", 0) + 1
    dl = parse_ts(st.get("deadline"))
    left_h = (dl - datetime.now()).total_seconds() / 3600 if dl else None
    skill = str(SKILL)
    lines = [
        "You are the studioigor autopilot: independent game development without the user. The user "
        "has handed you all decisions and is unavailable now. Don't ask questions, don't wait for anyone.",
        "",
        f"Tick {n} of {st['max_ticks']}. Task: {GOALS[st['goal']][1]}. Time left: "
        + (f"~{max(0.0, left_h):.1f} h." if left_h is not None else "no limit."),
    ]
    if st.get("brief"):
        lines.append(f"User's brief (verbatim): {st['brief']}")
    if st.get("idle", 0) >= 1:
        lines.append(f"WARNING: {st['idle']} tick(s) in a row without changes to the game. Change the approach: "
                     "another path to the same gates, or --block with a reason and work on what isn't blocked. "
                     "On the 3rd the autopilot stops.")
    last = n >= st["max_ticks"] or (left_h is not None and left_h * 60 < st["tick_minutes"] + 10)
    if goal_closed(root, st["goal"]):
        lines.append("All of the goal's gates are closed: do the finish per autopilot.md §8 and create STOP.")
    elif last:
        lines.append("THIS IS THE LAST TICK: bring what you started to a working state and do the finish per "
                     "autopilot.md §8 (REPORT.md), no STOP needed.")
    lines += [
        "",
        f"1. Read {skill}/SKILL.md and {skill}/references/autopilot.md — the proxy rules take precedence in this mode.",
        f"2. python3 {skill}/scripts/studio.py status — do what it says.",
        f"3. One substantive step toward the goal, in about {max(20, st['tick_minutes'] - 20)} minutes: the current "
        "phase's gates or one mechanic's cycle. The game comes first.",
        "4. At the end: studio.py commit \"…\" and studio.py note \"what was done\" \"what's next\".",
        f"5. Goal reached, or no way forward without a human — finish per autopilot.md §8 and the file {AP}/STOP "
        "with the reason in one line.",
        "Forbidden: git push, publishing, purchases, sign-ups and logins, sudo, deleting outside the game folder, "
        "editing the skill's files (except learn.py propose).",
        "The tick's last message is one line: what was done.",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ lifecycle

def auto_report(root: Path, st: dict, reason: str) -> None:
    rep = ap_dir(root) / "REPORT.md"
    if rep.is_file():
        return
    run = studio.field(studio.read(root / ST / "ENV.md"), "RUN")
    rows = "\n".join(log_rows(root)[-10:])
    rep.write_text(
        "# Autopilot report (automatic)\n\n"
        "The agent didn't get to do the finish — this is the runner's summary. The first session with the user "
        "completes it (references/autopilot.md §8–9).\n\n"
        f"- How to play: {('`' + run + '`') if run and not studio.PLACEHOLDER.search(run) else 'RUN is not written in ENV.md yet'}\n"
        f"- Stopped: {reason}\n- Phase: {phase_now(root)}\n"
        f"- Ticks: {st.get('ticks', 0)}, $ {st.get('cost', 0):.2f}\n"
        f"- Decided on the user's behalf: {len(review_rows(root))} — {AP}/REVIEW.md\n\n"
        "## Last ticks\n\n| # | start | min | phase | changed | commits | $ | outcome | what was done |\n"
        "|---|---|---|---|---|---|---|---|---|\n" + rows + "\n", encoding="utf-8")
    if studio.in_repo(root):
        rel = f"{AP}/REPORT.md"
        studio.git(root, "add", "--", rel)
        studio.git(root, "commit", "-q", "-m", f"autopilot: auto report — {reason[:60]}", "--", rel)


def finish(root: Path, st: dict, reason: str) -> None:
    st.update(active=False, stopped_at=ts(), reason=reason)
    save(root, st)
    log(root, f"| — | {datetime.now():%d.%m %H:%M} | | {phase_now(root)} | | | | STOP | {cell(reason)} |")
    auto_report(root, st, reason)
    cf = st.get("caffeinate_pid")
    if cf and "caffeinate" in proc_cmd(cf):
        try:
            os.kill(int(cf), signal.SIGTERM)
        except OSError:
            pass
    notify("studioigor — autopilot stopped", f"{root.name}: {reason}"[:200])
    print(f"autopilot stopped: {reason}")
    print(f"  report: {AP}/REPORT.md")
    if st.get("scheduler") == "session":
        print("  delete the CronCreate job in the session: CronList → CronDelete")
    print("NEXT: stop", flush=True)
    uninstall(st)  # last: launchd may take this process down too


def ensure_ignored(root: Path) -> None:
    gi = root / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    need = [f"{AP}/{x}" for x in RUNTIME if f"{AP}/{x}" not in text.split()]
    if need:
        gi.write_text(text.rstrip("\n") + ("\n" if text else "") + "# studioigor autopilot\n"
                      + "\n".join(need) + "\n", encoding="utf-8")


def cmd_start(a) -> int:
    root = find_root(a.root)
    old = load(root)
    if old.get("active"):
        if old.get("scheduler") == "session" or tick_running(root) or installed(old):
            print("autopilot is already active — autopilot.py status. No CronCreate job — autopilot.py prompt --cron; "
                  "restart — stop, then start")
            return 1
    claude = shutil.which("claude")
    if not claude:
        print("`claude` not found in PATH — the autopilot has nothing to launch the agent with")
        return 1
    sched = a.scheduler
    if sched == "system":
        sched = "launchd" if sys.platform == "darwin" else "cron" if shutil.which("crontab") else "none"
    if sched == "session" and (not a.hours or a.hours > 167):
        print("CronCreate lives at most 7 days — time limit set to 167 h")
        a.hours = 167
    every = norm_every(max(1, a.every))
    if every != a.every:
        print(f"cron can't express an interval of {a.every} min exactly — using {every} min")
    if sched in ("launchd", "cron"):
        sec = [k for k in SECRET_ENV if os.environ.get(k)]
        if sec:
            print(f"signed in via {', '.join(sec)}: launchd/cron won't get this variable (I don't write secrets "
                  "into the scheduler file). Use --scheduler session or sign in to `claude` via login.")
            return 1
        home = Path.home()
        if sys.platform == "darwin" and any(root.is_relative_to(home / d) for d in ("Desktop", "Documents", "Downloads")):
            print("WARNING: the game is in Desktop/Documents/Downloads — macOS may not let the launchd process in there. "
                  "Safer: ~/Games/… or --scheduler session")

    now = datetime.now()
    st = {
        "active": True, "goal": a.goal, "brief": a.brief.strip(), "mode": a.mode, "model": a.model,
        "every": every, "tick_minutes": a.tick_minutes, "tick_budget": a.tick_budget,
        "max_ticks": a.max_ticks, "started": ts(now),
        "deadline": ts(now + timedelta(hours=a.hours)) if a.hours else None,
        "scheduler": sched, "label": label(root), "claude": claude,
        "env": {k: os.environ[k] for k in KEEP_ENV if os.environ.get(k)},
        "ticks": 0, "fails": 0, "idle": 0, "cost": 0.0, "sleep_until": None, "prompt": a.prompt or "",
    }
    if sched == "session":
        st["cron"] = cron_expr(every)

    if not a.no_preflight:
        print("preflight: claude -p in the same permission mode…", flush=True)
        p = None
        try:
            p = subprocess.run(claude_cmd(st, "Answer with one word: OK", preflight=True), cwd=root,
                               env=run_env(st, minimal=sched in ("launchd", "cron")),
                               capture_output=True, text=True, timeout=240)
            out = parse_out_text(p.stdout)
        except subprocess.TimeoutExpired:
            out = {"is_error": True, "result": "timeout 240 s"}
        if out.get("is_error") or p is None or p.returncode != 0:
            print(f"claude -p doesn't work: {cell(out.get('result') or (p.stderr if p else ''), 300)}")
            if a.mode == "auto":
                print("if auto mode isn't available on this account — retry with --mode bypass (with the user's consent)")
            return 1
        print("  ok")

    d = ap_dir(root)
    (d / "logs").mkdir(parents=True, exist_ok=True)
    for f in ("STOP", "REPORT.md"):
        (d / f).unlink(missing_ok=True)
    rv = d / "REVIEW.md"
    if not rv.is_file():
        rv.write_text("# Decided on the user's behalf — for review\n\nThe autopilot writes every taste decision here.\n\n"
                      "| phase | decided | alternative | why | commit |\n|---|---|---|---|---|\n",
                      encoding="utf-8")
    ensure_ignored(root)
    if studio.in_repo(root):
        paths = [".gitignore", f"{AP}/REVIEW.md"]
        studio.git(root, "add", "--", *paths)
        studio.git(root, "commit", "-q", "-m", f"autopilot: start — {a.goal}, {a.hours or '∞'} h", "--", *paths)

    err = install(root, st)
    if err:
        print(err)
        return 1
    if sys.platform == "darwin" and not a.no_caffeinate and shutil.which("caffeinate"):
        secs = int(a.hours * 3600) if a.hours else 7 * 24 * 3600
        st["caffeinate_pid"] = subprocess.Popen(["caffeinate", "-i", "-s", "-t", str(secs)], start_new_session=True,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).pid
    save(root, st)
    log(root, f"| — | {now:%d.%m %H:%M} | | {phase_now(root)} | | | | START | goal {a.goal}, "
              f"{a.hours or '∞'} h, every {every} min, {sched}, {a.mode} |")

    print(f"autopilot started: {root.name}")
    print(f"  task: {GOALS[a.goal][1]}")
    print(f"  until: {st['deadline'] or 'no time limit'}; at most {a.max_ticks} ticks; a tick up to {a.tick_minutes} min")
    if sched == "session":
        print(f"  Do it now: 1) CronCreate — cron \"{st['cron']}\", recurring: true, prompt — the text between the lines;")
        print("  2) the first tick right away — the command from the prompt, Bash with run_in_background: true.")
        print("-" * 60)
        print(session_prompt(root))
        print("-" * 60)
        print("  Don't close the session and don't work in it: CronCreate jobs fire while it is open and idle.")
    elif sched == "none":
        print("  no scheduler: run the ticks yourself — " + " ".join(shlex.quote(x) for x in tick_argv(root)[:-1]))
    else:
        print(f"  scheduler: {sched} ({st['label']}), every {every} min; first tick — now")
    if sys.platform == "darwin":
        print("  The Mac must be on and awake (lid open or an external monitor); caffeinate keeps it from idling")
    print(f"  watch: autopilot.py status · log {AP}/LOG.md · stop: autopilot.py stop")
    return 0


def changed_files(root: Path, before: str) -> list[str]:
    if before:
        files = studio.git(root, "diff", "--name-only", before).stdout.split("\n")
    else:
        files = studio.git(root, "ls-files").stdout.split("\n")
    files += studio.git(root, "ls-files", "--others", "--exclude-standard").stdout.split("\n")
    return sorted({f for f in files if f.strip()})


def cmd_tick(a) -> int:
    root = find_root(a.root)
    st = load(root)
    if not st.get("active"):
        if a.from_scheduler and st:
            uninstall(st)
        print("autopilot is not active")
        print("NEXT: stop")
        return 0
    fh = try_lock(root)
    if fh is None:
        print("a tick is still running")
        print("NEXT: wait")
        return 0
    try:
        return run_tick(root, st, fh)
    finally:
        if read_lock(root).get("runner_pid") == os.getpid():
            (ap_dir(root) / "lock.json").unlink(missing_ok=True)
        fh.close()


def run_tick(root: Path, st: dict, fh) -> int:
    stop = ap_dir(root) / "STOP"
    dl = parse_ts(st.get("deadline"))
    if stop.is_file():
        finish(root, st, stop.read_text(encoding="utf-8").strip() or "STOP")
        return 0
    if dl and datetime.now() >= dl:
        finish(root, st, "time ran out")
        return 0
    if st["ticks"] >= st["max_ticks"]:
        finish(root, st, f"tick limit ({st['max_ticks']})")
        return 0
    su = parse_ts(st.get("sleep_until"))
    if su and datetime.now() < su:
        print(f"paused until {su:%H:%M} (usage limit or a streak of errors)")
        print("NEXT: wait")
        return 0
    prev = read_lock(root)
    if is_tick_agent(prev.get("claude_pid")):  # the previous tick's runner died, the agent is alive
        age = (datetime.now() - (parse_ts(prev.get("started")) or datetime.now())).total_seconds() / 60
        if age < st["tick_minutes"] + 15:
            print(f"tick {prev.get('tick')} is still running ({age:.0f} min, no runner)")
            print("NEXT: wait")
            return 0
        kill_group(prev["claude_pid"], signal.SIGKILL)

    n = st["ticks"] + 1
    started = datetime.now()
    before, ph_before = head(root), phase_now(root)
    closed_before = goal_closed(root, st["goal"])
    prompt = st.get("prompt") or build_prompt(root, st)
    out_p = ap_dir(root) / "logs" / f"tick-{n:03d}.json"
    err_p = out_p.with_suffix(".err")
    out_p.parent.mkdir(parents=True, exist_ok=True)
    outcome, rc, res, err_text = "ok", 0, {}, ""
    try:
        with out_p.open("w") as fo, err_p.open("w") as fe:
            proc = subprocess.Popen(claude_cmd(st, prompt), cwd=root, stdout=fo, stderr=fe, stdin=subprocess.DEVNULL,
                                    env=run_env(st), start_new_session=True)
            (ap_dir(root) / "lock.json").write_text(json.dumps({
                "runner_pid": os.getpid(), "claude_pid": proc.pid, "tick": n, "started": ts(started)}),
                encoding="utf-8")

            def on_term(sig, frame):  # the session was closed or stop --now — don't leave the agent orphaned
                kill_group(proc.pid)
                raise SystemExit(1)
            signal.signal(signal.SIGTERM, on_term)
            signal.signal(signal.SIGHUP, on_term)
            if sys.platform == "darwin" and shutil.which("caffeinate"):
                subprocess.Popen(["caffeinate", "-i", "-s", "-w", str(proc.pid)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                rc = proc.wait(timeout=st["tick_minutes"] * 60)
            except subprocess.TimeoutExpired:
                outcome, rc = "timeout", -1
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    kill_group(proc.pid, sig)
                    try:
                        proc.wait(timeout=20)
                        break
                    except subprocess.TimeoutExpired:
                        continue
        res = parse_out_text(out_p.read_text(encoding="utf-8", errors="replace"))
        err_text = err_p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        outcome, rc, res = "error", -1, {"is_error": True, "result": f"claude failed to start: {e}"}
    if err_p.is_file() and err_p.stat().st_size == 0:
        err_p.unlink()

    text = str(res.get("result") or "")
    subtype = str(res.get("subtype") or "")
    failed = bool(res.get("is_error")) or rc != 0
    until = limit_until(text + "\n" + err_text[-2000:]) if failed else None
    if outcome == "ok":
        if until:
            outcome = "limit"
        elif "max_budget" in subtype:
            outcome = "budget"
        elif "max_turns" in subtype:
            outcome = "turns"
        elif failed:
            outcome = "error"
    if not text and outcome != "ok":
        text = subtype or err_text.strip()[-200:]

    game = [f for f in changed_files(root, before) if not f.startswith(AP + "/") and f != f"{ST}/STATE.md"]
    if studio.in_repo(root) and studio.git(root, "status", "--porcelain").stdout.strip():
        studio.git(root, "add", "-A")
        studio.git(root, "commit", "-q", "-m", f"autopilot: tick {n} — uncommitted after the tick")
    after = head(root)
    commits = 0
    if after and after != before:
        commits = int(studio.git(root, "rev-list", "--count", f"{before}..{after}" if before else after).stdout.strip() or 0)

    st = load(root) or st  # stop may have changed the state while the tick was running
    cost = float(res.get("total_cost_usd") or 0)
    st["cost"] = round(st.get("cost", 0.0) + cost, 4)
    if outcome == "limit":
        st["sleep_until"] = ts(until)
    else:
        st["ticks"] = n
        bad = outcome in ("error", "timeout") and not game
        st["fails"] = st.get("fails", 0) + 1 if bad else 0
        st["idle"] = 0 if game else st.get("idle", 0) + 1
        st["sleep_until"] = ts(datetime.now() + timedelta(minutes=5 * st["fails"])) if bad else None
    st["last"] = {"tick": n, "outcome": outcome, "changed": len(game), "commits": commits,
                  "session": res.get("session_id"), "at": ts(), "result": text[:300]}
    save(root, st)
    mins = (datetime.now() - started).total_seconds() / 60
    log(root, f"| {n} | {started:%d.%m %H:%M} | {mins:.0f} | {ph_before}→{phase_now(root)} | {len(game)} | {commits} | "
              f"{cost:.2f} | {outcome} | {cell(text)} |")
    print(f"tick {n}: {outcome}, game files changed {len(game)}, commits {commits}, {mins:.0f} min")

    if not st.get("active"):
        print("NEXT: stop")
    elif stop.is_file():
        finish(root, st, stop.read_text(encoding="utf-8").strip() or "STOP")
    elif closed_before and goal_closed(root, st["goal"]):
        finish(root, st, "goal closed: all gates of the goal's phases")
    elif st["fails"] >= 3:
        finish(root, st, f"3 ticks in a row with an error — see {AP}/logs/tick-{n:03d}.json")
    elif st["idle"] >= 3:
        finish(root, st, "3 ticks in a row without changes to the game — stuck, a human is needed")
    elif st["ticks"] >= st["max_ticks"]:
        finish(root, st, f"tick limit ({st['max_ticks']})")
    elif dl and datetime.now() >= dl:
        finish(root, st, "time ran out")
    else:
        print("NEXT: now" if outcome in ("ok", "budget", "turns") else "NEXT: wait")
    return 0


def cmd_status(a) -> int:
    root = find_root(a.root)
    st = load(root)
    if not st:
        print("the autopilot has never run in this project")
        return 0
    lk = read_lock(root)
    running = tick_running(root)
    state = "ACTIVE" if st.get("active") else f"stopped {st.get('stopped_at', '')}: {st.get('reason', '')}"
    print(f"autopilot: {state}")
    print(f"  task: {GOALS[st['goal']][1]}")
    dl = parse_ts(st.get("deadline"))
    left = f", {max(0, (dl - datetime.now()).total_seconds() / 3600):.1f} h left" if dl and st.get("active") else ""
    sched = "CronCreate in the session" if st["scheduler"] == "session" else st["scheduler"]
    print(f"  started {st['started']}{left}; ticks {st['ticks']}/{st['max_ticks']}; $ {st.get('cost', 0):.2f}; "
          f"mode {st['mode']}; {sched}")
    if running:
        print(f"  tick {lk.get('tick', '?')} is running since {str(lk.get('started', ''))[11:16]} — "
              "don't edit the project in parallel")
    su = parse_ts(st.get("sleep_until"))
    if st.get("active") and su and su > datetime.now():
        print(f"  paused until {su:%H:%M} (usage limit or a streak of errors)")
    if st.get("active") and st["scheduler"] == "session":
        print(f"  CronCreate job: cron \"{st.get('cron')}\" — the session must stay open; if it's not in CronList — "
              "autopilot.py prompt --cron and CronCreate again")
    elif st.get("active") and st["scheduler"] != "none" and not installed(st):
        print("  ! the scheduler is not installed — ticks won't run. autopilot.py stop, then start")
    if st.get("fails") or st.get("idle"):
        print(f"  in a row: errors {st.get('fails', 0)}, without changes to the game {st.get('idle', 0)} (stops at 3)")
    rows = log_rows(root)
    if rows:
        print("  last ticks:")
        for l in rows[-5:]:
            print("    " + l[:170])
    rv = review_rows(root)
    if rv:
        print(f"  decided on the user's behalf: {len(rv)} ({AP}/REVIEW.md)")
    if (ap_dir(root) / "REPORT.md").is_file():
        print(f"  report: {AP}/REPORT.md")
    return 0


def cmd_stop(a) -> int:
    root = find_root(a.root)
    st = load(root)
    if not st.get("active"):
        if st:
            uninstall(st)
        print("autopilot is not active")
        print("NEXT: stop")
        return 0
    reason = a.reason or "stopped by the user"
    if tick_running(root):
        if not a.now:
            (ap_dir(root) / "STOP").write_text(reason + "\n", encoding="utf-8")
            print(f"the current tick will finish (up to {st['tick_minutes']} min), commit, and the autopilot will stop. "
                  "Immediately — stop --now")
            return 0
        lk = read_lock(root)
        if is_tick_agent(lk.get("claude_pid")):
            kill_group(lk["claude_pid"])
        rp = lk.get("runner_pid")
        if rp and "autopilot.py" in proc_cmd(rp):
            try:
                os.kill(int(rp), signal.SIGTERM)
            except OSError:
                pass
    finish(root, st, reason)
    return 0


def cmd_prompt(a) -> int:
    root = find_root(a.root)
    st = load(root)
    if not st:
        print("the autopilot has never run — the prompt depends on the start settings")
        return 1
    if a.cron:
        print(f"cron: {st.get('cron') or cron_expr(st['every'])}  (recurring: true)\n{'-' * 60}")
        print(session_prompt(root))
        return 0
    print(st.get("prompt") or build_prompt(root, st))
    return 0


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description="studioigor autopilot — independent development on a schedule")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default="", help="game root (searched upward by default)")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("start", parents=[common], help="start (only after the user's consent)")
    p.add_argument("--goal", choices=list(GOALS), default="slice")
    p.add_argument("--hours", type=float, default=10, help="time limit, 0 — no limit")
    p.add_argument("--every", type=int, default=15, help="how often the schedule runs a tick, min")
    p.add_argument("--max-ticks", type=int, default=60)
    p.add_argument("--tick-minutes", type=int, default=90, help="ceiling for one tick, min")
    p.add_argument("--tick-budget", type=float, default=0, help="$ ceiling per tick (--max-budget-usd), 0 — none")
    p.add_argument("--mode", choices=list(MODES), default="auto", help="claude -p permission mode")
    p.add_argument("--model", default="")
    p.add_argument("--brief", default="", help="the user's brief, verbatim")
    p.add_argument("--scheduler", choices=["session", "system", "none"], default="session",
                   help="session — this session's CronCreate; system — launchd/cron (the terminal can be closed)")
    p.add_argument("--no-caffeinate", action="store_true")
    p.add_argument("--no-preflight", action="store_true")
    p.add_argument("--prompt", default="", help=argparse.SUPPRESS)  # debug: a custom tick prompt

    p = sp.add_parser("tick", parents=[common], help="one tick (run by the schedule)")
    p.add_argument("--from-scheduler", action="store_true", help=argparse.SUPPRESS)
    sp.add_parser("status", parents=[common], help="what the autopilot is doing now")
    p = sp.add_parser("stop", parents=[common], help="stop: the current tick finishes, --now — immediately")
    p.add_argument("--reason", default="")
    p.add_argument("--now", action="store_true", help="abort the running tick")
    p = sp.add_parser("prompt", parents=[common], help="the next tick's prompt; --cron — for CronCreate")
    p.add_argument("--cron", action="store_true")

    a = ap.parse_args()
    if os.name == "nt":
        print("the autopilot runs on macOS and Linux; on Windows — via WSL")
        return 1
    return {"start": cmd_start, "tick": cmd_tick, "status": cmd_status, "stop": cmd_stop,
            "prompt": cmd_prompt}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
