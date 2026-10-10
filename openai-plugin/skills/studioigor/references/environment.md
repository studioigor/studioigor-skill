# Environment — phase 4

Read in phase 4, once the engine is chosen. Covers: researching the best setup, "best
setup" checklists per engine (installation, what the human does, verification), MCP in Claude Code,
the hello project, ENV.md commands, how the agent sees the game, minimal tests, pitfalls.

**Contents:** 1. Order · 2. Research · 3. Installation rules · 4. MCP in Claude Code ·
5. Godot · 6. Godot .NET · 7. Unity · 8. Web · 9. Unreal · 10. Defold, Bevy ·
11. Blender (3D) and git-lfs · 12. Hello project and ENV.md · 13. How the agent sees the game ·
14. Tests — the minimum · 15. Pitfalls

## 1. Order

1. Research → `.studioigor/research/environment.md` (section 2).
2. `python3 <skill>/scripts/envcheck.py` (takes engine and platforms from
   TECH.md) — what is there, what is missing, a command for each gap.
3. Install everything yourself using the engine checklist. The human only does logins, licenses, sudo, GUI
   (section 3). Before installing, tell the user in one message what goes in, one line per item; for a
   3D game the list includes Blender (section 11), and the user may decline it. Repeat `envcheck.py`
   until exit 0: this is the phase gate.
4. `studio.py gitignore <engine> --lfs`.
5. Hello project + capture template + commands in ENV.md (section 12).
6. `studio.py verify` — runs TEST and CAPTURE and sets `VERIFIED: yes`.
7. Start RUN in the background so the user sees the window; "do you see it?" → `tick` + `decide --by user`.
8. Tables "Installed" and "Agent integrations" in ENV.md (one line per item), `commit`.

The goal is a complete setup, not a minimal one: the engine at the right version, CLI in PATH, Claude Code
plugin and skills, editor MCP (connected and verified), a test framework,
linter/formatter, export modules for the platforms in TECH.md, git-lfs.

## 2. Researching the best setup

Agent tooling changes monthly (MCP servers, plugins, CLIs in beta). Before
installing, check, ≤ 60–80 lines, with a date and links:

- engine version: latest stable/LTS, does it match TECH.md; installation method (brew
  cask, engine CLI, archive);
- editor MCP: which one is currently best for Claude Code (stars, last release, list of
  tools, can it screenshot the game), engine version requirements, is it paid;
- Claude Code plugins and skills for the engine (`/plugin`, marketplaces, GitHub);
- test framework and its version for this engine version; linter/formatter;
- `claude mcp add` syntax (`claude mcp add --help` is the primary source);
- "What this changes": what we install, with what, what the human does.

Found an MCP, plugin or CLI better than described below — install the better one and write a proposal:
`learn.py propose --kind tool --phase 4 --title … --what … --when … --why … --source <link>`.
Installation pitfalls that ate more than 10 minutes — also as a proposal (`--kind fix`).

## 3. Installation rules

- Install yourself first: `brew install …`, `brew install --cask …`, engine CLI, `npm`, `uv tool`.
- An existing `/Applications/<App>.app` not from brew breaks `brew install --cask`. Don't
  use `--force` without consent: offer a symlink to the existing app or an update.
- Casks with a `.pkg` (`unity`, `dotnet-sdk`, `temurin`) ask for the sudo password — that is a human step.
  Prefer options without sudo (the `dotnet` formula, `openjdk@N`, engine CLI).
- Licenses and EULAs (Unity, Android SDK, Xcode) are accepted by the human: ask for an explicit "yes",
  then run the command with `--accept-eula` / `sdkmanager --licenses`.
- **A human step is one action at a time**:
  "Do one thing: <action>. Where: <window/URL>. When you're done, type "done"."
  After "done" — a verification command. If it fails — the next hint, not a wall of text.
- Write the version of each item into the "Installed" table in ENV.md; `HOMEBREW_NO_AUTO_UPDATE=1`
  speeds up a series of installs.

