#!/usr/bin/env python3
"""studioigor — game project state: where we are, what's next, what's decided.

All state lives in <game>/.studioigor/. This script is the only way to read
and change it without things drifting apart: the pipeline survives /clear,
a new session and a month-long break.

Commands (the project root is searched upward from the current folder, or --root):
  init <root> --name "Name"          create .studioigor/, git, CLAUDE.md, studio roles
  status [--full] [--no-run]         where we are, what's open, what's next (read FIRST)
  decide "decision" --by user|agent --why "…" [--options "…"] [--phase N]
  tick "<part of the gate text>" [--phase N] [--reopen | --skip "why" | --block "why"]
  note "what was done" "what's next" session log + the "Now" block in STATE.md
  verify                             run TEST and CAPTURE from ENV.md → VERIFIED: yes
  mechanics [--check]                mechanics table and the next step for each
  gitignore <engine> [--lfs]         add a .gitignore block for the engine (+ git-lfs)
  commit "message" [--body "…"] [--tag name]   git add -A + commit. Never pushes.
  projects                           known projects (registry in user-choices/projects.md)

stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.dont_write_bytecode = True
SKILL = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL / "scripts" / "templates"
ST = ".studioigor"

PHASE_HDR = re.compile(r"^##\s+Phase\s+(\d+)\s+—\s+(.+?)\s*$", re.M)
GATE = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")
PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")
FIELD = re.compile(r"^([A-Z][A-Z ]+):[ \t]*(.*)$", re.M)

HINT = {
    0: ("check git and move on to the idea", "SKILL.md"),
    1: ("idea interview: 2–3 AskUserQuestion rounds → pitch card for approval",
        "references/interview.md, design.md, narrative.md"),
    2: ("3–5 style directions → refs.py downloads references → board.py board → feedback → "
        "narrow down until locked → ART_BIBLE.md", "references/style.md"),
    3: ("research first (research/stack.md) → platforms → 2–4 engines with explanations → choice",
        "references/stack.md"),
    4: ("research the best setup (research/environment.md) → envcheck.py → install everything ourselves → "
        "hello project → studio.py verify → the user sees the window", "references/environment.md"),
    5: ("research (research/assets.md) → strategy by category → look-dev scene → "
        "captures/lookdev/ → board → approval", "references/assets.md"),
    6: ("next mechanic from the table: research → spec → gym → self-check → "
        "the user plays → tuning → locked", "references/mechanics.md, code.md"),
    7: ("build the vertical slice from locked mechanics, pass the game-ness checklist, let the user play",
        "references/production.md, narrative.md"),
    8: ("close SCOPE.md lines, contact sheet of units, playtests of new content",
        "references/production.md"),
    9: ("juice, sound, first 60 seconds, performance — until the user says \"good enough\"",
        "references/polish-release.md"),
    10: ("research platform requirements → ship gates → builds → publishing decision",
         "references/polish-release.md"),
}

MECH_NEXT = {
    "idea": "research research/mech-{id}.md → spec in DESIGN.md → status spec",
    "spec": "build the gym (test scene) → status gym",
    "gym": "self-check (CAPTURE, screenshots) → let the user play → status playtest",
    "playtest": "feedback (is it fun?) → tuning → repeat or locked",
    "locked": "done",
    "cut": "cut",
}

CODE_EXT = {".gd", ".cs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".rs", ".cpp", ".cc",
            ".h", ".hpp", ".lua", ".py", ".gdshader", ".shader", ".hlsl", ".glsl", ".wgsl"}
VENDOR = re.compile(r"(^|/)(addons|node_modules|Packages|Library|ThirdParty|vendor|third_party|"
                    r"Plugins|dist|build|\.godot)/")
TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e)/|(^|/)test_[^/]*$|"
                       r"[._-](test|spec)\.[a-z]+$|Tests?\.cs$", re.I)
OVERHEAD = re.compile(r"^(\.studioigor/|\.claude/|docs?/|tools/|\.git)|\.md$|(^|/)(tests?|__tests__|"
                      r"spec)/|[._-](test|spec)\.[a-z]+$|Tests?\.cs$", re.I)

IGNORE = {
    "base": [".DS_Store", ".claude/worktrees/", f"{ST}/captures/", f"{ST}/refs/**/*.jpg", f"{ST}/refs/**/*.jpeg",
             f"{ST}/refs/**/*.png", f"{ST}/refs/**/*.webp", f"{ST}/refs/**/*.gif",
             f"{ST}/refs/**/*.mp4", f"{ST}/refs/**/*.webm", f"{ST}/boards/**/*.png",
             f"{ST}/boards/**/*.jpg", f"{ST}/boards/**/*.mp4", f"{ST}/gauntlet/**/*.png",
             f"{ST}/gauntlet/**/*.jpg", f"{ST}/gauntlet/**/*.webp", f"{ST}/autopilot/state.json",
             f"{ST}/autopilot/lock", f"{ST}/autopilot/lock.json", f"{ST}/autopilot/logs/",
             f"{ST}/autopilot/runner.log", f"{ST}/autopilot/LOG.md"],
    "godot": [".godot/", "/android/", "/export/", "/build/", "*.tmp"],
    "godot-mono": [".godot/", "/android/", "/export/", "/build/", ".mono/", "bin/", "obj/", "*.tmp"],
    "unity": ["/[Ll]ibrary/", "/[Tt]emp/", "/[Oo]bj/", "/[Bb]uild/", "/[Bb]uilds/", "/[Ll]ogs/",
              "/[Uu]ser[Ss]ettings/", "/[Mm]emoryCaptures/", "/[Rr]ecordings/", "*.csproj",
              "*.sln", "*.suo", "*.user", "*.pidb", "*.pdb", "*.mdb", "*.opendb", "*.VC.db",
              "*.apk", "*.aab", "*.unitypackage", ".vs/", ".idea/", "crashlytics-build.properties"],
    "unreal": ["Binaries/", "DerivedDataCache/", "Intermediate/", "Saved/", ".vs/", "*.sln",
               "*.xcworkspace", "*.VC.db", "*.opensdf", "*.sdf"],
    "web": ["node_modules/", "dist/", ".vite/", "coverage/", "test-results/",
            "playwright-report/", "*.log"],
    "defold": [".internal/", "build/", ".externalToolBuilders", "*.der"],
    "bevy": ["target/"],
}
LFS = ["*.glb", "*.gltf", "*.fbx", "*.blend", "*.obj", "*.png", "*.jpg", "*.jpeg", "*.psd",
       "*.aseprite", "*.wav", "*.ogg", "*.mp3", "*.mp4", "*.exr", "*.hdr", "*.ttf", "*.otf"]


# ------------------------------------------------------------------ helpers

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def strip_noise(text: str) -> str:
    """Strip what isn't content: comments, code, examples."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    out = []
    for line in text.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue
        out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(strip_noise(text))


