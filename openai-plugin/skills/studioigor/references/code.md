# Code — a standard that keeps a long project cheap

Read before the first line of gameplay code (the phase 4 hello project, the first gym of phase 6)
and when auditing an existing game. Covers: layout, 8 rules, how this looks in Godot 4,
Unity 6, web and briefly in Unreal/Defold/Bevy, debug and tuning hooks, performance
basics, test policy, bans on over-engineering, audit.

**Contents:** 1. Why, and where the line is · 2. Layout · 3. Eight rules · 4. Godot 4 ·
5. Unity 6 · 6. Web · 7. Unreal, Defold, Bevy · 8. Debugging and tuning · 9. Performance ·
10. Test policy · 11. Against over-engineering · 12. Auditing an existing game · 13. learn.py

## 1. Why, and where the line is

A project lives for dozens of sessions, and each inherits the structure of the first. Good structure
makes each step cheaper: tuning is a diff of a data file, a level is a content file, a mechanic is a folder in
`systems/`. Bad structure makes you spend sessions fighting the code instead of the game. But
over-engineering is just as much of a fire: abstractions "for the future", layers over the engine, tests and
documentation nobody reads. Below is the minimum of seams that pay off in this
pipeline; anything beyond it — only once a second real need already exists.

## 2. Layout

```
core/      loop and time, seeded RNG, input (actions), saves, event bus
systems/   mechanics: one folder per mechanic from DESIGN.md (drift/, combat/); no rendering
view/      rendering and juice: reads state, decides nothing
ui/        menus and HUD: reads state, sends intents ("buy", "start")
data/      all numbers: tuning/, balance/ — .tres / ScriptableObject / JSON
content/   levels, tracks, enemies, dialogue — data for the loader
gyms/      gyms and their harness (in Godot — scenes/gyms/); the game doesn't import from here
debug/     tuning panel, overlay, debug arguments — debug build only
tests/     only what §10 allows
```

Root: Godot — `res://`, Unity — `Assets/_Game/`, web — `src/`. Names may differ,
the two separations may not:

- **simulation / view.** The mechanic computes, the view draws and adds juice. That way a capture with
  scripted input runs the same logic, and editing particles doesn't break the rules. In Godot and
  Unity a node or object combines logic and view — the separation is done by composition: the mechanic
  script changes state and emits a signal, a child view node or component subscribes to it.
- **state / UI.** The UI reads state and sends intents, but never changes game state
  itself. UI that owns state is the reason a menu edit in phase 9 breaks
  saves from phase 7.

## 3. Eight rules

1. **One seeded RNG, no global random in gameplay.** Godot — an `Rng` autoload with
   `RandomNumberGenerator`, not the global `randf()`; Unity — your own instance of
   `System.Random` or `Unity.Mathematics.Random`, not the static `UnityEngine.Random`;
   web — mulberry32/sfc32 instead of `Math.random()`. The seed comes from the `--seed`/`?seed=` argument.
   Why: a playtest bug reproduces with the same seed, capture frames are comparable between edits.
2. **Fixed timestep.** Gameplay and physics — in `_physics_process` / `FixedUpdate` / a loop
   with an accumulator (§6); per-frame `_process`/`Update` — only for the view. Why: the game
   is the same at 30 and 144 fps, and a capture with `--fixed-fps` is reproducible.
3. **All tuning numbers live in `data/`.** Speeds, damage, prices, input windows, spawn tables.
   Only 0, 1 and math remain in the code. Why: a live tuning panel; tuning after a playtest is
   a diff of a data file; balance is checked with arithmetic.
4. **Content is data, systems are code.** A level, a track, an enemy is a file the
   loader reads, not a copy of a scene with logic inside. Eight data tracks — eight files;
   eight copied tracks — eight diverging branches. Improving the loader improves all of them at once.
5. **Saves with a schema version.** `SCHEMA_VERSION` in the file and a migration function for each
   bump. Otherwise an update in phase 10 silently breaks players' progress. Location: Godot
   `user://`, Unity `Application.persistentDataPath`, web `localStorage` in try/catch
   (portals and incognito may forbid it).