## 4. MCP in Claude Code

Syntax checked against `claude mcp add --help` (Claude Code 2.1.283, 2026-09-27):

```bash
claude mcp add [-s local|user|project] [-t stdio|http|sse] <name> [-e KEY=val] [-H "Header: v"] <command|url> [args…]
claude mcp add -s user godot -e GODOT_PATH=/opt/homebrew/bin/godot -- npx @coding-solo/godot-mcp   # stdio: command after --
claude mcp add -t http -s user name https://host/mcp                                              # http
claude mcp add-json name '{"command":"…","args":["…"]}'
claude mcp list          # all servers + health check (✔ Connected / ✘ Failed)
claude mcp get <name>    # details of one
claude mcp remove <name> [-s <scope>]
```

`-e` and `-H` accept several values in a row: write them after the name, and the server command —
after `--`, as in the `--help` examples.

Scope: `local` (default) — this project only, private, in `~/.claude.json`;
`project` — `.mcp.json` in the repo (committed; on first launch Claude Code asks for
approval); `user` — all projects. Install the engine editor MCP in `user`, game-specific ones —
in `project`. A new server is picked up in a new Claude Code session; tell the user to
restart the session or reconnect via `/mcp` (UNVERIFIED whether `/mcp` is enough).
Verifying any MCP: `claude mcp list` shows `✔ Connected` with the editor open, and
one real tool call (for example, the scene tree) succeeds.

## 5. Godot (GDScript) — best setup

| item | installation | verification | human |
|---|---|---|---|
| Godot at the version from TECH.md | `brew install --cask godot` (or an archive from godotengine.org → `/Applications`) | `godot --version` | no |
| CLI in PATH | the cask creates `/opt/homebrew/bin/godot`; otherwise `ln -sf /Applications/Godot.app/Contents/MacOS/Godot /opt/homebrew/bin/godot` | `which godot` | no |
| export templates of **the same** version | see below | `cat ~/Library/Application\ Support/Godot/export_templates/<v>.stable/version.txt` | no |
| Godot MCP | godot-ai (below) | `claude mcp list` → godot-ai ✔ with the editor open | one Configure click in the dock |
| GUT (or gdUnit4) | addon of the same minor version as Godot | TEST from ENV.md, exit 0 | no |
| gdtoolkit | `uv tool install "gdtoolkit==4.*"` (or `pipx install`) | `gdlint --version`, `gdformat --check .` | no |
| script checking | built in | `godot --headless --path . --import` with no errors in the log | no |
| Android | Android SDK + JDK 17 (`brew install openjdk@17`, `android-commandlinetools`), paths in Editor Settings → Export → Android | `envcheck.py` | SDK licenses |
| iOS | Xcode from the App Store | `xcodebuild -version` | Apple ID, sudo |

Export templates (≈ 1.2 GB; folder named by the version from `godot --version`):

```bash
V=4.7.2   # from TECH.md; for x.y.0 the tag has no patch: 4.7
TPL="$HOME/Library/Application Support/Godot/export_templates/${V}.stable"
curl -L -o /tmp/tpl.tpz "https://github.com/godotengine/godot/releases/download/${V}-stable/Godot_v${V}-stable_export_templates.tpz"
mkdir -p "$TPL" && unzip -j -o /tmp/tpl.tpz 'templates/*' -d "$TPL" && cat "$TPL/version.txt"
```

**godot-ai** (github.com/hi-godot/godot-ai, MIT; v4.2.3 as of 2026-09-27): 46 tools —
scenes, nodes, scripts with validation, signals, UI, materials, animation, `project_run`,
`logs_read`, `test_run`, `editor_screenshot` (the editor viewport or a frame of the running game).
How it works: Claude Code → `godot-ai attach` (stdio) → Python server (HTTP :8000) →
editor plugin (WebSocket :9500). The plugin starts the server, so the MCP lives only
while the editor with this project is open. Requires `uv` and **Godot 4.7+** for v4.