def field(text: str, name: str) -> str:
    for m in FIELD.finditer(text):
        if m.group(1).strip() == name:
            return m.group(2).strip()
    return ""


def registry() -> Path:
    uc = os.environ.get("STUDIOIGOR_UC") or str(SKILL / "user-choices")
    return Path(uc) / "projects.md"


def known_projects() -> list[tuple[str, Path]]:
    out = []
    for line in read(registry()).splitlines():
        m = re.match(r"^- (.*?) — (/.*?) — ", line)
        if m and (Path(m.group(2)) / ST).is_dir():
            out.append((m.group(1), Path(m.group(2))))
    return out


def register(name: str, root: Path) -> None:
    reg = registry()
    reg.parent.mkdir(parents=True, exist_ok=True)
    text = read(reg) or "# studioigor projects\n\nWritten by `studio.py init`. Used to find a project from any folder.\n\n"
    if f" — {root} — " in text:
        return
    reg.write_text(text + f"- {name} — {root} — {date.today().isoformat()}\n", encoding="utf-8")


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        if (d / ST).is_dir():
            return d
    projs = known_projects()
    below = sorted({d.parent for d in p.glob(f"*/{ST}")})
    msg = ["no .studioigor/ found upward from the current folder."]
    if projs or below:
        msg.append("Known projects — go to the right one (cd) or pass --root:")
        for n, r in projs:
            msg.append(f"  {n}: {r}")
        for r in below:
            if r not in [x for _, x in projs]:
                msg.append(f"  {r.name}: {r}")
        msg.append("Several and unclear which one — ask the user (AskUserQuestion).")
    msg.append("New project: studio.py init <folder> --name \"Name\"")
    sys.exit("\n".join(msg))


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=check)


def in_repo(root: Path) -> bool:
    try:
        return git(root, "rev-parse", "--is-inside-work-tree").returncode == 0
    except FileNotFoundError:
        return False


def cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def engine_of(root: Path) -> str:
    e = field(read(root / ST / "TECH.md"), "ENGINE")
    return "" if (not e or PLACEHOLDER.search(e)) else e.split()[0].lower()


def subst(cmd: str, root: Path) -> str | None:
    """Substitute {skill} and {engine}. None if there is nothing to substitute."""
    cmd = cmd.replace("{skill}", str(SKILL))
    if "{engine}" in cmd:
        e = engine_of(root)
        if not e:
            return None
        cmd = cmd.replace("{engine}", e)
    return cmd


# ------------------------------------------------------------------ pipeline

def parse_pipeline(text: str) -> list[dict]:
    phases = []
    marks = list(PHASE_HDR.finditer(text))
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[start:end]
        fm = re.search(r"^files:[ \t]*(.*)$", body, re.M)
        files = [f.strip() for f in (fm.group(1) if fm else "").split(",") if f.strip()]
        gates = []
        offset = start
        for line in body.splitlines(keepends=True):
            g = GATE.match(line.strip())
            if g:
                t = g.group(2).strip()
                cm = re.search(r"—\s*check:\s*(.*)$", t)
                gates.append({
                    "done": g.group(1).lower() == "x",
                    "text": t,
                    "label": t[: cm.start()].strip() if cm else t,
                    "check": cm.group(1).strip() if cm else "manual",
                    "pos": offset,
                    "line": line,
                })
            offset += len(line)
        phases.append({"num": int(m.group(1)), "name": m.group(2), "files": files, "gates": gates})
    return phases


