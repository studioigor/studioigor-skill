#!/usr/bin/env python3
"""Reveal the key of a gauntlet round — only after the verdict (references/gauntlet.md).

Won't open key.json until <round>/verdict.md has a `WINNER: A|B|TIE` line and exactly
one `GAP: …`. That is the whole point: a verdict written before the answer can't be
fitted to the answer. Then appends the reveal to verdict.md, writes outcome.json
and a row to the target's log <target>/LEDGER.md.

Usage:
  reveal.py .studioigor/gauntlet/<target>/rounds/03
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

WINNER = re.compile(r"^[ \t]*(?:\*\*)?WINNER(?:\*\*)?:[ \t]*(A|B|TIE)\b", re.I | re.M)
GAP = re.compile(r"^[ \t]*(?:\*\*)?GAP(?:\*\*)?:[ \t]*(\S.*?)[ \t]*$", re.I | re.M)
LENS = re.compile(r"lens:[ \t]*([^\n|—]+)", re.I)


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    if len(sys.argv) != 2:
        print("usage: reveal.py <round folder>", file=sys.stderr)
        return 2
    rd = Path(sys.argv[1])
    verdict = rd / "verdict.md"
    key = rd / "ab" / "key.json"
    if not verdict.is_file():
        print(f"error: no {verdict}. Verdict first, then the key.", file=sys.stderr)
        return 1
    if not key.is_file():
        print(f"error: no {key} — the pair wasn't built (ab.py).", file=sys.stderr)
        return 1
    text = verdict.read_text(encoding="utf-8")
    win = WINNER.search(text)
    gaps = GAP.findall(text)
    if not win:
        print("error: verdict.md has no `WINNER: A` (or B, or TIE). The choice is locked in before the key.",
              file=sys.stderr)
        return 1
    if len(gaps) != 1:
        print("error: exactly one `GAP: …` is needed — the single biggest gap, not a list.",
              file=sys.stderr)
        return 1

    picked, gap = win.group(1).upper(), gaps[0].strip()
    k = json.loads(key.read_text(encoding="utf-8"))
    if picked == "TIE":
        outcome = "TIE"
    else:
        outcome = "BAR" if k.get(picked) == "reference" else "OURS"
    lens_m = LENS.search(text)
    lens = lens_m.group(1).strip() if lens_m else ""

    with verdict.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## Reveal\n- A = {k.get('A')}, B = {k.get('B')}\n"
                 f"- picked {picked} → winner: **{outcome}**\n")
        if outcome == "OURS":
            fh.write("- Recognition check: you built this side. Reread the lens line; "
                     "if the reason doesn't hold up — count it as a win for the bar.\n")
    (rd / "outcome.json").write_text(json.dumps({
        "round": rd.name, "lens": lens, "picked": picked, "winner": outcome, "gap": gap,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ledger = rd.parent.parent / "LEDGER.md"
    if not ledger.is_file():
        ledger.write_text("# Gauntlet log\n\n| round | lens | winner | gap |\n|---|---|---|---|\n",
                          encoding="utf-8")
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(f"| {rd.name} | {lens or '—'} | {outcome} | {gap.replace('|', '/')[:100]} |\n")

    print(f"winner: {outcome} (picked {picked})")
    print(f"this round's gap: {gap}")
    print(f"log: {ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