1. Addon from GitHub Releases (the release package, not the sources) → `addons/godot_ai/plugin.cfg`.
2. Enable the plugin: `[editor_plugins] enabled=PackedStringArray("res://addons/godot_ai/plugin.cfg")`
   in `project.godot` (or Project Settings → Plugins).
3. Open the editor from the project folder: `godot -e --path .` (in the background).
4. Human step: "Do one thing: in the Godot window, Godot AI dock → Configure next to Claude
   Code". The dock itself runs `claude mcp add … godot-ai … godot-ai attach --port 8000
   --ws-port 9500` (scope — Editor Settings → `godot_ai/mcp_client_scope`). Don't compose the entry
   by hand: it contains the addon's version and parameters (there is "Run this manually" in the dock).
5. New Claude Code session → `claude mcp list` → `godot-ai ✔`.

**Diagnosing "godot-ai: ECONNREFUSED"**:
1. Editor closed → open the project with the plugin enabled. Ports:
   `lsof -nP -iTCP:8000 -iTCP:9500 -sTCP:LISTEN` — empty means the server is not running.
2. An entry like `http://127.0.0.1:8000/mcp` (type http) is the v3 format. The v4 addon doesn't
   authorize that way: click Configure in the dock, it replaces the entry with `godot-ai attach`.
3. Version: v4 requires Godot 4.7+. Installed Godot is older (e.g. 4.6) → either update Godot (and the templates),
   or install the latest v3 release for 4.6. The best setup is to update.