def gate_open(g: dict) -> bool:
    return not g["done"] and "SKIP:" not in g["text"] and "BLOCKED:" not in g["text"]


def gate_kind(g: dict) -> str:
    c = g["check"].lower()
    if c.startswith("user"):
        return "user"
    if c.startswith("manual"):
        return "manual"
    return "cmd"


def run_check(cmd: str, root: Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    tail = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode == 0, (tail[-1][:120] if tail else f"exit {p.returncode}")


MARKS = {"SKIP:": r"\s+SKIP:\s.*$", "BLOCKED:": r"\s+BLOCKED:\s.*$",
         "PROXY": r"\s+PROXY \d{4}-\d{2}-\d{2}"}


def set_gate(pipeline: Path, gate: dict, mark: str | None = None, suffix: str = "",
             strip: tuple[str, ...] = ()) -> None:
    text = read(pipeline)
    line = gate["line"]
    new = line
    for s in strip:  # remove the SKIP/BLOCKED/PROXY mark without touching the gate text itself
        new = re.sub(MARKS[s], "", new.rstrip("\n")) + "\n"
    if mark is not None:
        new = re.sub(r"\[( |x|X)\]", f"[{mark}]", new, count=1)
    if suffix:
        new = new.rstrip("\n") + f" {suffix}\n"
    text = text[: gate["pos"]] + new + text[gate["pos"] + len(line):]
    pipeline.write_text(text, encoding="utf-8")


def current_phase(root: Path, phases: list[dict]) -> dict | None:
    for ph in phases:
        ph["file_gaps"] = []
        for f in ph["files"]:
            p = root / ST / f
            if not p.is_file():
                ph["file_gaps"].append((f, ["file missing"]))
            else:
                ph_ = placeholders(read(p))
                if ph_:
                    ph["file_gaps"].append((f, ph_))
        if ph["file_gaps"] or any(gate_open(g) for g in ph["gates"]):
            return ph
    return None


# ------------------------------------------------------------------ mechanics

def parse_table(text: str, heading: str) -> list[dict]:
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.M)
    if not m:
        return []
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    block = strip_noise(rest[: nxt.start()] if nxt else rest)
    rows = [l.strip() for l in block.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    head = [h.strip().lower() for h in rows[0].strip("|").split("|")]
    out = []
    for r in rows[2:]:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if not any(cells):
            continue
        row = dict(zip(head, cells + [""] * (len(head) - len(cells))))
        out.append(row)
    return out


def mechanics(root: Path) -> list[dict]:
    rows = parse_table(read(root / ST / "DESIGN.md"), "Mechanics")
    return [r for r in rows if r.get("id") and not PLACEHOLDER.search(r.get("id", ""))]


def ideas(root: Path) -> list[dict]:
    rows = parse_table(read(root / ST / "DESIGN.md"), "Game designer ideas")
    return [r for r in rows if r.get("id") and not PLACEHOLDER.search(r.get("id", ""))]


def autopilot_line(root: Path) -> str:
    try:
        s = json.loads(read(root / ST / "autopilot" / "state.json") or "{}")
    except ValueError:
        return ""
    if not s:
        return ""
    if s.get("active") and os.environ.get("STUDIOIGOR_AUTOPILOT"):
        return (f"mode: autopilot, tick {s.get('ticks', 0) + 1}/{s.get('max_ticks')}, goal {s.get('goal')} — "
                "taste decisions on the user's behalf per references/autopilot.md (decide --by proxy, tick --proxy)")
    if s.get("active"):
        return (f"AUTOPILOT ACTIVE: goal {s.get('goal')}, ticks {s.get('ticks', 0)}/{s.get('max_ticks')}, "
                f"until {str(s.get('deadline') or '∞')[:16]}. Do not edit the project in parallel — "
                "autopilot.py status / stop")
    rep = root / ST / "autopilot" / "REPORT.md"
    return (f"autopilot stopped {str(s.get('stopped_at', ''))[:16]}: {s.get('reason', '')}"
            + (f" — report {ST}/autopilot/REPORT.md" if rep.is_file() else ""))


def mech_problems(root: Path, rows: list[dict]) -> list[str]:
    pt = read(root / ST / "PLAYTESTS.md")
    probs = []
    mvp = [r for r in rows if r.get("tier", "").lower() == "mvp" and r.get("status", "").lower() != "cut"]
    if not mvp:
        return ["DESIGN.md has no mvp mechanics"]
    for r in mvp:
        mid, st = r["id"], r.get("status", "").lower()
        if st != "locked":
            probs.append(f"{mid} {r.get('mechanic', '')}: status {st or '—'}, needs locked")
        if not (root / ST / "research" / f"mech-{mid}.md").is_file():
            probs.append(f"{mid}: no research research/mech-{mid}.md")
        if st == "locked" and not re.search(rf"\b{re.escape(mid)}\b", strip_noise(pt)):
            probs.append(f"{mid}: locked without a playtest entry in PLAYTESTS.md")
    return probs


# ------------------------------------------------------------------ balance

def balance(root: Path) -> list[str]:
    """Game first: warn if effort goes into tests/docs/tools."""
    warn = []
    if not in_repo(root):
        return warn
    log = git(root, "log", "-8", "--name-only", "--format=@@%h %s").stdout
    commits, cur = [], None
    for line in log.splitlines():
        if line.startswith("@@"):
            cur = {"msg": line[2:], "files": []}
            commits.append(cur)
        elif line.strip() and cur is not None:
            cur["files"].append(line.strip())
    streak = 0
    for c in commits:
        if not c["files"] or all(f.startswith(ST + "/") for f in c["files"]):
            continue  # pipeline commits (decisions, concept, style) are neutral
        if all(OVERHEAD.search(f) for f in c["files"]):
            streak += 1
        else:
            break
    has_code = any(Path(f).suffix.lower() in CODE_EXT and not VENDOR.search(f) and not TEST_PATH.search(f)
                   for f in git(root, "ls-files").stdout.splitlines())
    if streak >= 3 and has_code:
        warn.append(f"FOCUS ON THE GAME — the last consecutive commits ({streak}) touched only "
                    "docs/tests/tools. The next step must change what the player sees or plays.")
    files = git(root, "ls-files").stdout.splitlines()
    code_lines = test_lines = doc_lines = 0
    for f in files:
        if VENDOR.search(f):
            continue
        p = root / f
        suf = p.suffix.lower()
        if suf not in CODE_EXT and suf != ".md":
            continue
        try:
            n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        if suf == ".md":
            if not f.startswith(ST + "/") and f not in ("CLAUDE.md", "README.md") \
                    and not f.startswith(".claude/"):
                doc_lines += n
        elif TEST_PATH.search(f):
            test_lines += n
        else:
            code_lines += n
    if code_lines + test_lines > 400 and test_lines > 0.35 * (code_lines + test_lines):
        warn.append(f"TOO MANY TESTS — {test_lines} lines of tests for {code_lines} lines of game. "
                    "Tests only where a bug silently breaks the game (references/code.md).")
    if doc_lines > max(800, 0.5 * code_lines):
        warn.append(f"TOO MUCH DOCUMENTATION — {doc_lines} lines of .md outside .studioigor/. "
                    "Documents are short decision records, not essays.")
    return warn


# ------------------------------------------------------------------ commands

def cmd_init(a) -> int:
    root = Path(a.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    st = root / ST
    for d in ("research", "refs", "boards", "captures"):
        (st / d).mkdir(parents=True, exist_ok=True)
    created, kept = [], []
    today = date.today().isoformat()
    for tpl in sorted((TEMPLATES / "project" / "studioigor").glob("*.md")):
        dst = st / tpl.name
        if dst.exists():
            kept.append(tpl.name)
            continue
        dst.write_text(read(tpl).replace("{name}", a.name).replace("{date}", today), encoding="utf-8")
        created.append(tpl.name)

    notes = []
    fresh_repo = False
    if not in_repo(root):
        if git(root, "init", "-b", "main").returncode == 0:
            fresh_repo = True
            notes.append("git init (branch main)")
    else:
        br = git(root, "branch", "--show-current").stdout.strip()
        has_commits = git(root, "rev-parse", "HEAD").returncode == 0
        if has_commits and br in ("main", "master"):
            notes.append(f"repository already exists, branch {br}: for an existing game create a working "
                         f"branch (git switch -c studioigor) and merge into {br} only with the user's consent")
    add_ignore(root, "base")

    cl_tpl = TEMPLATES / "project" / "CLAUDE.md"
    cl = root / "CLAUDE.md"
    if cl_tpl.is_file():
        body = read(cl_tpl).replace("{name}", a.name).replace("{skill}", str(SKILL))
        if not cl.exists():
            cl.write_text(body, encoding="utf-8")
            notes.append("CLAUDE.md created")
        elif "studioigor" not in read(cl):
            with cl.open("a", encoding="utf-8") as fh:
                fh.write("\n\n" + body)
            notes.append("CLAUDE.md extended with the studioigor block")
    agents = TEMPLATES / "agents"
    if agents.is_dir():
        dst = root / ".claude" / "agents"
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in sorted(agents.glob("*.md")):
            if not (dst / f.name).exists():
                (dst / f.name).write_text(read(f).replace("{skill}", str(SKILL)), encoding="utf-8")
                n += 1
        if n:
            notes.append(f"studio roles: {n} files in .claude/agents/ (available in a new session)")

    print(f"studioigor — project \"{a.name}\": {root}")
    if created:
        print(f"  created in {ST}/: {', '.join(created)}")
    if kept:
        print(f"  already there, left untouched: {', '.join(kept)}")
    for n in notes:
        print(f"  {n}")
    register(a.name, root)
    print(f"\nNext: cd {root} && python3 {Path(__file__).resolve()} status")
    print("  (all studio.py commands find the project from the current folder; next time start claude from here)")
    if fresh_repo:
        print("Then the first commit: studio.py commit \"studioigor: project start\"")
    return 0


def cmd_status(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    st = root / ST
    pipeline = st / "PIPELINE.md"
    phases = parse_pipeline(read(pipeline))
    if not phases:
        sys.exit(f"{pipeline}: no phases in the \"## Phase N — Name\" format. Restore from the template: "
                 f"{TEMPLATES / 'project' / 'studioigor' / 'PIPELINE.md'}")
    state = read(st / "STATE.md")
    name = field(state, "PROJECT") or root.name
    print(f"studioigor — {name}   ({root})")
    print(f"skill: {SKILL}   (the <skill> folder in SKILL.md and references)")

    # Auto-check command gates of the current phase (and of all closed ones with --full).
    ticked = []
    regress = []
    if not a.no_run:
        for _ in range(len(phases)):
            phases = parse_pipeline(read(pipeline))
            cur = current_phase(root, phases)
            changed = False
            if cur is None:
                break
            for g in cur["gates"]:
                if gate_open(g) and gate_kind(g) == "cmd":
                    cmd = subst(g["check"], root)
                    if cmd is None:
                        continue
                    ok, _ = run_check(cmd, root)
                    if ok:
                        set_gate(pipeline, g, "x")
                        ticked.append(f"P{cur['num']}: {g['label']}")
                        changed = True
                        break
            if not changed:
                break
        if a.full:
            for ph in parse_pipeline(read(pipeline)):
                for g in ph["gates"]:
                    if g["done"] and gate_kind(g) == "cmd":
                        cmd = subst(g["check"], root)
                        if cmd:
                            ok, out = run_check(cmd, root)
                            if not ok:
                                regress.append(f"P{ph['num']}: {g['label']} — {out}")

    phases = parse_pipeline(read(pipeline))
    cur = current_phase(root, phases)
    if ticked:
        print("\nticked automatically (check passed):")
        for t in ticked:
            print(f"  ✓ {t}")
    if regress:
        print("\nREGRESSION — gates of closed phases no longer pass:")
        for r in regress:
            print(f"  ! {r}")

    if cur is None:
        print("\nALL PHASES CLOSED.")
        skipped = [(p["num"], g["label"], g["text"]) for p in phases for g in p["gates"]
                   if "SKIP:" in g["text"] or "BLOCKED:" in g["text"]]
        if skipped:
            print("Skipped/blocked (tell the user first thing):")
            for n, _l, t in skipped:
                print(f"  P{n}: {t}")
        _update_state_phase(st, "done")
        return 0

    n = cur["num"]
    closed = [p["num"] for p in phases if p["num"] < n]
    done_s = "" if not closed else (f"   (phase {closed[0]} closed)" if len(closed) == 1
                                   else f"   (phases {min(closed)}–{max(closed)} closed)")
    print(f"\nPHASE {n} — {cur['name']}{done_s}")
    hint, ref = HINT.get(n, ("", ""))
    print(f"  what to do: {hint}")
    print(f"  read: {ref}")
    _update_state_phase(st, f"{n} — {cur['name']}")

    if cur["file_gaps"]:
        print("\n  unfilled:")
        for f, ph in cur["file_gaps"]:
            shown = ", ".join(p[:50] for p in ph[:4])
            more = f" (+{len(ph) - 4})" if len(ph) > 4 else ""
            print(f"    {f}: {shown}{more}")
    opened = [g for g in cur["gates"] if gate_open(g)]
    if opened:
        print("\n  open gates:")
        for g in opened:
            k = gate_kind(g)
            tag = {"user": "[user]", "manual": "[agent]", "cmd": "[command]"}[k]
            extra = ""
            if k == "cmd":
                cmd = subst(g["check"], root)
                extra = "  (engine not chosen in TECH.md yet)" if cmd is None else f"  → {cmd}"
            print(f"    {tag} {g['label']}{extra}")
        if os.environ.get("STUDIOIGOR_AUTOPILOT"):
            print("  tick: studio.py tick \"<part of the text>\"; user gates — tick \"…\" --proxy "
                  "(the autopilot decides on the user's behalf, references/autopilot.md)")
        else:
            print("  tick: studio.py tick \"<part of the text>\"   (user gates — only after an explicit \"yes\")")

    if n == 6 or (n > 6 and a.full):
        rows = mechanics(root)
        if rows:
            print("\n  mechanics:")
            for r in rows:
                s = r.get("status", "").lower()
                print(f"    {r['id']:<4} {r.get('mechanic', '')[:28]:<28} {r.get('tier', ''):<4} "
                      f"{s:<9} → {MECH_NEXT.get(s, '?').replace('{id}', r['id'])}")
            nxt = next((r for r in rows if r.get("tier", "").lower() == "mvp"
                        and r.get("status", "").lower() not in ("locked", "cut")), None)
            if nxt:
                print(f"  NEXT MECHANIC: {nxt['id']} {nxt.get('mechanic', '')}")
    if n == 8:
        sc = SKILL / "scripts" / "scope.py"
        if sc.is_file():
            p = subprocess.run([sys.executable, str(sc), str(root)], capture_output=True, text=True)
            print("\n" + "\n".join("  " + l for l in p.stdout.strip().splitlines()[:14]))

    waiting = [r for r in ideas(root) if r.get("status", "").lower().startswith("propos")]
    if waiting:
        print(f"\ngame designer ideas waiting for the user's decision: {len(waiting)} — "
              + ", ".join(f"{r['id']} {r.get('idea', '')[:24]}" for r in waiting[:4]))

    ap = autopilot_line(root)
    if ap:
        print("\n" + ap)
    pg = [g["label"] for p_ in parse_pipeline(read(st / "PIPELINE.md")) for g in p_["gates"]
          if g["done"] and "PROXY" in g["text"]]
    pd = len(re.findall(r"^\|\s*\d+\s*\|.*\|\s*proxy\s*\|", read(st / "DECISIONS.md"), re.M))
    if pg and not os.environ.get("STUDIOIGOR_AUTOPILOT"):
        print(f"decided by the autopilot on the user's behalf: gates {len(pg)}, decisions {pd} — go over them "
              f"with the user (autopilot.md §9 \"The user returns\"); once confirmed, tick \"…\" removes PROXY")

    now = re.search(r"^##\s+Now\s*\n(.*?)(?=^##\s|\Z)", state, re.M | re.S)
    if now and now.group(1).strip():
        print(f"\nnow (STATE.md): {now.group(1).strip()[:300]}")
    dec = [l for l in read(st / "DECISIONS.md").splitlines() if re.match(r"^\|\s*\d+\s*\|", l)]
    if dec:
        print("latest decisions:")
        for l in dec[-3:]:
            c = [x.strip().replace("\\|", "|") for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
            print(f"  #{c[0]} [{c[5] if len(c) > 5 else '?'}] {c[3][:90] if len(c) > 3 else ''}")
    pts = re.findall(r"^##\s+(PT-\d+.*)$", strip_noise(read(st / "PLAYTESTS.md")), re.M)
    if pts:
        print(f"last playtest: {pts[-1][:90]}")

    if in_repo(root):
        br = git(root, "branch", "--show-current").stdout.strip()
        dirty = [l for l in git(root, "status", "--porcelain").stdout.splitlines() if l.strip()]
        print(f"git: branch {br or '(detached)'}" + (f", uncommitted files: {len(dirty)}" if dirty else ", clean"))
        wts = [l for l in git(root, "worktree", "list").stdout.splitlines()[1:] if l.strip()]
        if wts:
            print(f"  subagent worktrees: {len(wts)} — merge or remove after review")
    else:
        print("git: NOT a repository — git init")

    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import learn  # noqa: E402
        items = learn.for_phase(str(n), root)
        if items:
            print("\nkeep in mind (approved by the user — priority over general instructions; "
                  "[this game] beats [all games]):")
            for i in items[:12]:
                print(f"  - {i}")
            if len(items) > 12:
                print(f"  … +{len(items) - 12} more: learn.py for-phase {n}")
        pend = learn.pending_count()
        if pend:
            print(f"skill improvements awaiting a decision: {pend} — ask at the end of the phase/session (learn.py list)")
        due, last = learn.radar_due()
        if due and n in (0, 3, 4, 5):
            print(f"tech radar: due (last: {last}) — a short search for what's new → learn.py propose")
    except Exception as e:  # learned items must not break status
        print(f"(user-choices unavailable: {e})")

    warns = balance(root)
    if warns:
        print()
        for w in warns:
            print(f"  ! {w}")
    return 0


def _update_state_phase(st: Path, phase: str) -> None:
    p = st / "STATE.md"
    t = read(p)
    if not t:
        return
    t2 = re.sub(r"^PHASE:.*$", f"PHASE: {phase}", t, count=1, flags=re.M)
    if t2 != t:
        p.write_text(t2, encoding="utf-8")


def pick_phase(root: Path, n: int | None) -> dict:
    phases = parse_pipeline(read(root / ST / "PIPELINE.md"))
    if n is None:
        cur = current_phase(root, phases)
        if cur is None:
            sys.exit("all phases are closed — pass --phase N")
        return cur
    for p in phases:
        if p["num"] == n:
            return p
    sys.exit(f"no phase {n}")


def cmd_tick(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    q = a.gate.lower()
    if a.phase is None:
        phases = parse_pipeline(read(root / ST / "PIPELINE.md"))
        cur = current_phase(root, phases)
        pool = [cur] if cur else []
        found = [(p, g) for p in pool for g in p["gates"] if q in g["text"].lower()]
        if not found:  # a gate of a past or future phase — search all of them
            found = [(p, g) for p in phases for g in p["gates"] if q in g["text"].lower()]
        if len({(p["num"], g["label"]) for p, g in found}) == 1:
            ph = found[0][0]
        elif found:
            print("several gates match — refine the text or pass --phase N:")
            for p, g in found:
                print(f"  P{p['num']}: {g['label']}")
            return 1
        else:
            ph = cur or phases[-1]
    else:
        ph = pick_phase(root, a.phase)
    hits = [g for g in ph["gates"] if q in g["text"].lower()]
    if not hits:
        print(f"phase {ph['num']} has no gate matching \"{a.gate}\". It has:")
        for g in ph["gates"]:
            print(f"  [{'x' if g['done'] else ' '}] {g['label']}")
        return 1
    if len(hits) > 1:
        print("several gates match — refine:")
        for g in hits:
            print(f"  {g['label']}")
        return 1
    g = hits[0]
    pipeline = root / ST / "PIPELINE.md"
    if a.reopen:
        set_gate(pipeline, g, " ", strip=("SKIP:", "BLOCKED:", "PROXY"))
        print(f"reopened: P{ph['num']} — {g['label']}")
    elif a.skip:
        set_gate(pipeline, g, None, f"SKIP: {a.skip}")
        print(f"skipped: P{ph['num']} — {g['label']} (SKIP: {a.skip})")
    elif a.block:
        set_gate(pipeline, g, None, f"BLOCKED: {a.block}")
        print(f"blocked: P{ph['num']} — {g['label']} (BLOCKED: {a.block})")
    else:
        proxy = a.proxy or (bool(os.environ.get("STUDIOIGOR_AUTOPILOT")) and gate_kind(g) == "user")
        if proxy and gate_kind(g) != "user":
            print("--proxy is only for user gates; tick the others with a plain tick")
            return 1
        if gate_kind(g) == "cmd":
            cmd = subst(g["check"], root)
            if cmd:
                ok, out = run_check(cmd, root)
                if not ok:
                    print(f"check fails: {cmd}\n  {out}\nNot ticking. Fix it or use --skip/--block with a reason.")
                    return 1
        if proxy:
            set_gate(pipeline, g, "x", f"PROXY {date.today().isoformat()}", strip=("PROXY",))
            print(f"ticked on the user's behalf: P{ph['num']} — {g['label']} (PROXY)")
            print(f"  record it: decide \"…\" --by proxy --why \"…\" and a line in {ST}/autopilot/REVIEW.md")
            return 0
        set_gate(pipeline, g, "x", strip=("PROXY",))
        print(f"ticked: P{ph['num']} — {g['label']}")
        if gate_kind(g) == "user":
            print("  this is a user gate: record the decision — studio.py decide \"…\" --by user --why \"…\"")
    return 0


def cmd_decide(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    p = root / ST / "DECISIONS.md"
    text = read(p) or "# Decisions\n\n| # | date | phase | decision | options | by | why |\n|---|---|---|---|---|---|---|\n"
    nums = [int(m) for m in re.findall(r"^\|\s*(\d+)\s*\|", text, re.M)]
    num = max(nums) + 1 if nums else 1
    phase = a.phase
    if phase is None:
        cur = current_phase(root, parse_pipeline(read(root / ST / "PIPELINE.md")))
        phase = cur["num"] if cur else "-"
    if a.by == "user" and os.environ.get("STUDIOIGOR_AUTOPILOT"):
        a.by = "proxy"  # on autopilot the user is absent — this is a decision on their behalf, for review
        print(f"autopilot: --by user recorded as proxy; add a line to {ST}/autopilot/REVIEW.md")
    row = (f"| {num} | {date.today().isoformat()} | {phase} | {cell(a.decision)} | "
           f"{cell(a.options or '—')} | {a.by} | {cell(a.why or '—')} |\n")
    p.write_text(text.rstrip("\n") + "\n" + row, encoding="utf-8")
    print(f"decision #{num} recorded ({a.by})")
    return 0


def cmd_note(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    p = root / ST / "STATE.md"
    t = read(p)
    phase = field(t, "PHASE") or "?"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    t = re.sub(r"^UPDATED:.*$", f"UPDATED: {now}", t, count=1, flags=re.M)
    t = re.sub(r"(^##\s+Now\s*\n)(.*?)(?=^##\s|\Z)", lambda m: m.group(1) + a.next.strip() + "\n\n",
               t, count=1, flags=re.M | re.S)
    row = f"| {now} | {cell(phase)} | {cell(a.done)} | {cell(a.next)} |\n"
    p.write_text(t.rstrip("\n") + "\n" + row, encoding="utf-8")
    print("session log updated")
    return 0


def cmd_verify(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    envp = root / ST / "ENV.md"
    env = read(envp)
    fails = []
    for name in ("TEST", "CAPTURE"):
        c = field(env, name)
        if not c or PLACEHOLDER.search(c):
            fails.append(f"{name}: command not recorded in ENV.md")
            continue
        t0 = time.time()
        print(f"{name}: {c}")
        try:
            p = subprocess.run(c, shell=True, cwd=root, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            fails.append(f"{name}: timeout 15 min")
            continue
        if p.returncode != 0:
            tail = "\n    ".join((p.stdout + p.stderr).strip().splitlines()[-8:])
            fails.append(f"{name}: exit {p.returncode}\n    {tail}")
            continue
        if name == "CAPTURE":
            caps = [f for f in (root / ST / "captures").rglob("*")
                    if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and f.stat().st_mtime >= t0 - 1]
            if not caps:
                fails.append("CAPTURE: the command passed, but no image appeared in .studioigor/captures/")
                continue
            print(f"  ok — {len(caps)} frame(s), e.g. {caps[0].relative_to(root)}")
        else:
            print("  ok")
    if fails:
        print("\nNOT VERIFIED:")
        for f in fails:
            print(f"  - {f}")
        return 1
    new = re.sub(r"^VERIFIED:.*$", "VERIFIED: yes", env, count=1, flags=re.M)
    if new == env and "VERIFIED: yes" not in env:
        new = "VERIFIED: yes\n" + env
    envp.write_text(new, encoding="utf-8")
    print("\nVERIFIED: yes — the environment is confirmed by a real run")
    return 0


def cmd_mechanics(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    rows = mechanics(root)
    if not rows:
        print("DESIGN.md (section \"## Mechanics\") has no mechanics")
        return 1
    for r in rows:
        s = r.get("status", "").lower()
        print(f"{r['id']:<4} {r.get('mechanic', '')[:30]:<30} {r.get('tier', ''):<4} {s:<9} "
              f"{r.get('scene', '')[:40]}")
    if a.check:
        probs = mech_problems(root, rows)
        if probs:
            print("\nnot ready:")
            for p in probs:
                print(f"  - {p}")
            return 1
        print("\nall mvp mechanics locked, with research and a playtest")
    return 0


def add_ignore(root: Path, key: str) -> bool:
    gi = root / ".gitignore"
    text = read(gi)
    start, end = f"# >>> studioigor:{key}", f"# <<< studioigor:{key}"
    if start in text:
        return False
    block = "\n".join([start, *IGNORE[key], end]) + "\n"
    gi.write_text((text.rstrip("\n") + "\n\n" if text.strip() else "") + block, encoding="utf-8")
    return True


def cmd_gitignore(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    e = a.engine.lower()
    if e not in IGNORE or e == "base":
        sys.exit(f"unknown engine: {e}. Available: {', '.join(k for k in IGNORE if k != 'base')}")
    print(".gitignore block added" if add_ignore(root, e) else ".gitignore block already present")
    if a.lfs:
        if subprocess.run(["git", "lfs", "version"], capture_output=True).returncode != 0:
            print("git-lfs is not installed: brew install git-lfs && git lfs install")
            return 1
        ga = root / ".gitattributes"
        t = read(ga)
        add = [f"{p} filter=lfs diff=lfs merge=lfs -text" for p in LFS if f"{p} filter=lfs" not in t]
        if add:
            ga.write_text((t.rstrip("\n") + "\n" if t else "") + "\n".join(add) + "\n", encoding="utf-8")
        git(root, "lfs", "install", "--local")
        print(f"git-lfs: {len(add)} patterns in .gitattributes")
    return 0


def cmd_commit(a) -> int:
    root = Path(a.root).resolve() if a.root else find_root()
    if not in_repo(root):
        sys.exit("not a git repository")
    git(root, "add", "-A")
    args = ["commit", "-m", a.message]
    if a.body:
        args += ["-m", a.body]
    c = git(root, *args)
    if c.returncode != 0:
        out = (c.stdout + c.stderr).strip()
        print("nothing to commit" if "nothing to commit" in out else out)
        return 0 if "nothing to commit" in out else 1
    h = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"commit {h}: {a.message}")
    if a.tag:
        t = git(root, "tag", a.tag)
        print(f"tag {a.tag}" if t.returncode == 0 else f"tag not created: {t.stderr.strip()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="studioigor — game project state")
    ap.add_argument("--root", default="", help="project root (searched upward by default)")
    # --root is also accepted after the subcommand; SUPPRESS does not overwrite a value given before it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init")
    p.add_argument("root")
    p.add_argument("--name", required=True)

    p = sp.add_parser("status", parents=[common])
    p.add_argument("--full", action="store_true", help="re-check gates of closed phases")
    p.add_argument("--no-run", action="store_true", help="do not run check commands")

    p = sp.add_parser("decide", parents=[common])
    p.add_argument("decision")
    p.add_argument("--by", required=True, choices=["user", "agent", "proxy"],
                   help="proxy — the autopilot decided on the user's behalf (the user reviews it later)")
    p.add_argument("--why", default="")
    p.add_argument("--options", default="")
    p.add_argument("--phase", type=int)

    p = sp.add_parser("tick", parents=[common])
    p.add_argument("gate")
    p.add_argument("--phase", type=int)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--reopen", action="store_true")
    g.add_argument("--skip", default="")
    g.add_argument("--block", default="")
    g.add_argument("--proxy", action="store_true", help="autopilot: a user gate on the user's behalf (PROXY)")

    p = sp.add_parser("note", parents=[common])
    p.add_argument("done")
    p.add_argument("next")

    sp.add_parser("verify", parents=[common])

    p = sp.add_parser("mechanics", parents=[common])
    p.add_argument("--check", action="store_true")

    p = sp.add_parser("gitignore", parents=[common])
    p.add_argument("engine")
    p.add_argument("--lfs", action="store_true")

    p = sp.add_parser("commit", parents=[common])
    p.add_argument("message")
    p.add_argument("--body", default="")
    p.add_argument("--tag", default="")

    sp.add_parser("projects")

    a = ap.parse_args()
    if a.cmd == "init":
        return cmd_init(a)
    if a.cmd == "projects":
        projs = known_projects()
        if not projs:
            print("no projects in the registry")
        for n, r in projs:
            print(f"{n}: {r}")
        return 0
    return {"status": cmd_status, "decide": cmd_decide, "tick": cmd_tick, "note": cmd_note,
            "verify": cmd_verify, "mechanics": cmd_mechanics, "gitignore": cmd_gitignore,
            "commit": cmd_commit}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
