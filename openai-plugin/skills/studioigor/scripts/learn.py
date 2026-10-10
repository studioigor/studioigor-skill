#!/usr/bin/env python3
"""The skill learns — but into its own user-choices/ folder, without touching the skill itself.

Anything the agent found that works better than what the skill says (a technique, a tool, a
process trick, a fix) first becomes a PROPOSAL. The user decides what to keep. Accepted items
live in user-choices/accepted/ and in INDEX.md, and `studio.py status` shows them in the right
phase. SKILL.md, references/ and scripts/ never change — so a skill update doesn't wipe what was
learned, and what was learned doesn't break the skill.

A game's own choices never become global rules: games differ. `prefer` writes into the game's
.studioigor/PREFERENCES.md by default, and the next game starts clean. Only a rule about how to
work with the user in any game goes to user-choices/preferences.md, and only with --global.

Commands:
  propose --title "…" --phase N|all --kind technique|tool|process|fix --what "…"
          --when "…" --why "…" [--source "…"] [--force]
  list [--all]                      awaiting a decision (and totals with --all)
  show <ID>
  accept <ID>… [--note "…"]         save into the skill (accepted/ + INDEX.md)
  reject <ID>… --why "…"            reject (rejected/ — so it isn't proposed again)
  prefer "…" [--phase N|all] [--global]
                                    a lasting user preference, in force immediately: this game's
                                    .studioigor/PREFERENCES.md; --global — a rule about how to
                                    work in any game (user-choices/preferences.md)
  unprefer "<part of the text>" [--project | --global]
                                    remove a preference (the user took it back)
  for-phase N                       what to take into account in phase N: preferences + accepted
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
ST = ".studioigor"
PREF = re.compile(r"^- \((.*?), P?(.*?)\) (.*)$")
GLOBAL_PREFS_HDR = ("# User preferences — all games\n\n"
                    "Rules about how to work with the user in any game, in their own words "
                    "(learn.py prefer --global).\nA game's taste is not here: it stays in "
                    "<game>/.studioigor/PREFERENCES.md.\n\n")
PROJECT_PREFS_HDR = ("# Preferences — this game only\n\n"
                     "The user's choices for this game, in their own words (learn.py prefer). "
                     "They beat the global\nones in <skill>/user-choices/ and don't carry over "
                     "to other games.\n\n")

README = """# user-choices — what the skill has learned from this user

Only `scripts/learn.py` writes this folder. The skill itself (SKILL.md, references/,
scripts/) doesn't change: learned items live here, on top of it.

- `INDEX.md` — accepted improvements, one line each. Read at the start of work.
  If an accepted item contradicts the skill's general instructions, the accepted item
  wins: the user approved it.
- `preferences.md` — rules about how to work with the user in any game, in their own words.
  A game's taste is not here: it stays in `<game>/.studioigor/PREFERENCES.md`.
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
        (UC / "preferences.md").write_text(GLOBAL_PREFS_HDR, encoding="utf-8")


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


def project_root(start: str | None = None) -> Path | None:
    p = Path(start).expanduser().resolve() if start else Path.cwd().resolve()
    for d in [p, *p.parents]:
        if (d / ST).is_dir():
            return d
    return None


def pref_files(root: Path | None) -> list[tuple[str, Path]]:
    """(scope, file); this game's first — it beats the global one."""
    out = [("this game", root / ST / "PREFERENCES.md")] if root else []
    return out + [("all games", UC / "preferences.md")]


def prefs(p: Path) -> list[tuple[str, str, str]]:
    """(line, phase, text) of every preference in the file."""
    return [(line, m.group(2), m.group(3)) for line in read(p).splitlines() if (m := PREF.match(line))]


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
        pr = " · ".join(f"{s}: {len(prefs(p))}" for s, p in pref_files(project_root(a.root)))
        print(f"\naccepted: {acc} · rejected: {rej} · preferences — {pr}")
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
    text = " ".join(a.text.split())
    if a.all_games:
        ensure()
        dst, where = UC / "preferences.md", "for all games"
    else:
        root = project_root(a.root)
        if not root:
            print(f"no {ST}/ found upward from {Path(a.root or '.').resolve()} — cd into the game or "
                  f"pass --root. A game's choice is saved only into that game; --global is for a rule "
                  f"about how to work with the user in any game.")
            return 1
        dst, where = root / ST / "PREFERENCES.md", f"for this game only ({root.name}/{ST}/PREFERENCES.md)"
        if not dst.exists():
            dst.write_text(PROJECT_PREFS_HDR, encoding="utf-8")
    if any(t.lower() == text.lower() for _, _, t in prefs(dst)):
        print(f"already saved {where}")
        return 0
    with dst.open("a", encoding="utf-8") as fh:
        fh.write(f"- ({date.today().isoformat()}, {ptag(a.phase)}) {text}\n")
    print(f"preference saved {where}")
    return 0


