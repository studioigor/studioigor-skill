#!/usr/bin/env python3
"""The skill learns — but into its own user-choices/ folder, without touching the skill itself.

Anything the agent found that works better than what the skill says (a technique, a tool, a
process trick, a fix) first becomes a PROPOSAL. The user decides what to keep. Accepted items
live in user-choices/accepted/ and in INDEX.md, and `studio.py status` shows them in the right
phase. SKILL.md, references/ and scripts/ never change — so a skill update doesn't wipe what was
learned, and what was learned doesn't break the skill.

Commands:
  propose --title "…" --phase N|all --kind technique|tool|process|fix --what "…"
          --when "…" --why "…" [--source "…"] [--force]
  list [--all]                      awaiting a decision (and totals with --all)
  show <ID>
  accept <ID>… [--note "…"]         save into the skill (accepted/ + INDEX.md)
  reject <ID>… --why "…"            reject (rejected/ — so it isn't proposed again)
  prefer "…" [--phase N|all]        a lasting user preference (in force immediately)
  for-phase N                       what to take into account in phase N: accepted + preferences
  radar [--done "summary"]          is the tech radar due (every 30 days); --done — mark it done

stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

UC = Path(os.environ.get("STUDIOIGOR_UC") or Path(__file__).resolve().parent.parent / "user-choices")
DIRS = ("proposals", "accepted", "rejected")
RADAR_DAYS = 30

README = """# user-choices — what the skill has learned from this user

Only `scripts/learn.py` writes this folder. The skill itself (SKILL.md, references/,
scripts/) doesn't change: learned items live here, on top of it.

- `INDEX.md` — accepted improvements, one line each. Read at the start of work.
  If an accepted item contradicts the skill's general instructions, the accepted item
  wins: the user approved it.
