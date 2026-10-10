#!/usr/bin/env python3
"""Blind pair for a gauntlet round (references/gauntlet.md).

Copies the bar (--ref) and our capture (--cand) to <round>/ab/A.* and B.* in random
order, matching format and size so the side can't be guessed from the files.
The key is written to <round>/ab/key.json — it isn't opened before the verdict; reveal.py
reveals it only after verdict.md has WINNER and GAP.

Usage:
  ab.py --round .studioigor/gauntlet/<target>/rounds/03 --ref <bar file> --cand <our frame>
        [--shrink 1000] [--squint]

stdlib only; images are matched with sips (macOS) or magick, if available.
"""
from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".gif", ".heic"}


def tool(name: str) -> bool:
    return shutil.which(name) is not None


def to_png(src: Path, dst: Path, size: int | None) -> Path:
    """Match format and size: identical PNGs don't give the side away."""
    dst = dst.with_suffix(".png")
    if tool("sips"):
        cmd = ["sips", "-s", "format", "png"] + (["-Z", str(size)] if size else []) + [str(src), "--out", str(dst)]
    elif tool("magick"):
        cmd = ["magick", str(src)] + (["-resize", f"{size}x{size}>"] if size else []) + [str(dst)]
    else:
        shutil.copyfile(src, dst.with_suffix(src.suffix))
        return dst.with_suffix(src.suffix)
    subprocess.run(cmd, check=True, capture_output=True)
    return dst


def dims(p: Path) -> tuple[int, int] | None:
    if not tool("sips"):
        return None
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(p)],
                         capture_output=True, text=True).stdout
    try:
        w = int(out.split("pixelWidth:")[1].split()[0])
        h = int(out.split("pixelHeight:")[1].split()[0])
        return w, h
    except (IndexError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Blind pair for a gauntlet round")
    ap.add_argument("--round", required=True, help="round folder, e.g. .studioigor/gauntlet/lookdev/rounds/03")
    ap.add_argument("--ref", required=True, help="the bar")
    ap.add_argument("--cand", required=True, help="our capture")
    ap.add_argument("--shrink", type=int, default=1000, help="max image side, 0 — don't change")
    ap.add_argument("--squint", action="store_true", help="also 128 px copies — the silhouette test")
    a = ap.parse_args()

    ref, cand = Path(a.ref), Path(a.cand)
    for label, p in (("--ref", ref), ("--cand", cand)):
        if not p.is_file():
            print(f"error: {label} not found: {p}", file=sys.stderr)
            return 2
    ab = Path(a.round) / "ab"
    ab.mkdir(parents=True, exist_ok=True)
    for old in ab.glob("*"):
        old.unlink()

    sides = [("reference", ref), ("candidate", cand)]
    random.SystemRandom().shuffle(sides)
    written = {}
    for letter, (role, src) in zip("AB", sides):
        if src.suffix.lower() in IMAGE_EXTS:
            written[letter] = to_png(src, ab / letter, a.shrink or None)
            if a.squint and tool("sips"):
                sq = ab / f"{letter}.squint.png"
                subprocess.run(["sips", "-Z", "128", str(written[letter]), "--out", str(sq)],
                               check=True, capture_output=True)
        else:
            written[letter] = ab / f"{letter}{src.suffix}"
            shutil.copyfile(src, written[letter])
    (ab / "key.json").write_text(json.dumps({
        "A": sides[0][0], "B": sides[1][0],
        "reference_source": str(ref), "candidate_source": str(cand),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"blind pair: {written['A']}  {written['B']}")
    da, db = dims(written["A"]), dims(written["B"])
    if da and db and abs(da[0] / da[1] - db[0] / db[1]) > 0.05 * max(da[0] / da[1], db[0] / db[1]):
        print("WARNING: different aspect ratios — that's a hint and a comparison of the wrong things. "
              "Match the capture's framing to the bar.")
    print("Judge through one lens, write verdict.md (WINNER + GAP), then reveal.py. "
          "Don't open key.json, don't look at file sizes (ls -l).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
