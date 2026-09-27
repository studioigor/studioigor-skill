#!/usr/bin/env python3
"""envcheck — what is installed, what is missing for the chosen engine, and how to install it.

Usage:
  envcheck.py [--engine godot|godot-mono|unity|unreal|web|defold|bevy] [--dimension 2d|3d] [--json]
              [--project DIR] [--platforms web,android,ios,windows,mac,linux] [--no-claude]

--engine     defaults to ENGINE: from .studioigor/TECH.md, otherwise common checks only.
--dimension  defaults to DIMENSION: in TECH.md. 3d → Blender is recommended; 2d → Blender is not checked.
--project    game root (default: current folder): TECH.md, addons, packages, .mcp.json.
--platforms  defaults to the PLATFORMS: line in TECH.md.
--no-claude  do not call `claude mcp list` (faster; MCP connection status unknown).

Exit 0 — every REQUIRED item for the engine is present (recommended ones are only
warnings); 1 — something required is missing; 2 — invalid arguments.
stdlib only. Installs and changes nothing — it only looks.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ENGINES = ("godot", "godot-mono", "unity", "unreal", "web", "defold", "bevy")
HOME = Path.home()
GODOT_TPL = HOME / "Library/Application Support/Godot/export_templates"
PW_CACHE = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or HOME / "Library/Caches/ms-playwright")
UNITY_ENV = {"UNITY_NO_BANNER": "1", "UNITY_NO_PAGER": "1", "UNITY_NON_INTERACTIVE": "1",
             "UNITY_NO_CONSENT_PROMPT": "1", "UNITY_NO_UPDATE_CHECK": "1"}
PLACEHOLDER = re.compile(r"<[^<>\n]{1,80}>")

REQ, REC = "required", "recommended"


# ------------------------------------------------------------------ helpers

def run(cmd: list[str], timeout: float = 15, cwd: Path | None = None, env: dict | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd,
                           env={**os.environ, **(env or {})})
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def ver(text: str) -> str:
    m = re.search(r"\d+\.\d+(?:\.\d+)?(?:[a-z]\d+)?", text or "")
    return m.group(0) if m else ""


def vtuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) if v else ()


def first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text else ""


def app_version(app: Path) -> str:
    try:
        with open(app / "Contents/Info.plist", "rb") as f:
            return str(plistlib.load(f).get("CFBundleShortVersionString", ""))
    except (OSError, plistlib.InvalidFileException, ValueError):
        return ""


def jdk(major: int) -> str:
    """Version of the installed JDK with the given major version, or ''. java_home -v lies when
    JAVA_HOME is set, so we parse the full -V list and the keg-only brew formulas."""
    rc, out = run(["/usr/libexec/java_home", "-V"])
    for line in out.splitlines():
        m = re.match(r"\s*(\d+)(\.[\d.]+)?(?:_\d+)?\s", line)
        if m and int(m.group(1)) == major:
            return m.group(1) + (m.group(2) or "")
    for p in (f"/opt/homebrew/opt/openjdk@{major}", f"/usr/local/opt/openjdk@{major}"):
        if Path(p, "bin/java").exists():
            return f"{major} (brew openjdk@{major})"
    return ""


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def field(text: str, name: str) -> str:
    m = re.search(rf"^{re.escape(name)}:[ \t]*(.*)$", text, re.M)
    v = m.group(1).strip() if m else ""
    return "" if not v or PLACEHOLDER.search(v) else v


def dimension(text: str) -> str:
    """DIMENSION from TECH.md → '3d' / '2d' / ''. 2.5D with 3D models counts as 3D."""
    t = text.lower().replace(" ", "")
    return "3d" if re.search(r"3d|2\.5d", t) else ("2d" if "2d" in t else "")


class Report:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, group: str, name: str, ok: bool | None, level: str = REQ, version: str = "",
            hint: str = "", note: str = "", human: bool = False) -> bool:
        """ok=None — cannot be checked yet (the project does not exist yet): not a failure."""
        self.items.append({"group": group, "name": name, "ok": ok, "level": level,
                           "version": version, "hint": "" if ok else hint, "note": note,
                           "human": human and ok is False})
        return bool(ok)


# ------------------------------------------------------------------ Claude Code: MCP, plugins, skills

def mask(text: str) -> str:
    """Do not leak keys from MCP server arguments into the output."""
    return re.sub(r"(?i)((?:key|token|secret|password)[=: ]+)\S+", r"\1***", text)


def mcp_servers(project: Path, probe: bool) -> list[dict]:
    """Servers from the configs (user/local/project) + status from `claude mcp list`."""
    servers: dict[str, dict] = {}
    cfg = {}
    try:
        cfg = json.loads(read(HOME / ".claude.json") or "{}")
    except json.JSONDecodeError:
        pass

    def take(d: dict, scope: str) -> None:
        for name, s in (d or {}).items():
            if not isinstance(s, dict):
                continue
            target = s.get("url") or " ".join([s.get("command", "")] + [str(x) for x in s.get("args", [])])
            target = mask(target)
            servers[name] = {"name": name, "scope": scope, "type": s.get("type", "stdio"),
                             "target": target.strip(), "status": "unknown"}

    take(cfg.get("mcpServers", {}), "user")
    proj = cfg.get("projects", {}).get(str(project), {}) or cfg.get("projects", {}).get(str(project) + "/", {})
    take(proj.get("mcpServers", {}), "local")
    try:
        take(json.loads(read(project / ".mcp.json") or "{}").get("mcpServers", {}), "project")
    except json.JSONDecodeError:
        pass

    if probe and which("claude"):
        rc, out = run(["claude", "mcp", "list"], timeout=25, cwd=project)
        for line in out.splitlines():
            m = re.match(r"^(.+?):\s+(.+?)\s+-\s+(.+)$", line.strip())
            if not m:
                continue
            name, target, st = m.group(1).strip(), mask(m.group(2).strip()), m.group(3)
            status = ("connected" if "Connected" in st or "✔" in st or "✓" in st else
                      "pending" if "Pending" in st or "⏸" in st else
                      "needs-auth" if "auth" in st.lower() else "failed")
            s = servers.setdefault(name, {"name": name, "scope": "?", "type": "?", "target": target})
            s["status"] = status
            s["detail"] = st.strip()[:160]
    return list(servers.values())


def find_mcp(servers: list[dict], pattern: str) -> list[dict]:
    rx = re.compile(pattern, re.I)
    return [s for s in servers if rx.search(s["name"]) or rx.search(s.get("target", ""))]


def claude_plugins() -> list[str]:
    try:
        d = json.loads(read(HOME / ".claude/plugins/installed_plugins.json") or "{}")
        return list(d.get("plugins", {}).keys())
    except json.JSONDecodeError:
        return []


def claude_skills(project: Path) -> list[str]:
    names = []
    for base in (HOME / ".claude/skills", project / ".claude/skills"):
        if base.is_dir():
            names += [p.name for p in base.iterdir() if p.is_dir() or p.is_symlink()]
    return names


def check_mcp(r: Report, servers: list[dict], label: str, pattern: str, level: str, hint: str,
              probed: bool, human_note: str = "") -> list[dict]:
    found = find_mcp(servers, pattern)
    if not found:
        r.add("Agent integrations", f"MCP: {label}", False, level, hint=hint)
        return []
    for s in found:
        st = s.get("status", "unknown")
        r.add("Agent integrations", f"MCP: {s['name']} ({s.get('scope', '?')})", True, level,
              version=st, note=s.get("target", "")[:70])
        if probed and st not in ("connected", "unknown"):
            r.add("Agent integrations", f"MCP {s['name']} connects", False, level,
                  hint=human_note or "claude mcp get " + s["name"], note=s.get("detail", st))
    return found


# ------------------------------------------------------------------ common

def check_common(r: Report, engine: str | None, dim: str) -> None:
    g = "General"
    brew = which("brew")
    r.add(g, "brew", bool(brew), REQ, ver(run([brew, "--version"])[1]) if brew else "",
          '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
          human=True, note="HUMAN: sudo password during install" if not brew else "")
    git = which("git")
    r.add(g, "git", bool(git), REQ, ver(run(["git", "--version"])[1]) if git else "", "xcode-select --install")
    lfs = run(["git", "lfs", "version"])[0] == 0 if git else False
    r.add(g, "git-lfs", lfs, REQ, ver(run(["git", "lfs", "version"])[1]) if lfs else "",
          "brew install git-lfs && git lfs install")
    r.add(g, "python3", True, REQ, sys.version.split()[0])
    node = which("node")
    r.add(g, "node + npm", bool(node and which("npm")), REQ if engine == "web" else REC,
          ver(run(["node", "--version"])[1]) if node else "", "brew install node   (or nvm install --lts)")
    for name, cmd, hint, why in (
        ("ffmpeg", ["ffmpeg", "-version"], "brew install ffmpeg", "video, frames from clips"),
        ("yt-dlp", ["yt-dlp", "--version"], "brew install yt-dlp", "reference frames from YouTube"),
        ("magick (ImageMagick)", ["magick", "-version"], "brew install imagemagick", "palettes, contact sheets"),
        ("gh", ["gh", "--version"], "brew install gh", "GitHub: releases, assets"),
    ):
        path = which(cmd[0])
        r.add(g, name, bool(path), REC, ver(run(cmd)[1]) if path else "", hint, note=why)
    blender = which("blender") or ("/Applications/Blender.app/Contents/MacOS/Blender"
                                   if Path("/Applications/Blender.app").exists() else None)
    b_ver = ver(first_line(run([blender, "--version"], 20)[1])) if blender else ""
    if dim == "3d":      # 3D models are made by Python scripts in Blender -b; no MCP needed
        r.add(g, "Blender", bool(blender), REC, b_ver, "brew install --cask blender",
              note="3D: models via Python scripts; if the user declined — assets.md §4")
    elif dim == "2d":    # procedural and generators by default; Blender only if the asset strategy asks
        if blender:
            r.add(g, "Blender", True, REC, b_ver, note="2D: only for 3D→2D renders, if the style needs them")
    else:
        r.add(g, "Blender", bool(blender), REC, b_ver, "brew install --cask blender",
              note="recommended for 3D; set DIMENSION in TECH.md")


# ------------------------------------------------------------------ platforms from TECH.md

PLATFORM_WORDS = {
    "web": ("web", "browser", "portal", "html5"),
    "android": ("android", "mobile"),
    "ios": ("ios", "iphone", "ipad", "mobile"),
    "windows": ("windows", " pc", "pc ", "desktop"),
    "mac": ("mac", "macos"),
    "linux": ("linux",),
}


def parse_platforms(text: str) -> list[str]:
    t = f" {text.lower()} "
    return [p for p, words in PLATFORM_WORDS.items() if any(w in t for w in words)]


# ------------------------------------------------------------------ Godot

def godot_binary(mono: bool) -> tuple[str | None, str]:
    names = ("godot-mono", "godot_mono") if mono else ("godot", "godot4")
    on_path = which(*names)
    if on_path:
        return on_path, "PATH"
    apps = sorted(glob.glob("/Applications/Godot*.app") + glob.glob(str(HOME / "Applications/Godot*.app")))
    apps = [a for a in apps if ("mono" in a.lower()) == mono]
    for a in apps:
        b = Path(a) / "Contents/MacOS/Godot"
        if b.exists():
            return str(b), a
    return None, ""


def check_godot(r: Report, mono: bool, project: Path, platforms: list[str], want_ver: str,
                servers: list[dict], probed: bool) -> None:
    g = "Engine"
    cask = "godot-mono" if mono else "godot"
    binp, where = godot_binary(mono)
    gv = ""
    if binp:
        lines = [l.strip() for l in run([binp, "--version"], 20)[1].splitlines() if re.match(r"^\d+\.\d+", l.strip())]
        gv = lines[-1] if lines else ""
    m = re.match(r"^(\d+\.\d+(?:\.\d+)?)\.([a-z]+\d*)", gv)
    short = f"{m.group(1)}.{m.group(2)}" if m else ""          # 4.6.1.stable → templates folder
    num = m.group(1) if m else ""
    r.add(g, "Godot .NET" if mono else "Godot", bool(binp), REQ, short or gv, f"brew install --cask {cask}",
          note=where if binp else "")
    on_path = which(*(("godot-mono",) if mono else ("godot",)))
    app_bin = binp if binp and binp.endswith("Contents/MacOS/Godot") else "/Applications/Godot.app/Contents/MacOS/Godot"
    r.add(g, f"`{cask}` on PATH", bool(on_path), REQ, hint=f"ln -sf '{app_bin}' /opt/homebrew/bin/{cask}"
          if binp else f"brew install --cask {cask}   (creates /opt/homebrew/bin/{cask})")
    if want_ver and num:
        r.add(g, f"version as in TECH.md ({want_ver})", num.startswith(want_ver) or want_ver.startswith(num), REQ,
              num, f"brew upgrade --cask {cask}   (or download {want_ver} from godotengine.org)")
    if mono:
        dn = which("dotnet")
        dv = ver(run(["dotnet", "--version"])[1]) if dn else ""
        need = (9, 0) if "android" in platforms else (8, 0)
        r.add(g, f".NET SDK >= {need[0]}", bool(dv) and vtuple(dv)[:2] >= need, REQ, dv,
              "brew install dotnet   (or dotnet-install.sh --channel 9.0 into ~/.dotnet)",
              note="Android export of C# requires .NET 9+" if "android" in platforms else "")
        if "web" in platforms:
            r.add(g, "C# and Web", False, REQ, hint="pick godot (GDScript) or drop web from the platforms",
                  note="Godot 4 does not export C# projects to Web")

    # export templates of the same version
    ge = "Export"
    if short:
        tpl = GODOT_TPL / (short + (".mono" if mono else ""))
        have = tpl.is_dir() and read(tpl / "version.txt").strip() != ""
        url_v = short.replace(".stable", "-stable")
        r.add(ge, f"export templates {tpl.name}", have, REQ, read(tpl / "version.txt").strip(),
              f"download Godot_v{url_v}{'_mono' if mono else ''}_export_templates.tpz from "
              f"github.com/godotengine/godot/releases and unpack templates/* into '{tpl}'")
        if have:
            need = {"web": ["web_nothreads_release.zip"], "android": ["android_release.apk", "android_source.zip"],
                    "ios": ["ios.zip"], "windows": ["windows_release_x86_64.exe"], "mac": ["macos.zip"],
                    "linux": ["linux_release.x86_64"]}
            for p in platforms:
                files = need.get(p, [])
                if files:
                    miss = [f for f in files if not (tpl / f).exists()]
                    r.add(ge, f"template {p}", not miss, REQ, hint="reinstall the .tpz of this version",
                          note=", ".join(miss))
    check_mobile(r, platforms, jdk_major="17")

    # agent integrations
    found = check_mcp(r, servers, "Godot MCP (godot-ai or godot-mcp)", r"godot", REQ,
                      "open the project in Godot with the addons/godot_ai addon → Godot AI dock → Configure "
                      "(Claude Code); see references/environment.md", probed,
                      "the Godot editor must be open with the project and the Godot AI plugin enabled")
    for s in found:
        if "godot-ai" in s["name"] or "godot_ai" in s.get("target", ""):
            if s.get("type") == "http" or s.get("target", "").startswith("http"):
                r.add("Agent integrations", "godot-ai: new-format entry (stdio attach)", False, REC,
                      hint="Godot AI dock → Configure: rewrites the entry to `godot-ai attach`",
                      note="a bare http://…:8000/mcp is the v3 format; addon v4 (Godot 4.7+) needs godot-ai attach")
            if num and vtuple(num) < (4, 7):
                r.add("Agent integrations", "godot-ai v4 requires Godot 4.7+", False, REC, num,
                      f"brew install --cask {cask} (4.7+), then update the addon in the project")
    skills = [s for s in claude_skills(project) + claude_plugins() if "godot" in s.lower()]
    r.add("Agent integrations", "Claude Code skills/plugin for Godot", bool(skills), REC,
          ", ".join(skills)[:60], "there is no official plugin — look for one in the phase 4 research (plugin marketplaces, GitHub)")

    gq = "Tests and quality"
    gdf, gdl = which("gdformat"), which("gdlint")
    r.add(gq, "gdtoolkit (gdformat, gdlint)", bool(gdf and gdl), REQ,
          ver(run(["gdformat", "--version"])[1]) if gdf else "",
          "uv tool install 'gdtoolkit==4.*'   (or pipx install 'gdtoolkit==4.*')")
    has_proj = (project / "project.godot").exists()
    tf = [n for n in ("gut", "gdUnit4") if (project / "addons" / n).is_dir()]
    r.add(gq, "GUT or gdUnit4 in addons/", bool(tf) if has_proj else None, REQ, ", ".join(tf),
          "GUT of the same minor version as Godot: github.com/bitwes/Gut/releases → addons/gut",
          note="" if has_proj else "checked once project.godot exists")
    rc, _ = run(["lsof", "-nP", "-iTCP:6005", "-sTCP:LISTEN"], 5)
    r.add(gq, "GDScript LSP (editor, tcp 6005)", rc == 0, REC,
          hint="the LSP lives in the open Godot editor; without it, check with godot --headless --import",
          note="the editor is not listening on 6005 right now" if rc != 0 else "")


def check_mobile(r: Report, platforms: list[str], jdk_major: str) -> None:
    ge = "Export"
    if "android" in platforms:
        sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or str(HOME / "Library/Android/sdk")
        ok = Path(sdk, "platform-tools").is_dir() and Path(sdk, "build-tools").is_dir()
        r.add(ge, "Android SDK", ok, REQ, "present" if ok else "",
              "brew install --cask android-commandlinetools && sdkmanager 'platform-tools' "
              "'build-tools;35.0.1' 'platforms;android-36'", human=True,
              note="HUMAN: accept the SDK licenses" if not ok else sdk)
        jv = jdk(int(jdk_major))
        r.add(ge, f"JDK {jdk_major}", bool(jv), REQ, jv, f"brew install openjdk@{jdk_major}")
    if "ios" in platforms:
        rc, out = run(["xcodebuild", "-version"])
        r.add(ge, "Xcode (full)", rc == 0 and "Xcode" in out, REQ, ver(out),
              "App Store → Xcode, then sudo xcodebuild -license accept", human=True,
              note="HUMAN: Apple ID, sudo; publishing — Apple Developer $99/year")


# ------------------------------------------------------------------ Unity

def check_unity(r: Report, project: Path, platforms: list[str], want_ver: str,
                servers: list[dict], probed: bool) -> None:
    g = "Engine"
    cli = which("unity") or (str(HOME / ".unity/bin/unity") if (HOME / ".unity/bin/unity").exists() else None)
    r.add(g, "Unity CLI (`unity`)", bool(cli), REQ, first_line(run([cli, "--version"], env=UNITY_ENV)[1]) if cli else "",
          "brew install --cask unity-cli   (or curl -fsSL https://public-cdn.cloud.unity3d.com/hub/prod/cli/"
          "install.sh | UNITY_CLI_CHANNEL=beta bash)")
    hub = Path("/Applications/Unity Hub.app")
    r.add(g, "Unity Hub", hub.exists(), REC, app_version(hub), "brew install --cask unity-hub",
          note="the Hub CLI is deprecated; do everything via `unity`")
    editors: list[dict] = []
    if cli:
        rc, out = run([cli, "editors", "--installed", "--format", "json"], 30, env=UNITY_ENV)
        try:
            editors = json.loads(out[out.find("{"):]).get("data", []) if rc == 0 else []
        except (json.JSONDecodeError, ValueError):
            editors = []
    if not editors:
        for p in sorted(glob.glob("/Applications/Unity/Hub/Editor/*/Unity.app")):
            editors.append({"version": Path(p).parent.name, "modules": ""})
    vers = [e.get("version", "") for e in editors]
    r.add(g, "Unity 6 editor", any(v.startswith("6000") for v in vers), REQ, ", ".join(vers)[:60],
          "unity install lts --architecture arm64 -m webgl -m android -m ios --child-modules --yes --accept-eula",
          human=True, note="HUMAN: accept the EULA" if not vers else "")
    pv = re.search(r"m_EditorVersion:\s*(\S+)", read(project / "ProjectSettings/ProjectVersion.txt"))
    need_ver = pv.group(1) if pv else want_ver
    latest6 = sorted((v for v in vers if v.startswith("6000")), key=vtuple)[-1:] or [""]
    if need_ver:
        r.add(g, f"project version {need_ver} installed", any(v.startswith(need_ver) for v in vers), REQ,
              hint=f"unity install {need_ver} --architecture arm64 --yes --accept-eula")
    if cli:
        rc, out = run([cli, "license", "status", "--format", "json"], 30, env=UNITY_ENV)
        active = '"active": true' in out
        r.add(g, "Unity sign-in and license", active, REQ,
              hint="unity auth login   then   unity license activate --personal --accept-eula", human=True,
              note="HUMAN: sign in in the browser, accept the EULA" if not active else "")
    mods = " ".join(str(e.get("modules", "")) for e in editors if str(e.get("version", "")).startswith(need_ver or "6000"))
    ge = "Export"
    for p, key, mod in (("web", "Web", "webgl"), ("android", "Android", "android"), ("ios", "iOS", "ios"),
                        ("windows", "Windows", "windows-mono")):
        if p in platforms:
            r.add(ge, f"{key} module", key.lower() in mods.lower(), REQ,
                  hint=f"unity install-modules --editor-version {need_ver or latest6[0] or 'lts'} -m {mod} --child-modules --yes")
    if "ios" in platforms:
        check_mobile(r, ["ios"], jdk_major="17")

    gi = "Agent integrations"
    plug = [p for p in claude_plugins() if p.lower().startswith("unity@")] + \
           [s for s in claude_skills(project) if s.lower() == "unity"]
    r.add(gi, "Unity plugin for Claude Code", bool(plug), REQ, ", ".join(plug),
          "claude plugin install unity@claude-plugins-official   (loads in a new session or after /reload-plugins)")
    check_mcp(r, servers, "Unity MCP", r"unity", REQ,
              "unity mcp configure claude-code   (without a Unity AI subscription — CoplayDev MCP for Unity, see environment.md)",
              probed, "needs an open Unity editor with the com.unity.pipeline package and no compile errors")

    gq = "Tests and quality"
    has_proj = (project / "ProjectSettings/ProjectVersion.txt").exists()
    manifest = read(project / "Packages/manifest.json")
    for pkg, level, why in (("com.unity.test-framework", REQ, "unity test"),
                            ("com.unity.pipeline", REQ, "live editor control: unity command, unity mcp")):
        r.add(gq, pkg, (pkg in manifest) if has_proj else None, level,
              hint=("unity pipeline install --project-path ." if "pipeline" in pkg else
                    "add the line to dependencies in Packages/manifest.json"),
              note=why if has_proj else "checked once the project exists")
    es = read(project / "ProjectSettings/EditorSettings.asset")
    vcs = read(project / "ProjectSettings/VersionControlSettings.asset") + es
    r.add(gq, "Asset Serialization: Force Text", ("m_SerializationMode: 2" in es) if has_proj else None, REQ,
          hint="Project Settings → Editor → Asset Serialization → Force Text")
    r.add(gq, "Version Control: Visible Meta Files", ("Visible Meta Files" in vcs) if has_proj else None, REQ,
          hint="Project Settings → Version Control → Mode: Visible Meta Files")
    rc, out = run(["git", "config", "--get", "merge.unityyamlmerge.driver"], cwd=project if project.is_dir() else None)
    r.add(gq, "git smart merge (UnityYAMLMerge)", rc == 0 and bool(out), REC,
          hint="git config merge.unityyamlmerge.name 'Unity SmartMerge' && git config merge.unityyamlmerge.driver "
               "\"'<Unity.app>/Contents/Helpers/UnityYAMLMerge' merge -p %O %B %A %A\" + in .gitattributes: "
               "*.unity *.prefab *.asset merge=unityyamlmerge")


# ------------------------------------------------------------------ Unreal

def check_unreal(r: Report, platforms: list[str], want_ver: str, servers: list[dict], probed: bool) -> None:
    g = "Engine"
    launcher = Path("/Applications/Epic Games Launcher.app")
    r.add(g, "Epic Games Launcher", launcher.exists(), REQ, app_version(launcher),
          "brew install --cask epic-games", human=True, note="HUMAN: sign in to the Epic account")
    ues = sorted(glob.glob("/Users/Shared/Epic Games/UE_*") + glob.glob(str(HOME / "Epic Games/UE_*")))
    r.add(g, "Unreal Engine 5", bool(ues), REQ, ", ".join(Path(u).name for u in ues),
          "Epic Games Launcher → Unreal Engine → Library → + → version → Install", human=True,
          note="HUMAN: install only via the launcher GUI, 40–100+ GB")
    if want_ver and ues:
        r.add(g, f"version as in TECH.md ({want_ver})", any(want_ver in u for u in ues), REQ,
              hint="install this version in the launcher")
    rc, out = run(["xcodebuild", "-version"])
    r.add(g, "Xcode (full)", rc == 0 and "Xcode" in out, REQ, ver(out),
          "brew install xcodes && xcodes install <version from the UE requirements>", human=True,
          note="match the Xcode version to the UE requirements (research/environment.md)")
    free = shutil.disk_usage(str(HOME)).free // 2**30
    r.add(g, "free disk space >= 100 GB", free >= 100, REC, f"{free} GB", "free up space")
    if "windows" in platforms:
        r.add("Export", "Windows build from a Mac", False, REC, hint="a Windows PC is needed to build for Windows",
              note="UE does not build Windows on macOS")
    check_mcp(r, servers, "Unreal MCP", r"unreal", REC,
              "Edit → Plugins → Model Context Protocol (experimental, UE 5.8) or community unreal-mcp",
              probed)
    check_mobile(r, platforms, jdk_major="17")


# ------------------------------------------------------------------ Web

def check_web(r: Report, project: Path, servers: list[dict], probed: bool) -> None:
    g = "Engine"
    nv = ver(run(["node", "--version"])[1]) if which("node") else ""
    r.add(g, "node >= 20.19 (Vite 8)", bool(nv) and vtuple(nv) >= (20, 19), REQ, nv,
          "brew install node   (or nvm install --lts)")
    r.add(g, "npx", bool(which("npx")), REQ, hint="comes with npm")
    pkg = {}
    try:
        pkg = json.loads(read(project / "package.json") or "{}")
    except json.JSONDecodeError:
        pass
    has_proj = bool(pkg)
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    libs = [d for d in ("three", "phaser", "pixi.js", "@babylonjs/core", "playcanvas") if d in deps]
    if has_proj:
        r.add(g, "game library", bool(libs), REC, ", ".join(f"{d} {deps[d]}" for d in libs),
              "npm i three   |   npm i phaser   |   npm i pixi.js   |   npm i @babylonjs/core")
    gq = "Tests and quality"
    for d, level, hint in (("vite", REQ, "npm create vite@latest . -- --template vanilla-ts"),
                           ("typescript", REQ, "npm i -D typescript"),
                           ("playwright", REQ, "npm i -D playwright && npx playwright install chromium"),
                           ("vitest", REQ, "npm i -D vitest"),
                           ("eslint", REQ, "npm init @eslint/config@latest"),
                           ("prettier", REC, "npm i -D prettier")):
        ok = (d in deps or (d == "playwright" and "@playwright/test" in deps)) if has_proj else None
        r.add(gq, d, ok, level, deps.get(d, ""), hint, note="" if has_proj else "checked once package.json exists")

    # the browser revision the project's playwright expects
    if has_proj and not (project / "node_modules").is_dir():
        r.add(gq, "dependencies installed (node_modules)", False, REQ, hint="npm install")
    bj = project / "node_modules/playwright-core/browsers.json"
    if bj.exists():
        try:
            revs = {b["name"]: b["revision"] for b in json.loads(read(bj))["browsers"]}
        except (json.JSONDecodeError, KeyError):
            revs = {}
        for name, folder in (("chromium", "chromium"), ("chromium-headless-shell", "chromium_headless_shell")):
            rev = revs.get(name)
            if rev:
                r.add(gq, f"browser {name}-{rev} for the project's playwright", (PW_CACHE / f"{folder}-{rev}").is_dir(), REQ,
                      hint="npx playwright install chromium   (in the project root)")
    else:
        have = sorted(p.name for p in PW_CACHE.glob("chromium*")) if PW_CACHE.is_dir() else []
        r.add(gq, "Playwright browsers in the cache", bool(have) if not has_proj else None, REC, ", ".join(have)[:60],
              "npx playwright install chromium   (in the project, after npm i -D playwright)")
    check_mcp(r, servers, "Playwright MCP (browser for the agent)", r"playwright", REC,
              "claude mcp add playwright -- npx @playwright/mcp@latest", probed)


# ------------------------------------------------------------------ Defold

def check_defold(r: Report, project: Path, platforms: list[str], servers: list[dict], probed: bool) -> None:
    g = "Engine"
    app = Path("/Applications/Defold.app")
    r.add(g, "Defold", app.exists(), REQ, app_version(app), "brew install --cask defold")
    jv = jdk(25)
    r.add(g, "JDK 25 (for bob.jar)", bool(jv), REQ, jv, "brew install openjdk@25",
          note="the editor ships its own JDK; 25 is needed for bob.jar from the CLI")
    bobs = [p for p in (project / "bob.jar", project / "tools/bob.jar", HOME / ".local/share/defold/bob.jar") if p.exists()]
    r.add(g, "bob.jar (CLI build)", bool(bobs), REQ, str(bobs[0]) if bobs else "",
          "download bob.jar of the same version as the editor: github.com/defold/defold/releases → tools/bob.jar")
    check_mcp(r, servers, "Defold MCP", r"defold", REC, "community: github.com/Fulviuus/defold-mcp (phase 4 research)",
              probed)
    check_mobile(r, platforms, jdk_major="17")


# ------------------------------------------------------------------ Bevy

def check_bevy(r: Report, platforms: list[str], servers: list[dict], probed: bool) -> None:
    g = "Engine"
    for name, cmd in (("cargo", ["cargo", "--version"]), ("rustc", ["rustc", "--version"])):
        r.add(g, name, bool(which(name)), REQ, ver(run(cmd)[1]) if which(name) else "",
              "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y")
    ru = which("rustup")
    r.add(g, "rustup", bool(ru), REC, ver(run(["rustup", "--version"])[1]) if ru else "", "brew install rustup")
    if "web" in platforms:
        rc, out = run(["rustup", "target", "list", "--installed"]) if ru else (1, "")
        r.add("Export", "wasm32-unknown-unknown target", "wasm32-unknown-unknown" in out, REQ,
              hint="rustup target add wasm32-unknown-unknown")
    r.add(g, "bevy_cli (`bevy`)", bool(which("bevy")), REC,
          hint="cargo install --git https://github.com/TheBevyFlock/bevy_cli --locked bevy_cli")
    lsp = [p for p in claude_plugins() if "rust-analyzer" in p]
    r.add("Agent integrations", "rust-analyzer LSP (Claude Code plugin)", bool(lsp), REC, ", ".join(lsp),
          "claude plugin install rust-analyzer-lsp@claude-plugins-official")
    check_mcp(r, servers, "Bevy BRP MCP", r"bevy|brp", REC,
              "cargo install bevy_brp_mcp && claude mcp add bevy-brp -- bevy_brp_mcp   (+ bevy_brp_extras in the game)",
              probed)


# ------------------------------------------------------------------ output

def print_table(r: Report, engine: str | None, src: str, dim: str, platforms: list[str], project: Path,
                probed: bool) -> None:
    print(f"envcheck — engine: {engine or 'not set (common checks only)'}{src}; "
          f"dimension: {dim or 'not set'}; platforms: {', '.join(platforms) or 'not set'}; project: {project}")
    if not probed:
        print("  (claude mcp list was not called — MCP connection status unknown)")
    group = None
    for it in r.items:
        if it["group"] != group:
            group = it["group"]
            print(f"\n{group}")
        mark = "·" if it["ok"] is None else ("✓" if it["ok"] else ("✗" if it["level"] == REQ else "!"))
        lvl = "req. " if it["level"] == REQ else "rec. "
        line = f"  {mark} {lvl} {it['name']:<44} {it['version'][:28]:<28}"
        tail = it["hint"] if (it["ok"] is False and it["hint"]) else it["note"]
        if it["ok"] is False and it["note"] and it["hint"]:
            tail = f"{it['hint']}   [{it['note']}]"
        print((line + ("  " + tail if tail else "")).rstrip())
    miss_req = [i["name"] for i in r.items if i["ok"] is False and i["level"] == REQ]
    miss_rec = [i["name"] for i in r.items if i["ok"] is False and i["level"] == REC]
    pend = [i["name"] for i in r.items if i["ok"] is None]
    humans = [i["name"] for i in r.items if i["human"]]
    print("\nLegend: ✓ present · ✗ missing (required) · ! missing (recommended) · · checked later")
    if miss_req:
        print(f"MISSING required ({len(miss_req)}): {', '.join(miss_req)}")
    if miss_rec:
        print(f"Recommended to add ({len(miss_rec)}): {', '.join(miss_rec)}")
    if pend:
        print(f"Checked after the hello project: {', '.join(pend)}")
    if humans:
        print(f"Needs a human (guide them one action at a time): {', '.join(humans)}")
    print("Result: everything required is present" if not miss_req else "Result: setup not ready (exit 1)")


def main() -> int:
    ap = argparse.ArgumentParser(description="studioigor environment check")
    ap.add_argument("--engine", choices=ENGINES)
    ap.add_argument("--dimension", choices=("2d", "3d"), type=str.lower)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--project", default=".")
    ap.add_argument("--platforms", default=None, help="comma-separated: web,android,ios,windows,mac,linux")
    ap.add_argument("--no-claude", action="store_true", help="do not call `claude mcp list`")
    a = ap.parse_args()

    project = Path(a.project).resolve()
    tech = read(project / ".studioigor/TECH.md")
    engine, src = a.engine, ""
    if not engine:
        e = field(tech, "ENGINE").split()[0].lower() if field(tech, "ENGINE") else ""
        if e in ENGINES:
            engine, src = e, " (from TECH.md)"
    want_ver = ver(field(tech, "ENGINE VERSION"))
    dim = a.dimension or dimension(field(tech, "DIMENSION"))
    if a.platforms is not None:
        platforms = [p.strip().lower() for p in a.platforms.split(",") if p.strip()]
    else:
        platforms = parse_platforms(field(tech, "PLATFORMS"))

    probe = not a.no_claude
    servers = mcp_servers(project, probe)
    probed = probe and bool(which("claude"))

    r = Report()
    check_common(r, engine, dim)
    if engine in ("godot", "godot-mono"):
        check_godot(r, engine == "godot-mono", project, platforms, want_ver, servers, probed)
    elif engine == "unity":
        check_unity(r, project, platforms, want_ver, servers, probed)
    elif engine == "unreal":
        check_unreal(r, platforms, want_ver, servers, probed)
    elif engine == "web":
        check_web(r, project, servers, probed)
    elif engine == "defold":
        check_defold(r, project, platforms, servers, probed)
    elif engine == "bevy":
        check_bevy(r, platforms, servers, probed)

    order = ["General", "Engine", "Export", "Agent integrations", "Tests and quality"]
    r.items.sort(key=lambda i: order.index(i["group"]) if i["group"] in order else 99)
    miss_req = [i["name"] for i in r.items if i["ok"] is False and i["level"] == REQ]
    if a.json:
        print(json.dumps({
            "engine": engine, "dimension": dim, "platforms": platforms, "project": str(project), "ok": not miss_req,
            "missing_required": miss_req,
            "missing_recommended": [i["name"] for i in r.items if i["ok"] is False and i["level"] == REC],
            "needs_human": [i["name"] for i in r.items if i["human"]],
            "mcp": servers, "mcp_probed": probed, "items": r.items,
        }, ensure_ascii=False, indent=2))
    else:
        print_table(r, engine, src, dim, platforms, project, probed)
    return 0 if not miss_req else 1


if __name__ == "__main__":
    sys.exit(main())