4. `uv --version` — without uv the server doesn't start. Startup errors are in the Godot AI dock and in the
   editor output (`logs_read` is unavailable while there's no connection — look at the Godot console).
5. After fixing — a new session, `claude mcp list`, a trial call "show the scene tree".

Alternative without the editor: Coding-Solo/godot-mcp (`claude mcp add -s user godot -e
GODOT_PATH=$(which godot) -- npx @coding-solo/godot-mcp`) — runs the project and shows debug
output, no screenshots (from research 2026-09-27, UNVERIFIED here).

GUT: version for the Godot minor version (per the GUT README: 9.7.x — 4.7, 9.6.x — 4.6).
`curl -L -o /tmp/gut.zip https://github.com/bitwes/Gut/archive/refs/tags/v9.6.1.zip`,
unpack and copy `addons/gut` into the project. For the CLI the plugin need not be enabled (verified on
4.6.1 + GUT 9.6.1: exit 0 when green, 1 when red). The GDScript LSP is served by an open
editor (tcp 6005); without the editor, errors show up via `--import` and via CAPTURE (Logger).
No official GDScript plugin for Claude Code was found as of 2026-09-27 — check in the research.

## 6. Godot .NET (C#) — differences

`brew install --cask godot-mono` (pulls the `dotnet-sdk` cask with a `.pkg` → sudo) or the formula
`brew install dotnet`. .NET 8+, for Android .NET 9+. Templates — `Godot_v<V>-stable_mono_export_templates.tpz`
into the folder `<V>.stable.mono`. Run `dotnet build` before launching. **Web does not export.**
For C#, godot-ai only writes files; look for compile errors in `dotnet build`.

## 7. Unity 6 — best setup

All three are required: the `unity` CLI + the Unity plugin for Claude Code
(`claude plugin install unity@claude-plugins-official`) + Unity MCP. Create the project with
`unity projects new <name>` (non-interactive; flags — `unity projects new --help`), open it with
`unity open`; editor — `unity command`, build — `unity build`, tests — `unity test`.
The Hub CLI is deprecated since Hub 3.18 — don't use it.

| item | installation | verification | human |
|---|---|---|---|
| `unity` CLI | `brew install --cask unity-cli` or `curl -fsSL https://public-cdn.cloud.unity3d.com/hub/prod/cli/install.sh \| UNITY_CLI_CHANNEL=beta bash` | `unity --version` | no |
| login | `unity auth login` (prints a URL) | `unity auth status --format json` | login in the browser |
| Personal license | `unity license activate --personal --accept-eula` after a "yes" to the EULA | `unity license status --format json` → `"active": true` | consent |
| LTS editor + modules | `unity releases --stream lts --limit 5 --format json`; `unity install <version> --architecture arm64 -m webgl -m android -m ios --child-modules --yes --accept-eula` | `unity editors --installed --format json` | EULA |
| Claude Code plugin | `claude plugin install unity@claude-plugins-official` (fallback: `claude plugin marketplace add Unity-Technologies/unity-agent-plugin` → `unity@unity-agent-plugin`) | `claude plugin list` shows `unity`; its commands are available in a new session | no |
| Pipeline package | `unity pipeline install --project-path .` | `unity status` → `ready` with the editor open | no |
| Unity MCP | `unity mcp configure claude-code` | `claude mcp list` → `unity-editor-mcp ✔` with the editor open | no |
| Unity Test Framework | `com.unity.test-framework` in `Packages/manifest.json` (a line in `dependencies`, version from the research), folder `Assets/Tests/EditMode` with an asmdef | TEST exit 0 | no |
| git | Force Text and Visible Meta Files (Project Settings → Editor / Version Control; in the files `ProjectSettings/EditorSettings.asset` `m_SerializationMode: 2`) + smart merge | `envcheck.py` | no |

`unity mcp configure claude-code` runs `claude mcp add --scope user --transport stdio
unity-editor-mcp unity mcp` (verified with `--dry-run` on this machine). This MCP is built into the CLI and
works through `com.unity.pipeline`; whether it needs a Unity AI subscription is UNVERIFIED.
The official MCP of the AI Assistant package (`com.unity.ai.assistant`) on Personal requires a
Unity AI subscription (Unity's statement, May 2026) — that is a money decision, ask. The free replacement is
CoplayDev "MCP for Unity" (MIT): Package Manager → Add from git URL
`https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main`, then Window → MCP for
Unity → Configure for Claude Code (check the details in the research). Order: `unity mcp` first;
if it doesn't work — CoplayDev.

Smart merge (path verified on 6000.6.2f1):
```bash
U="/Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/Helpers/UnityYAMLMerge"
git config merge.unityyamlmerge.name "Unity SmartMerge"
git config merge.unityyamlmerge.driver "'$U' merge -p %O %B %A %A"
printf '*.unity merge=unityyamlmerge eol=lf\n*.prefab merge=unityyamlmerge eol=lf\n*.asset merge=unityyamlmerge eol=lf\n' >> .gitattributes
```

## 8. Web (Vite + TypeScript) — best setup

| item | installation | verification |
|---|---|---|
| Node ≥ 20.19 (Vite 8) | `brew install node` or `nvm install --lts` | `node --version` |
| scaffold | `npm create vite@latest web-tmp -- --template vanilla-ts`, then `rsync -a --ignore-existing web-tmp/ ./ && rm -rf web-tmp` (doesn't overwrite `.studioigor/` and `.gitignore`) | `npm run build` |
| library | `npm i phaser` · `npm i three @dimforge/rapier3d-compat` · `npm i @babylonjs/core @babylonjs/havok` · `npm i pixi.js` | the import builds |
| dev tools | `npm i -D typescript vitest playwright eslint @eslint/js typescript-eslint prettier` | `npx tsc --noEmit`, `npx vitest run` |
| Playwright browser | `npx playwright install chromium` **in the project root** | CAPTURE passes |
| linter | `eslint.config.js`: `import js from '@eslint/js'; import ts from 'typescript-eslint'; export default ts.config(js.configs.recommended, ...ts.configs.recommended);` | `npx eslint src` |
| Playwright MCP (a browser for the agent) | `claude mcp add -s user playwright -- npx @playwright/mcp@latest` | `claude mcp list` |

`npm init @eslint/config` is interactive — write the config as a file. Models mix up Phaser 3/4,
Pixi 7/8, Three imports (`three/addons/…`): the version in `package.json` is the source of truth.
Capture hooks (details in `references/code.md`): `?seed=` for all randomness,
`window.__metrics = {completed, events, …}`, `window.__GAME__ = {ready: true}` after loading.

## 9. Unreal 5 — what gets automated

| automatic | human only |
|---|---|
| `brew install --cask epic-games` | Epic account login; installing the engine in the launcher (Library → + → version → Options: iOS/Android) |
| build: `RunUAT.sh BuildCookRun -project=… -platform=Mac -clientconfig=Shipping -build -cook -stage -pak -archive -archivedirectory=…` | Xcode of the required version (Apple ID) — Xcode versions are pinned per UE release |
| tests: `UnrealEditor <p>.uproject -ExecCmds="Automation RunTests <filter>;Quit" -unattended -nullrhi -stdout` | Blueprint and `.uasset` edits — GUI (the agent does C++, `.ini`, editor Python scripts) |
| C++ compilation (minutes) | MCP: the experimental Model Context Protocol plugin in UE 5.8 (Edit → Plugins) — the human enables it |

Default path: `/Users/Shared/Epic Games/UE_<version>/` (UNVERIFIED for 5.8). Disk
budget 100+ GB. Unreal does not make a Windows build from a Mac.

## 10. Defold and Bevy — briefly

**Defold:** `brew install --cask defold`; `brew install openjdk@25` (for `bob.jar`; the editor
ships its own JDK); `bob.jar` of the same version as the editor → `tools/bob.jar` (GitHub releases
defold/defold). BUILD: `$JAVA25/bin/java -jar tools/bob.jar --archive --platform wasm-web
--variant debug --bundle-output build/web resolve build bundle`. Frames — web bundle +
`capture.mjs --dir build/web/<name>`. LLM docs: `defold.com/llms.txt`. MCP — community
(Fulviuus/defold-mcp), check in the research.
**Bevy:** rustup, `cargo`, `rustup target add wasm32-unknown-unknown` for web, `bevy_cli`
(alpha), the `rust-analyzer-lsp` Claude Code plugin, `bevy_brp_mcp` + `bevy_brp_extras` in the game
(screenshots and input via BRP). Pin the Bevy version in `Cargo.toml` and read the migration guide:
the API changes every 0.x.

## 11. Blender (3D) and git-lfs

- **A 3D game on any engine → Blender LTS is recommended** (`brew install --cask blender`; CLI
  `/Applications/Blender.app/Contents/MacOS/Blender`). The agent drives it with Python scripts only:
  `Blender -b -P script.py`, templates in `<skill>/scripts/templates/blender/`. No Blender MCP is
  needed: script → GLB export → preview render → you look at the PNG covers the whole loop, and the
  lead and subagents run it in parallel. Verification — the example prop builds and exports:
  ```bash
  B=/Applications/Blender.app/Contents/MacOS/Blender; T=<skill>/scripts/templates/blender
  $B -b --factory-startup --python-exit-code 1 -P $T/example_prop.py -- --out-dir "$(mktemp -d)"
  ```
- The user declined Blender (or it won't install) → `decide "3D without Blender" --by user`
  and make 3D without it (`assets.md` §4). Don't ask again.
- A 2D game → Blender only if the asset strategy (phase 5) needs 3D→2D renders; by default
  2D is procedural plus image generation, if available.
- A Blender MCP the user already has connected may be used by the lead for a quick look.
  Don't install one.
- git-lfs: `brew install git-lfs && git lfs install`, then
  `studio.py gitignore <engine> --lfs` (the engine's `.gitignore` + LFS for models, textures, audio).

## 12. Hello project and ENV.md

Hello project — game root = engine root (with `.studioigor/` next to it). The minimum that
proves the setup: one scene with a camera, an object and input-driven movement; a `Metrics`
autoload (Godot) or `window.__metrics` (web); the capture template; one test of pure logic;
an export preset for the first platform. Layout — per `references/code.md`.

- Godot: `project.godot` (renderer: web → Compatibility, mobile → Mobile, PC 3D →
  Forward+), `scenes/main.tscn`, `autoload/metrics.gd`, `tools/capture.gd` (template),
  `tools/inputs/hello.json`, `tests/test_smoke.gd`, `addons/gut`, `export_presets.cfg`.
  After creating the files: `godot --headless --path . --import` (`.uid` files appear — commit them).
  Minimal web preset (verified on 4.6.1, Godot fills in the rest itself):
  ```ini
  [preset.0]
  name="Web"
  platform="Web"
  runnable=true
  export_filter="all_resources"
  export_path="build/web/index.html"
  [preset.0.options]
  variant/thread_support=false
  ```
- Web: Vite scaffold, `src/main.ts`, `tools/capture.mjs` (template), `tests/smoke.test.ts`.
- Unity: project via the `unity` CLI (LTS, URP template), `Assets/Editor/StudioCapture.cs` (template),
  `Assets/Scenes/Main.unity`, `Assets/Tests/EditMode/` with an asmdef.

Templates — `<skill>/scripts/templates/{godot,web,unity}/`; flag
details are in the header of each file.

**ENV.md commands.** From the project root, non-interactive, with a meaningful exit code; CAPTURE
writes to `.studioigor/captures/<name>/`. The Godot column was run through `studio.py verify` (4.6.1,
GUT 9.6.1); web CAPTURE — `capture.mjs` on chromium 1243; the Unity column is from the CLI docs, not
run:

| | Godot | Web | Unity |
|---|---|---|---|
| RUN | `godot --path . res://scenes/main.tscn` | `npm run dev -- --open` | `unity open .` |
| TEST | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit` | `npx tsc --noEmit && npx vitest run` | `unity test . --mode EditMode --report-format junit --output Logs/tests.xml` |
| BUILD | `mkdir -p build/web && godot --headless --path . --export-release "Web" build/web/index.html` | `npm run build` | `unity build . --target StandaloneOSX --output-path Build/Game.app` |
| CAPTURE | `godot --path . --resolution 1280x720 --fixed-fps 60 --script res://tools/capture.gd -- --out .studioigor/captures/hello --duration 5 --every 1` | `npm run build && node tools/capture.mjs --dir dist --out .studioigor/captures/hello --duration 5 --every 1` | `unity run . -- -executeMethod StudioCapture.Run -studioScene Assets/Scenes/Main.unity -studioOut .studioigor/captures/hello` |
| EDITOR | `godot -e --path .` | `none — the code is in the repository` | `unity open .` |

Bevy: RUN `cargo run`, TEST `cargo test`, CAPTURE — a game flag `--capture <folder>` with
`Screenshot::primary_window()`. Defold: CAPTURE = bob web bundle + `capture.mjs`.
Unreal: CAPTURE — `-ExecCmds="HighResShot 1280x720"` with rendering, and a copy from
`Saved/Screenshots/` (UNVERIFIED).

Then:
```bash
S=<skill>/scripts/studio.py
python3 $S gitignore godot --lfs
python3 $S verify            # TEST and CAPTURE; needs a fresh image in .studioigor/captures/
```
Look at the frames yourself (Read `sheet.png`). Then RUN in the background (Bash `run_in_background`) and
`AskUserQuestion`: "Did the game window open, can you see movement with the arrow keys?" → `tick "saw"` +
`decide --by user`. Then `studio.py status --full`: it re-checks the gates that earlier passed marked "will be checked later" (tests, linter). `commit "env: <engine> setup + hello"`.

## 13. How the agent sees the game

The main check of the game is frames the agent reads itself (Read PNG), and the user playing.

| engine | how to capture | don't |
|---|---|---|
| Web | `capture.mjs`: Playwright headless (on macOS WebGL goes through the GPU), input schedule, console errors → exit 1, `window.__metrics` → `metrics.json`, `sheet.png` | `canvas.toDataURL` without `preserveDrawingBuffer` — empty |
| Godot | `capture.gd` **in a window**: `await RenderingServer.frame_post_draw` → `get_texture().get_image()`, input via `Input.parse_input_event`, script errors via Logger → exit 1. A sequence with sound: `godot --path . res://x.tscn --write-movie .studioigor/captures/x/frame.png --fixed-fps 30 --quit-after 240` (files `frame00000000.png` + `frame.wav`). With the editor open — godot-ai's `editor_screenshot` | `--headless`: dummy renderer, `get_image()` → null |
| Godot web | export + `capture.mjs --dir build/web --wait-for "!document.getElementById('status')"` | — |
| Unity | live editor: `unity command screenshot --output <png> --width 1280 --height 720`; without the editor — `StudioCapture.cs` (render — a snapshot of the scene; play — N seconds of gameplay, launching the binary without `-quit`) | `-nographics`: no pixels |
| Unreal | rendering + `HighResShot`, Movie Render Queue | `-nullrhi`: no pixels |
| Defold | web bundle + Playwright; runtime automation API | — |
| Bevy | `Screenshot::primary_window()` + `save_to_disk`; `bevy_brp_extras` | — |

Contact sheet, if the template doesn't make one: `magick montage <dir>/frame_*.png -tile 4x
-geometry 480x270+2+2 <dir>/sheet.png`. The system `screencapture` needs the "Screen
Recording" permission (human) — last resort only. Don't minimize the Godot window during capture:
a minimized window doesn't draw, and the template fails on a timeout.

## 14. Tests — the minimum

One framework, run from the CLI, exit code is the gate. The hello project has exactly one test of a
pure function — it proves that TEST works. After that, tests only per the policy in
`references/code.md` §10: formulas, saves, determinism, a bug that came back. No
UI tests, "pyramids" or coverage for coverage's sake: the game is checked by CAPTURE and playtests.

## 15. Pitfalls

| symptom | cause | what to do |
|---|---|---|
| Godot: empty frame / `get_image()` null | `--headless` | run with a window; the template itself exits with code 2 |
| Godot: export "no export template found" | templates of a different version | folder `<v>.stable` exactly as in `godot --version` |
| Godot: new files "not visible", export fails | no import | `godot --headless --path . --import` after external edits |
| Godot: exit 0 despite script errors | that's how the engine works | smoke test via CAPTURE (Logger catches errors) |
| `brew install --cask godot` fails | `/Applications/Godot.app` installed by hand | symlink to the existing app or `--force` with consent |
| godot-ai ECONNREFUSED | editor closed / v3 entry / Godot < 4.7 | section 5 |
| Playwright: "Executable doesn't exist … chromium-NNNN" | browser revision ≠ package version | `npx playwright install chromium` in the project; as a last resort `PW_CHROMIUM=<path>` |
| global `@playwright/cli` expects a different chromium | its own playwright-core | don't rely on the global one; playwright is a project devDependency |
| Unity: `unity command` doesn't connect | Safe Mode due to compile errors | `unity pipeline list`, fix the C#, restart the editor |
| Unity: CAPTURE via `unity run` fails with the editor open | the project is already open in another instance | with the editor open — `unity command screenshot`; batch — with it closed |
| Unity: Hub CLI | deprecated since Hub 3.18 | only the `unity` CLI |
| Unity: web build crashes on iPhone | Safari memory | see stack.md; no Unity for mobile web |
| Godot C# + Android | needs .NET 9+ | `brew install dotnet` or dotnet-install.sh `--channel 9.0` |
| Godot C# + web | not supported | GDScript |
| Unreal doesn't open the project / doesn't build iOS | Xcode version not on the UE list | `xcodes install <version from the UE docs>` (human: Apple ID) |
| MCP added, no tools | the session is older than the entry | a new Claude Code session; `claude mcp list` |
| `npm create vite .` in the project folder | asks about a non-empty folder, may delete files | scaffold in a temporary folder + `rsync --ignore-existing` |