6. **No allocations in the hot loop.** Pools for bullets, particles, damage numbers; reuse
   vectors and arrays (on the web, `new Vector3()` per frame is a direct path to garbage collector hitches).
   Cheap from day one, painful later.
7. **Systems communicate through events or through state**, not by calling each other. Combat emits
   `enemy_died` — economy, audio and UI subscribe. All sound goes through a single point
   `play_sound(name)`: that gives you both mixing and a sound log for the capture.
8. **No god object.** A `Game`/`GameManager` longer than ~200 lines that knows every system by
   name is a signal to cut. It creates the systems and runs the loop, nothing more.

## 4. Godot 4

- **Scenes and composition.** A scene = an entity; behavior — child component nodes (`Health`,
  `Hurtbox`, `Juice`). Scene inheritance — only for variants of the same thing (an enemy and an
  elite enemy), not for a shared "base of everything".
- **Signals up, calls down.** A parent calls its children's methods, children emit signals.
  Global events — an `Events` autoload containing only signal declarations.
  Connect in code, in `_ready` (not in `_process`: that connects every frame, and not in the
  editor: the agent can't see the connections by grepping). Names in the past tense: `died`, `drift_started`.
- **Autoloads — sparingly**: `Events`, `Rng`, `Save`, `Metrics`, a debug `TuningPanel`.
  Not a dumping ground for global state and logic.
- **Resources for data**: `class_name EnemyDef extends Resource` + `@export` fields, `.tres`
  files in `data/`. A loaded resource is shared (cached by path): mutable instance
  state — via `duplicate()`, nested resources — `duplicate_deep()` (newer versions).
  Keep a mechanic's numbers in a Resource, not scattered as `@export` across scenes: otherwise the panel and
  the data file don't work. `@export` on a node — for placing a specific instance.
- **Typed GDScript everywhere**: `var speed: float`, `:=`, return types,
  `Array[Enemy]`. Enable the warning `debug/gdscript/warnings/untyped_declaration`
  (1 — warn) in Project Settings: type errors are caught before running.
- `@onready var body := $Body` — not `$Body`/`get_node()` in `_process`. Groups (`enemies`,
  `damageable`) — for sets of objects; cache the list, don't query it every frame.
  `&"jump"` (StringName) for action names in hot code.
- **Files**: commit `.uid`; after creating or renaming files outside the editor —
  `godot --headless --import --path .`. 3D physics is Jolt by default (since 4.6); for web —
  the Compatibility renderer and GDScript only (C# doesn't export to web).
- **Godot exits with code 0 even on script errors** — smoke test via `capture.gd`, it catches them.

**Wrong → Right.** Models often write the Godot 3 API. Checked 2026-09-27 against the official
documentation (upgrading_to_godot_4, the GDScript reference, @GlobalScope, CharacterBody2D);
rows marked ¹ were not checked in this pass.

| Wrong (Godot 3) | Right (Godot 4) |
|---|---|
| `KinematicBody2D/3D` | `CharacterBody2D/3D` |
| `move_and_slide(velocity, Vector2.UP)` | `velocity = …` then `move_and_slide()`; `up_direction` is a property |
| `Spatial`, `Position2D` | `Node3D`, `Marker2D` |
| `translation` on a 3D node ¹ | `position` |
| `export var speed = 10` | `@export var speed := 10.0` |
| `onready var`, `tool` | `@onready var`, `@tool` |
| `yield(obj, "done")` | `await obj.done` |
| `connect("hit", self, "_on_hit")` | `hit.connect(_on_hit)` |
| `emit_signal("hit", 5)` (works, but) | `hit.emit(5)` |
| `scene.instance()` | `scene.instantiate()` |
| `var hp setget set_hp` | `var hp: int: set = set_hp` or a `set(value):` block |
| `File`, `Directory` | `FileAccess.open(path, FileAccess.READ)`, `DirAccess` |
| `update()` on CanvasItem | `queue_redraw()` |
| `rand_range`, `stepify`, `deg2rad`, `str2var` | `randf_range`, `snapped`, `deg_to_rad`, `str_to_var` |
| `get_tree().change_scene(path)` | `get_tree().change_scene_to_file(path)` |
| `Tween` node | `create_tween()` |
| `BUTTON_LEFT`, `event.scancode` ¹ | `MOUSE_BUTTON_LEFT`, `event.keycode` / `physical_keycode` |
| `Engine.editor_hint` | `Engine.is_editor_hint()` |
| `OS.get_ticks_msec()` ¹ | `Time.get_ticks_msec()` |
| `TileMap` (deprecated since 4.3) | `TileMapLayer` |

A grep gate for these mistakes, cheap to run before a commit:

```bash
grep -rnE --include='*.gd' --exclude-dir=addons \
  'yield\(|\.instance\(\)|KinematicBody|Spatial\b|^\s*(export|onready|tool)\b|setget|connect\("[a-z_]+", *self|rand_range|stepify|deg2rad' . \
  && echo "Godot 3 API — fix it" || echo ok
```

## 5. Unity 6

- **Data — ScriptableObject** (`[CreateAssetMenu]`): mechanic tuning and content definitions
  (`EnemyDef`, `TrackDef`). Fields — `[SerializeField] private` with `[Range]`.
- **Prefabs and variants** for entities; behavior — small MonoBehaviours. Cache `GetComponent`
  in `Awake`; no `Find`/`SendMessage` — serialized references and C# events.
- **Input — the Input System package** (already in Unity 6 templates): actions, not keys.
  The old `Input.GetKey` throws an exception if only the new input is selected in Player Settings.
- **Assembly definitions — only when needed**: recompiles longer than ~10–15 s, or a tests
  folder (Unity Test Framework requires a test assembly). **Addressables — only** with
  large content, remote loading, memory problems; otherwise direct references in SOs and
  prefabs, `Resources.Load` is not the main path. **URP** by default, we don't use HDRP.
- **Pools** — `UnityEngine.Pool.ObjectPool<T>`; physics queries in hot code — `*NonAlloc`.
  Physics — in `FixedUpdate`, `Rigidbody` with interpolation enabled.
- **Don't edit scenes, prefabs and .asset as YAML while the editor is open** — use the `unity`
  CLI (`unity command`) or the editor MCP. Commit `.meta`.

| Wrong | Right (Unity 6, checked 2026-09-27) |
|---|---|
| `rb.velocity` | `rb.linearVelocity` |
| `rb.drag`, `rb.angularDrag` | `rb.linearDamping`, `rb.angularDamping` |
| `FindObjectOfType<T>()` | `FindFirstObjectByType<T>()` / `FindAnyObjectByType<T>()` |
| `Input.GetAxis("Horizontal")` | `move.ReadValue<Vector2>()` on an `InputAction` |
| `GetComponent<T>()` in `Update` | a field filled in `Awake` |

## 6. Web (Vite + TypeScript)

```
src/main.ts        reads ?seed=&scene=&state=&debug=, starts the loop
src/core/          loop.ts (step + interpolation) · rng.ts · events.ts (typed bus) ·
                   input.ts (actions by event.code) · assets.ts (loading with progress) · save.ts
src/systems/ view/ ui/ (DOM over the canvas) · data/*.json · content/ · gyms/ · debug/
```

```ts
const STEP = 1 / 60; let acc = 0, last = performance.now();
function frame(now: number) {
  acc += Math.min((now - last) / 1000, 0.25); last = now;  // clamp the gap after a tab pause
  while (acc >= STEP) { update(STEP); acc -= STEP; }        // simulation, fixed step
  render(acc / STEP);                                       // view with interpolation
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

- **Three.js**: game state lives in plain objects, meshes are the view, synchronized with the state
  every frame. Many identical objects — `InstancedMesh`. On unload —
  `dispose()` geometries, materials, textures. Physics — Rapier (`@dimforge/rapier3d-compat`),
  stepped inside `update`. The API drifts (`three/addons/…` imports, light units, `colorSpace`) —
  check against the types in `node_modules/three`.
- **Phaser 4**: Scene = a screen (Boot, Preload, Menu, Game, Gym); logic lives in systems
  called from `update`, not in a 500-line scene. Arcade physics for platformers and
  top-down. Models write Phaser 3 code — check against `node_modules/phaser/types`.
- **ECS-lite**: simple function-systems over arrays of plain objects. Structures of arrays
  and typed arrays — when there are more than ~1000 objects and the profiler has confirmed it;
  an ECS library — only for the same reason.
- **Assets**: preload per scene with a progress bar; GLB via GLTFLoader (+ KTX2/Draco
  when size matters); audio is unlocked by the first input; debug — under `import.meta.env.DEV`.
- **The truth about the API** — `package.json`, the lock file and `.d.ts`: `tsc --noEmit` catches invented
  methods. Input by `event.code` (the physical key) — otherwise non-Latin keyboard layouts break the controls.

## 7. Unreal, Defold, Bevy — briefly

- **Unreal**: systems in C++, Blueprint — glue and content (up to ~20 nodes per graph); data — in
  DataAsset/DataTable; input — Enhanced Input; `UPROPERTY()` on UObject pointers. Assets are
  binary: the agent edits C++, `.ini` and editor Python scripts, the rest — via MCP.
- **Defold**: game objects and components, the bus — `msg.post` messages; tuning — `go.property`
  and Lua modules or JSON via `sys.load_resource`; hot reload for tuning.
- **Bevy**: ECS out of the box; tuning — `Resource`; logic — in `FixedUpdate`; live tuning —
  `bevy-inspector-egui`. Pin the version: the API changes in every 0.x, check the migration guide.

## 8. Debugging and tuning

- **Debug arguments** (parsed in one place, at load time): `--scene`/`?gym=`,
  `--seed`, `--state=<preset>` (reach a state without clicking: `shop_full`, `boss_phase2`),
  `--overlay`. Without them the capture won't reach the right screen.
- **Tuning**: one parameters object per mechanic, loaded from `data/`; the mechanic reads
  it every frame; the panel is bound to the same object; dump on `P` → the agent moves it into data
  and commits. Panel code per engine — `mechanics.md` §8.
- **Metrics**: a `Metrics` autoload/singleton (`completed`, `events` — a tap off the event
  bus, `score`); `capture.gd` reads `/root/Metrics`, the web capture — `window.__metrics`.
- **Everything debug lives in `debug/` and is off in release**: Godot — `OS.is_debug_build()`, the panel
  is not registered in an export; Unity — `#if UNITY_EDITOR || DEVELOPMENT_BUILD`; web —
  `import.meta.env.DEV` (stripped by the bundler). The phase 10 gates check that there are no cheats.

## 9. Performance — the basics

- **Measure the worst moment** (maximum frame time, fps_min), not the average; budgets — in
  TECH.md. Profile before optimizing: Godot — Debugger → Profiler and Monitors; Unity —
  Profiler; web — Chrome Performance.
- **Habits from day one** (cheap now, expensive later): pools; zero allocations per frame;
  cache references to nodes and components; don't query groups, `FindObjectsByType` and raycasts for
  every enemy every frame — spread them across frames.
- **Draw calls**: fewer materials, atlases, instancing — Godot `MultiMeshInstance3D`, Unity
  GPU Instancing and SRP Batcher, Three `InstancedMesh`. Per-platform budgets — the table in
  `polish-release.md` (web/mobile — up to 100–200, PC — up to ~2000).
- **Textures** — by on-screen size: hero up to 2K, props 512–1K, UI — at actual size,
  half that for mobile and web; compression with GPU formats (Godot VRAM compression, ASTC on
  mobile in Unity, KTX2/Basis on the web); mipmaps in 3D.
- **Physics**: simple colliders, layers and masks. **Web**: bundle size and first load
  (portals cut by them), `dispose` on scene change.

## 10. Test policy

The main check of the game is capturing frames that the agent reads itself, and the user playing.
A test is a narrow tool for errors that are invisible in frames and silently break the game.

**Test:**
1. Pure logic with math: damage, economy and progression formulas, score, cooldown
   timers, generation invariants (same seed → same level; the level is completable).
2. Saves: write-read and migration from every old schema version.
3. Determinism of the core, if the capture or replays rely on it.
4. A regression test for a bug that came back a second time. First watch the test fail on the
   old code: a test that has never failed proves nothing.

**Never test:** UI and layout; the existence of nodes and scenes; engine behavior (physics,
rendering); getters and setters; "a test for every class"; screen snapshots; "play through the whole game"
with a bot — that's CAPTURE's job; engine mocks for the sake of isolation.

**Proportion**: far fewer tests than gameplay code, guideline 5–15% of lines; `status`
warns at 35% — then stop writing them and get back to the game. Move logic worth
testing into pure functions in `systems/` (`static func damage(base: int, armor:
int, crit: bool) -> int`) that the node calls: the test does without a scene.

**One framework**, the one in ENV.md: Godot — GUT or gdUnit4; web — Vitest; Unity — Unity
Test Framework in EditMode; Bevy — `cargo test`. Names: `test_<what>_<condition>_<expectation>`,
e.g. `test_damage_crit_doubles`. TEST should run in under ~30 s.

**Smoke test before committing a mechanic**: TEST + CAPTURE of the main scene and today's gym.

| engine | TEST | smoke |
|---|---|---|
| Godot | `godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -gexit` (logic needs no window) | `capture.gd` with `--scene res://scenes/main.tscn --duration 5`, in a window (full command — `mechanics.md` §9) |
| Web | `npx tsc --noEmit && npx vitest run` | `capture.mjs` — an error in the console = failure |
| Unity | `unity test <project> --mode EditMode` (code 8 = tests failed) | Play Mode + `unity command screenshot` |

## 11. Against over-engineering

- **No abstraction before the second use**, extraction — on the third. No interfaces,
  factories, "managers", `EntityManager`, plugin systems "for the future".
- **Don't wrap the engine API in a layer that adds nothing** (`InputManager` over
  `Input`). The exception is the single `play_sound` point (rule 7): it pays off.
- **No documentation for code**: no per-folder READMEs, no architecture descriptions, no
  docstrings on obvious functions. A comment — only about a non-obvious "why": a workaround for an engine
  bug, the source of a formula, a number from a playtest (`# 0.74 — PT-03`).
- **No options nobody asked for**, and no editor tools until a manual operation
  has repeated three times. A file longer than ~300 lines or a function longer than ~40 — split by
  responsibility, not by pattern.
- **Delete dead code** (git remembers); the gym of a cut mechanic goes along with it.
  Refactor only what the current work touches (§12).

## 12. Auditing an existing game

Twenty minutes; the result is lines in BACKLOG, not an essay.

1. Map the actual layout against §2: where do simulation, view, state, UI,
   data actually live? Mixed files are findings.
2. Greps (adjust the paths to the project):
   ```bash
   F=(-- '*.gd' '*.cs' '*.ts' ':!addons')
   git grep -nE '(^|[^.a-z_])rand[fi]?(_range)?\(|Math\.random\(|Random\.Range\(' "${F[@]}"  # rule 1
   git grep -niE '(speed|damage|health|cost|gravity|jump)[a-z_]*[[:space:]]*[:=][[:space:]]*[0-9]' "${F[@]}"  # rule 3
   git grep -lE 'SCHEMA_VERSION|schema_version' "${F[@]}"                            # rule 5
   git ls-files '*.gd' '*.cs' '*.ts' | xargs wc -l | sort -n | tail -6              # god object
   ```
   For Godot, add the Godot 3 API grep gate from §4.
3. God object: the largest file and how many systems it knows by name.
4. The seams the pipeline relies on: can a gym or scene be launched directly? is there
   scripted input and capture? are mechanic numbers in data? do saves have a version? debug arguments?
5. Verdict — `studio.py decide "code audit: <fine / fix the seams / rebuild> — <3
   worst findings>" --by agent --why "…"`.
6. Into BACKLOG "Now" — only the seams that **block the current work** (the numbers of the mechanic
   you are tuning are hard-coded — there will be no panel):
   `- [ ] [P6][M02] refactor: drift numbers from car.gd → data/tuning/drift.tres (panel needed)`.
   Everything else — into "Later" or nowhere. Refactor one seam at a time, after each one the game
   is launched (self-check with frames); "rewrite everything properly" in one step is not allowed.

## 13. What to propose to the skill (learn.py)

- An engine trap bit you that isn't in the tables above (an API renamed in a new version,
  an import quirk) — `learn.py propose --title "…" --phase 6 --kind fix --what "…"
  --when "…" --why "…" --source "<link to the docs>"`.
- A structural technique or hook noticeably made tuning or content cheaper (auto-generated sliders,
  a content loader) — `--kind technique`.