- `preferences.md` — the user's lasting preferences, in their own words.
- `accepted/` — full text of accepted improvements.
- `proposals/` — awaiting the user's decision.
- `rejected/` — rejected, with the reason, so they aren't proposed again.
- `radar.md` — when the tech radar ran and what it found.
"""


def ensure() -> None:
    UC.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (UC / d).mkdir(exist_ok=True)
    if not (UC / "README.md").exists():
        (UC / "README.md").write_text(README, encoding="utf-8")
    if not (UC / "INDEX.md").exists():
        (UC / "INDEX.md").write_text("# Accepted improvements\n\nRead at the start of work. "
                                     "Format: `- [ID] (P1) title — when to apply`.\n\n",
                                     encoding="utf-8")
    if not (UC / "preferences.md").exists():
        (UC / "preferences.md").write_text("# User preferences\n\n"
                                           "What the user said themselves — in force immediately.\n\n",
                                           encoding="utf-8")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def field(text: str, name: str) -> str:
    m = re.search(rf"^{name}:[ \t]*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def title_of(text: str) -> str:
    m = re.search(r"^#\s+(.*)$", text, re.M)
    return m.group(1).strip() if m else "?"


def section(text: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def words(s: str) -> set[str]:
    # letters/digits of any script, 4+ long (not only ASCII: proposals may be written in any language)
    return {w for w in re.findall(r"[^\W_]{4,}", s.lower())}


def all_items(where: tuple[str, ...] = DIRS) -> list[tuple[str, Path]]:
    out = []
    for d in where:
        for p in sorted((UC / d).glob("*.md")):
            out.append((d, p))
    return out


def find(pid: str) -> tuple[str, Path] | None:
    for d, p in all_items():
        if p.name.startswith(pid):
            return d, p
    return None


def slug(s: str) -> str:
    s = re.sub(r"[\W_]+", "-", s.lower()).strip("-")
    return s[:40] or "item"


def new_id() -> str:
    today = date.today().strftime("%Y%m%d")
    n = len([p for _, p in all_items() if p.name.startswith(f"P-{today}")]) + 1
    return f"P-{today}-{n:02d}"


def phase_matches(ph: str, n: str) -> bool:
    ph = ph.lower()
    if ph in ("all", "*", ""):
        return True
    return n in re.findall(r"\d+", ph)


# ------------------------------------------------------------------ commands

def cmd_propose(a) -> int:
    ensure()
    w = words(a.title + " " + a.what)
    if not a.force:
        for d, p in all_items():
            t = read(p)
            ow = words(title_of(t) + " " + section(t, "What"))
            if w and ow and len(w & ow) / max(1, min(len(w), len(ow))) >= 0.6:
                where = {"proposals": "already proposed", "accepted": "already accepted",
                         "rejected": "already rejected"}[d]
                print(f"looks {where}: {p.stem} — {title_of(t)}. Not duplicating (--force if it's something else).")
                return 0
    pid = new_id()
    body = (f"# {a.title}\n\nID: {pid}\nDATE: {date.today().isoformat()}\nPHASE: {a.phase}\n"
            f"KIND: {a.kind}\nSOURCE: {a.source or '—'}\nSTATUS: pending\n\n"
            f"## What\n{a.what.strip()}\n\n## When to apply\n{a.when.strip()}\n\n"
            f"## Why\n{a.why.strip()}\n")
    (UC / "proposals" / f"{pid}-{slug(a.title)}.md").write_text(body, encoding="utf-8")
    pend = len(list((UC / "proposals").glob("*.md")))
    print(f"proposal {pid} written ({pend} awaiting a decision). Ask the user at the end of the "
          f"phase or session, in one question.")
    return 0


def cmd_list(a) -> int:
    ensure()
    pend = all_items(("proposals",))
    if not pend:
        print("no proposals awaiting a decision")
    else:
        print(f"awaiting a decision ({len(pend)}):")
        for _, p in pend:
            t = read(p)
            print(f"  {field(t, 'ID')}  P{field(t, 'PHASE'):<4} [{field(t, 'KIND')}] {title_of(t)}")
            print(f"      {section(t, 'What')[:150]}")
    if a.all:
        acc = len(all_items(("accepted",)))
        rej = len(all_items(("rejected",)))
        print(f"\naccepted: {acc} · rejected: {rej} · preferences: "
              f"{len(re.findall(r'^- ', read(UC / 'preferences.md'), re.M))}")
    return 0


def cmd_show(a) -> int:
    hit = find(a.id)
    if not hit:
        print(f"not found: {a.id}")
        return 1
    print(read(hit[1]))
    return 0


def cmd_accept(a) -> int:
    ensure()
    idx = UC / "INDEX.md"
    for pid in a.ids:
        hit = find(pid)
        if not hit or hit[0] != "proposals":
            print(f"{pid}: not found among pending proposals")
            continue
        _, p = hit
        t = read(p).replace("STATUS: pending", f"STATUS: accepted {date.today().isoformat()}")
        if a.note:
            t += f"\n## User's note\n{a.note.strip()}\n"
        dst = UC / "accepted" / p.name
        dst.write_text(t, encoding="utf-8")
        p.unlink()
        when = section(t, "When to apply").splitlines()[0][:120] if section(t, "When to apply") else ""
        line = f"- [{field(t, 'ID')}] ({ptag(field(t, 'PHASE'))}) {title_of(t)} — {when} → accepted/{dst.name}\n"
        with idx.open("a", encoding="utf-8") as fh:
            fh.write(line)
        print(f"{pid}: accepted and saved into the skill")
    return 0


def cmd_reject(a) -> int:
    ensure()
    for pid in a.ids:
        hit = find(pid)
        if not hit or hit[0] != "proposals":
            print(f"{pid}: not found among pending proposals")
            continue
        _, p = hit
        t = read(p).replace("STATUS: pending", f"STATUS: rejected {date.today().isoformat()}")
        t += f"\n## Why rejected\n{a.why.strip() or '—'}\n"
        (UC / "rejected" / p.name).write_text(t, encoding="utf-8")
        p.unlink()
        print(f"{pid}: rejected")
    return 0


def cmd_prefer(a) -> int:
    ensure()
    with (UC / "preferences.md").open("a", encoding="utf-8") as fh:
        fh.write(f"- ({date.today().isoformat()}, {ptag(a.phase)}) {a.text.strip()}\n")
    print("preference saved")
    return 0


def ptag(phase: str) -> str:
    """P1, P6 … or `all` for a phase-independent item."""
    phase = str(phase).strip()
    return "all" if phase in ("all", "*", "") else f"P{phase}"


def for_phase(n: str) -> list[str]:
    if not UC.is_dir():
        return []
    out = []
    for line in read(UC / "INDEX.md").splitlines():
        m = re.match(r"^- \[(.*?)\] \(P?(.*?)\) (.*)$", line)
        if m and phase_matches(m.group(2), n):
            out.append(f"[{m.group(1)}] {m.group(3).split(' → ')[0]}")
    for line in read(UC / "preferences.md").splitlines():
        m = re.match(r"^- \((.*?), P?(.*?)\) (.*)$", line)
        if m and phase_matches(m.group(2), n):
            out.append(f"[preference] {m.group(3)}")
    return out


def pending_count() -> int:
    return len(list((UC / "proposals").glob("*.md"))) if (UC / "proposals").is_dir() else 0


def radar_due() -> tuple[bool, str]:
    t = read(UC / "radar.md")
    dates = re.findall(r"^## (\d{4}-\d{2}-\d{2})", t, re.M)
    if not dates:
        return True, "never"
    last = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    return (date.today() - last).days >= RADAR_DAYS, dates[-1]


def cmd_for_phase(a) -> int:
    items = for_phase(str(a.n))
    if not items:
        print(f"nothing learned for phase {a.n}")
        return 0
    print(f"take into account in phase {a.n} (accepted by the user, takes priority over the general instructions):")
    for i in items:
        print(f"  - {i}")
    return 0


def cmd_radar(a) -> int:
    ensure()
    if a.done:
        with (UC / "radar.md").open("a", encoding="utf-8") as fh:
            if not read(UC / "radar.md"):
                fh.write("# Tech radar\n\nEvery ~30 days: new engine versions, MCP, asset generators, "
                         "Claude Code capabilities. Findings become proposals via propose.\n\n")
            fh.write(f"## {date.today().isoformat()}\n{a.done.strip()}\n\n")
        print("tech radar marked done")
        return 0
    due, last = radar_due()
    print(f"tech radar: {'DUE' if due else 'not needed'} (last: {last})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="studioigor — learned items in user-choices/")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("propose")
    p.add_argument("--title", required=True)
    p.add_argument("--phase", default="all")
    p.add_argument("--kind", default="technique", choices=["technique", "tool", "process", "fix"])
    p.add_argument("--what", required=True)
    p.add_argument("--when", required=True)
    p.add_argument("--why", required=True)
    p.add_argument("--source", default="")
    p.add_argument("--force", action="store_true")
    p = sp.add_parser("list")
    p.add_argument("--all", action="store_true")
    p = sp.add_parser("show")
    p.add_argument("id")
    p = sp.add_parser("accept")
    p.add_argument("ids", nargs="+")
    p.add_argument("--note", default="")
    p = sp.add_parser("reject")
    p.add_argument("ids", nargs="+")
    p.add_argument("--why", default="")
    p = sp.add_parser("prefer")
    p.add_argument("text")
    p.add_argument("--phase", default="all")
    p = sp.add_parser("for-phase")
    p.add_argument("n")
    p = sp.add_parser("radar")
    p.add_argument("--done", default="")
    a = ap.parse_args()
    return {"propose": cmd_propose, "list": cmd_list, "show": cmd_show, "accept": cmd_accept,
            "reject": cmd_reject, "prefer": cmd_prefer, "for-phase": cmd_for_phase,
            "radar": cmd_radar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