def cmd_unprefer(a) -> int:
    root = project_root(a.root)
    if a.project and not root:
        print(f"no {ST}/ found upward from {Path(a.root or '.').resolve()} — cd into the game or pass --root")
        return 1
    files = [(s, p) for s, p in pref_files(root)
             if not (a.project and s != "this game") and not (a.all_games and s != "all games")]
    want = " ".join(a.text.split()).lower()
    every = [(s, p, line, t) for s, p in files for line, _, t in prefs(p)]
    hits = [h for h in every if want in h[3].lower()]
    hits = [h for h in hits if h[3].lower() == want] or hits
    if len(hits) != 1:
        print("several preferences match — give more of the text or --project / --global:" if hits
              else f"no preference contains \"{a.text}\". There are:")
        for s, _, line, _ in hits or every:
            print(f"  [{s}] {line[2:]}")
        return 1
    s, p, line, _ = hits[0]
    lines = read(p).splitlines()
    lines.remove(line)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"removed [{s}]: {line[2:]}")
    return 0


def ptag(phase: str) -> str:
    """P1, P6 … or `all` for a phase-independent item."""
    phase = str(phase).strip()
    return "all" if phase in ("all", "*", "") else f"P{phase}"


def for_phase(n: str, root: Path | None = None) -> list[str]:
    """This game's preferences, then the global ones, then accepted improvements."""
    out = [f"[{s}] {t}" for s, p in pref_files(root) for _, ph, t in prefs(p) if phase_matches(ph, n)]
    for line in read(UC / "INDEX.md").splitlines():
        m = re.match(r"^- \[(.*?)\] \(P?(.*?)\) (.*)$", line)
        if m and phase_matches(m.group(2), n):
            out.append(f"[{m.group(1)}] {m.group(3).split(' → ')[0]}")
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
    items = for_phase(str(a.n), project_root(a.root))
    if not items:
        print(f"nothing learned for phase {a.n}")
        return 0
    print(f"take into account in phase {a.n} (approved by the user, takes priority over the general "
          f"instructions; [this game] beats [all games]):")
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
    ap.add_argument("--root", default="", help="game root for preferences (searched upward by default)")
    # --root is also accepted after the subcommand; SUPPRESS does not overwrite a value given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
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
    p = sp.add_parser("list", parents=[common])
    p.add_argument("--all", action="store_true")
    p = sp.add_parser("show")
    p.add_argument("id")
    p = sp.add_parser("accept")
    p.add_argument("ids", nargs="+")
    p.add_argument("--note", default="")
    p = sp.add_parser("reject")
    p.add_argument("ids", nargs="+")
    p.add_argument("--why", default="")
    p = sp.add_parser("prefer", parents=[common])
    p.add_argument("text")
    p.add_argument("--phase", default="all")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--project", action="store_true", help="this game only (default)")
    g.add_argument("--global", dest="all_games", action="store_true",
                   help="a rule about how to work with the user in any game — never a game's taste")
    p = sp.add_parser("unprefer", parents=[common])
    p.add_argument("text", help="part of the preference text")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--project", action="store_true", help="look only in this game")
    g.add_argument("--global", dest="all_games", action="store_true", help="look only in the global ones")
    p = sp.add_parser("for-phase", parents=[common])
    p.add_argument("n")
    p = sp.add_parser("radar")
    p.add_argument("--done", default="")
    a = ap.parse_args()
    return {"propose": cmd_propose, "list": cmd_list, "show": cmd_show, "accept": cmd_accept,
            "reject": cmd_reject, "prefer": cmd_prefer, "unprefer": cmd_unprefer,
            "for-phase": cmd_for_phase, "radar": cmd_radar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
