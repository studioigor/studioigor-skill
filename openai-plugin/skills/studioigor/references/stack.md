# Platform and engine — phase 3

Read in phase 3, after the style is locked. Covers: mandatory research, how to ask about
platforms, platform constraints, the engine matrix for the game and for the agent, how to show
2–4 options, and what to write to TECH.md. Installation and setup is phase 4 (`environment.md`).

## 1. Phase order

1. Research → `.studioigor/research/stack.md` (section 2). Without the file the gates won't close.
2. Platforms: take them from CONCEPT.md; ask only if they are not stated (section 3).
3. Filter engines by hard platform constraints (section 4), score the rest with the matrix
   (sections 5–6) for THIS game: 2D/3D, genre, scale, style from ART_BIBLE.md.
4. Show 2–4 options, the recommended one first (section 7). One call per decision.
5. Write TECH.md, `decide --by user`, `tick`, `commit` (section 8).

Being already installed is a plus, not a reason. If the best engine for the game is not
installed, recommend it and install it in phase 4. State the cost honestly: which steps the
human does (login, license, GUI installer), how many gigabytes, what the agent cannot see itself.

## 2. Research (mandatory, before questions)

The model's memory of engine versions and platform rules goes stale within months. Check:

| what | where to look |
|---|---|
| current versions and LTS of the candidates | GitHub releases, engine releases/LTS pages, `brew info --cask <engine>` |
| export to the chosen platforms, limitations (C# on web, Windows from a Mac, web build size) | official export/build docs |
| agent integrations: editor MCP, Claude Code plugins/skills, CLI, headless tests, how to capture a frame | GitHub (stars, last release date), engine docs |
| requirements of the chosen stores/portals: size, SDK, accounts, fees | official developer docs of the stores/portals (requirements, guidelines, pricing) |
| license and money | pricing/license pages |
| live games of this genre on the engine | game store pages, engine showcase |

The skill deliberately contains no fresh facts: look them up yourself. Research can be handed
to a subagent without a worktree (it only reads the web). File format, ≤ 60–80 lines:

```markdown
# Stack — research (2026-09-28)
Game: 3D arcade racing, stylized, web portal + later a PC store.
## Findings
- Godot 4.7.2 (2026-08-18): web is Compatibility/WebGL2 only, build ~5–9 MB compressed …
- Three.js r186 + Rapier: …
- <store/portal>: size limit, required SDK, … (from its docs)
## What this changes
- Unity is out: the web build crashes on iOS Safari from memory, and the portal has mobile traffic.
## Sources
- https://… (date)
```

Mark `UNVERIFIED` anything not confirmed by a primary source.

If the research shows that the engine assessments in this reference are outdated (a version
came out that removed a limitation; an MCP or export appeared that changes the recommendation),
write a proposal: `learn.py propose --kind tool --phase 3 --title … --what … --when … --why …
--source <link>`. Do not edit the reference itself.

## 3. Platforms

If the platforms are already in CONCEPT.md, don't ask. Otherwise one `AskUserQuestion`,
`multiSelect: true`, header up to 12 characters:

- "Browser: web portal or your own site (Recommended for a first game)" — no accounts until
  publishing, fast playtests via a link;
- "PC: a store or your own site (Windows, Mac, Linux)";
- "Mobile: iOS and Android";
- "Consoles (later, through a publisher)".

In each option's description, one line with the entry cost for that type (account, fee, review),
so the choice is honest. The specific store/portal is named by the user — now or by phase 10;
the skill doesn't impose one. Platform order is also a decision: "browser first, then PC" changes
the engine choice.

## 4. Platform constraints that decide the choice

By store/portal type; numbers for a specific store/portal only come from research (phase 10 re-checks).

| type | typical requirements | what it means for the engine |
|---|---|---|
| web portal | small initial download (from a few to tens of MB), the portal's SDK, pause on ads and focus loss, no external requests or links, iframe, mobile browsers | web stack is ideal (Phaser/Pixi/Three), Defold; Godot web (GDScript) is fine, but the base is ~40 MB wasm uncompressed (5–9 MB compressed); Unity web — watch memory and size, risky on iOS Safari |
| own site, indie storefront | zip with `index.html` or a downloadable build; soft limits | everything |
| PC store | account and a per-game fee, mandatory wait before release, store page in advance, review; gamepad and handheld PCs | Godot and Defold build Windows/Linux from a Mac; Unity from a Mac — Windows only with Mono; Unreal does not build Windows from a Mac (needs a Windows PC); web — via Electron/Tauri |
| mobile store: iOS | paid developer account, Mac + Xcode, signing, review | Godot, Unity, Unreal, Defold natively; web — Capacitor; Godot C# — experimental |
| mobile store: Android | account with identity verification; package format, target API, closed test for new accounts — from research; 16 KB memory pages | Godot ≥ 4.5 and Unity 6 comply; Godot C# — .NET 9+ |
| console | platform holder approval, devkits, certification | Unity — Pro + approval; Unreal — approval; Godot — through a porting studio; Defold — free after approval; web and Bevy — no |

Filtering rules:
- **Web in the platform list** → exclude Unreal and Godot C#. Unity — only if the game is
  small and the iOS browser doesn't matter.
- **Consoles as the first target** — don't take that on for a solo project with an agent:
  approval and devkits are months of human work. Pick an engine with a path to consoles
  (Godot/Unity/Defold) and postpone the port.
- **PC and a Mac developer** → Unreal needs a Windows PC for a Windows build. Say
  this before the choice.

## 5. How the agent drives the engine

The agent works through text and commands. The more of this an engine has, the better:

| criterion | why it matters |
|---|---|
| scenes and resources are text | the agent edits and greps them without the editor; binary assets only via GUI/MCP |
| build and export from the CLI | BUILD without a human, including by a subagent in a worktree |
| tests from the CLI | TEST in ENV.md, exit code as a gate |
| frames without a human | CAPTURE: the agent sees the game itself (the main check, see environment.md) |
| editor MCP | live scene edits, logs, editor screenshots |
| few human steps | logins, licenses, GUI installers slow down autonomy |
| freshness of the model's knowledge | APIs that break often cause more hallucinations |

| engine | agent-friendliness | in short |
|---|---|---|
| Web (Three, Babylon, Phaser, Pixi) | 5 | everything is code; Playwright gives frames, input and state; build in seconds; no accounts |
| Godot 4 (GDScript) | 4.5 | text `.tscn/.tres/.gd`; export, import, tests from the CLI; MCP exists; frames only with a window |
| Defold | 4 | text collections, `bob.jar`, editor HTTP API; Lua, smaller corpus in the model |
| Godot .NET (C#) | 3.5 | like Godot, but a `dotnet build` loop, no web, mobile is experimental |
| Bevy | 3.5 | pure Rust, `cargo test`; API breaks every 0.x, the model mixes up versions |
| Unity 6 | 3 | YAML with GUID references — edit through the editor; login and license; good CLI and Claude Code plugin |
| Unreal 5 | 1.5–2 | binary `.uasset`, Blueprint only in the GUI, installed via the launcher, 40–100+ GB |

## 6. Recommendation matrix

First — the engine the agent can drive completely with a minimum of human steps; in parentheses —
the industry alternative, when its ecosystem matters more.

| | Browser / portals | Mobile | PC | Everything at once |
|---|---|---|---|---|
| **2D** | Phaser 4 (Pixi 8, Defold) | Godot (Defold for tiny casual games) | Godot (Defold) | Godot (Defold) |
| **3D** | Three.js + Rapier (Babylon.js + Havok for large scenes; PlayCanvas if a visual editor is needed) | Godot (Unity 6 if ads/IAP, weak Android devices, the asset store are central) | Godot for stylized (Unity 6; Unreal only for photorealism) | Godot (Unity 6); if web is primary — Three/Babylon + wrappers |

By genre (2D / 3D; alternative in parentheses):

| genre | browser | mobile | PC |
|---|---|---|---|
| racing | Phaser (top-down) / Three + Rapier raycast vehicle (Babylon + Havok) | Godot / Godot (Unity) | Godot / Godot (Unity; Unreal for a sim) |
| shooter | Phaser / Babylon.js (pointer lock, Havok) | Godot / Godot (Unity) | Godot / Godot (Unity; Unreal for a realistic FPS) |
| platformer | Phaser Arcade / Three | Godot (Defold) | Godot / Godot |
| RPG, action | Phaser + Tiled / Babylon.js | Godot / Unity 6 (animation, assets) | Godot / Godot (Unity) |
| strategy, TD | Phaser (Pixi for thousands of sprites) / Three InstancedMesh | Godot / Godot | Godot / Godot (Bevy or Unity DOTS for huge armies) |
| puzzle, casual | Phaser (Defold) | Defold (Godot) | Godot |
| survival | Phaser / Babylon.js | Godot / Unity 6 | Godot / Unity 6 (terrain, streaming) |

When to deviate from the recommendation:
- **Godot** — the default for native games: no account, everything is text, all desktops from
  a Mac. Take Unity if the user already knows Unity, if the game relies on ads/IAP
  on mobile, or it is a big 3D world that needs the asset store.
- **Web stack** — the default for portals: the smallest builds, the agent sees everything
  through Playwright. Godot web instead — if the same game later goes native
  (PC, mobile). For portals with a strict initial download limit Godot is on the heavy side.
- **Unity 6** — offer it honestly when the ecosystem matters. Warn: login and license
  are done by the human; the official Unity MCP on Personal requires a Unity AI subscription (there
  is a free community MCP and `unity mcp` from the CLI — see environment.md); Windows from a Mac
  only with Mono. LTS line — 6.3 (UNVERIFIED whether 6.7 LTS is out — see the research).
- **Unreal 5** — only photorealism on PC/consoles, and the user is ready for GUI work,
  binary assets, 100+ GB, a pinned Xcode version and a Windows PC for Windows builds.
  Never for 2D.
- **Defold** — small mobile and portal games where size and startup decide;
  a free path to consoles after approval.
- **Bevy** — only if the user wants Rust/ECS and accepts API churn.
- **Godot C#** — only if the user insists on C# and web is not needed.
- **Web libraries within `web`**: Phaser 4 — 2D with physics and scenes; PixiJS 8 — 2D
  rendering only, everything else is your own; Three.js — 3D rendering, physics (Rapier) and
  everything else you assemble yourself; Babylon.js — a full 3D engine with physics, GUI and an
  inspector; PlayCanvas — engine plus a cloud editor (private projects are paid).

## 7. How to show the options

2–4 options, the recommended one first with "(Recommended)". Each option explains
the choice for this game, not the engine in general. Two forms:

**A. `AskUserQuestion` with `preview` (default).** One question "What do we build
<title> on?", each option's `preview` is a text card:

```
GODOT 4.7 (GDScript)                          Recommended
Why for this game: stylized 3D, browser + later
  PC from one project; scenes are text — I edit them myself.
What you'll see: a game window within minutes, one gym per mechanic.
Downsides: web build 5–9 MB compressed; no photorealism.
I'll install: Godot, export templates, MCP, GUT, linter.
From you: nothing.
Cost: free, no royalties.
```

Card ≤ 10 lines, the same structure for every option: why, what you'll see,
downsides, what I'll install, what is needed from the user, money.

**B. A board with cards (`board.py build`)** — when the user wants to compare
at leisure or see games made with the engines. Build `board.json`:

```json
{"title": "Engine for “Neon Racing”", "question": "What do we build it on?", "mode": "single",
 "options": [
  {"id": "godot", "title": "Godot 4.7 — Recommended", "text": "Why for this game …",
   "tags": ["3D", "web + PC"], "pros": ["…"], "cons": ["…"],
   "media": [{"src": "../../refs/engine-godot/01.jpg", "caption": "a game made with Godot",
              "source": "https://store.steampowered.com/app/…", "credit": "…"}]}]}
```

Images are screenshots of real games made with the engine (`refs.py steam "<game>"` into
`refs/engine-<id>/`). Then `board.py build .studioigor/boards/engine/board.json` and
`board.py serve .studioigor/boards/engine --open --until-feedback` in the background. Confirm the
feedback from the board with one `AskUserQuestion`.

Option "you decide" → take the recommended one and write `--by agent`.

## 8. What to write

TECH.md (a line instead of a paragraph):

```
ENGINE: godot            one of: godot, godot-mono, unity, unreal, web, defold, bevy
ENGINE VERSION: 4.7.2    exact version from the research (Unity — 6000.3.xfN, Unreal — 5.8)
DIMENSION: 3D            2D or 3D; 2.5D with 3D models is 3D
LANGUAGE: GDScript
PLATFORMS: web (portal), windows, linux, macos
```

- `ENGINE` is read by `studio.py` and `envcheck.py`: only a word from the list. Phaser, Three.js,
  Babylon.js, PixiJS, PlayCanvas → `web`, and the library goes in "Decision".
- Write `PLATFORMS` with the keywords `envcheck.py` recognizes: web, windows, macos, linux,
  android, ios, console; the store/portal name, if chosen, goes in parentheses next to the
  type.
- "Decision" — a four-line ADR: context, options with pros/cons, the choice and why,
  consequences (assets, export, performance).
- "Budgets" — numbers from the platform: e.g. web — build ≤ 30 MB, load ≤ 5 s,
  60 fps on an average laptop; mobile — 60 fps on an average Android, ≤ 150 draw calls.
- "Project structure" — per `references/code.md`, one line per folder.

Then:

```bash
S=<skill>/scripts/studio.py
python3 $S decide --phase 3 --by user "platforms: browser, then PC" --why "…"
python3 $S decide --phase 3 --by user "engine: Godot 4.7.2 (GDScript)" --why "…" \
  --options "Godot 4.7 | Three.js + Rapier | Unity 6.3"
python3 $S tick --phase 3 "platforms"
python3 $S tick --phase 3 "engine"
python3 $S commit "stack: Godot 4.7, web + PC"
```

## 9. Phase pitfalls

| mistake | what to do |
|---|---|
| picked whatever is installed | the matrix and the game matter more; installation is phase 4's job |
| Godot C# and web in one project | doesn't export; GDScript or another engine |
| Unity for a portal with mobile traffic | Unity web crashes on iOS Safari from memory; web stack or Godot |
| Unreal for 2D or for web | Paper2D is abandoned, there is no web export |
| Windows build from a Mac with Unreal | needs a Windows PC; say so before the choice |
| the model writes an old API | pin the version; in the research — the major changes (Phaser 3→4, Pixi 7→8, Bevy 0.x, Godot 3→4) |
| consoles as the first target | postpone the port; an engine with a path to consoles |
| a wall of options | 2–4 options, one call, recommendation first |
