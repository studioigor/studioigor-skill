# Mechanics — phase 6, the heart of the pipeline

Read at the start of phase 6 and before every mechanic. Here: mechanic order, the cycle of one
mechanic (research → spec → gym → self-check → the user plays → tuning → locked),
the prototype doctrine, the gym catalog, the tuning panel, the feedback template, tests. Code — `code.md`;
dialogue and cutscenes — `narrative.md`; parallel gyms — `team.md`; refinement — `gauntlet.md`;
ways to structure a mechanic and turns after "boring" — `gamedesigner.md`.

**Contents:** 1. Mechanic order · 2. The cycle of one mechanic · 3. Research · 4. Spec: feel
in numbers · 5. Prototype doctrine · 6. Gym: required contents · 7. Gym catalog ·
8. Tuning panel and overlay · 9. Self-check · 10. The user plays · 11. Tuning and lock ·
12. Gauntlet · 13. Parallel gyms · 14. Tests · 15. Narrative · 16. Statuses · 17. learn.py

## 1. Mechanic order

1. **First — the mechanic of the 30-second loop**: what the player does most often (steers,
   shoots, jumps, places a tower). If it isn't fun, nothing else will save it, and everything
   built on top will have to be redone.
2. **Then — in the order of the rows of the DESIGN.md table** (layers and order — `design.md`): the foundation
   (input, camera) grows inside the first gym; then what gives the verb pressure and a goal
   (enemy, track, timer), the meso-loop, progression. You can't tune a mechanic before the one
   it stands on: nitro can't be felt without drift.
3. **Within a layer — the riskiest first**: where there's the least certainty that it will be
   fun or that the engine can handle it.
4. **In phase 6 — only `mvp`**, `full` — in phase 8 with the same cycle. Menus, saves,
   settings are not mechanics, phase 7 builds them. The user always plays one
   mechanic at a time, otherwise the feedback gets mixed (building can be parallel, §13).

## 2. The cycle of one mechanic

| step | what appears | status after |
|---|---|---|
| research | `.studioigor/research/mech-<id>.md` | idea |
| spec | a card in DESIGN.md → "Mechanic specs" | spec |
| gym | `scenes/gyms/<mechanic>_gym` (e.g. `drift_gym`), data file, panel, overlay | gym |
| self-check | `captures/mech-<id>/NN/`, frames read by you | gym |
| the user plays | a PT-NN entry in PLAYTESTS.md | playtest |
| tuning | a diff of the data file, another play session | playtest |
| lock | final numbers in data, tag `mech/<id>` | locked |

After every step — the status in DESIGN.md and `studio.py commit "M01 Drift: <step>"`.

## 3. Research

Mandatory before EVERY mechanic: without `research/mech-<id>.md` the phase gates won't pass.
The model's memory of engines goes stale, and the reference games have already solved half of your
questions. It can be handed to a subagent without a worktree while you build the previous gym. What to look for:

- **How the references do it** from CONCEPT.md: GDC talks, postmortems, developer blogs,
  game feel breakdowns (`"<game> <mechanic> GDC"`, `"<game> postmortem"`).
- **Frame-by-frame breakdown**: `refs.py youtube <url> --frames N` → frames from input to the first
  reaction, how many responses fire together, the duration of a hit or a jump. These are the spec's numbers.
- **The right way on this engine and version**: official node documentation, tutorials and
  demos for this version, issues with pitfalls (a tutorial for Godot 3 or Phaser 3 will do harm).

Format — conclusions, not an essay, up to 60 lines:

```markdown
# M01 Drift — research (2026-09-28)
Sources: [GDC: …](url) — grip model; [video](url) — frames of entering a slide
How the references do it: the slide comes from the handbrake, the angle is held with throttle, the exit gives nitro
Numbers from frames: slide entry 6–9 frames; angle 25–40°; camera lags ~0.2 s
On Godot 4.6: VehicleBody3D doesn't give an arcade slide → a custom model on RigidBody3D
Decision: arcade model, 2 grip axes, parameters in data/tuning/drift.tres
Risk: holding the angle on a gamepad · not verified: <what>
```

## 4. Spec: feel in numbers

Under `## Mechanic specs` in DESIGN.md, 5–10 lines. Every line is checked by eye or by a
number, otherwise it's a wish.

```markdown
### M01 — Drift
- hypothesis: if the player enters a turn in a slide and holds the throttle, they feel "on the edge
  of control" — visible in that they seek out turns themselves and restart the lap
- pillar: Speed on the edge · controls: ←/→ steer, Space handbrake, ↑ throttle; gamepad: stick, A, RT
- rules: the handbrake breaks the rear axle loose; the angle is held with throttle and countersteer; a drift ≥1 s gives nitro
- parameters (data/tuning/drift.tres): grip_rear, drift_angle_max, countersteer_gain, nitro_per_sec
- feel: steering ≤2 frames at 60 fps; slide entry ≤150 ms; camera lags 0.15 s;
  wall hit: hit-stop 50 ms + shake 120 ms with decay; anti-reference: "ice"
- acceptance: at 120 km/h handbrake + steer → angle 25–40° within ≤0.4 s; a lap with 4 slides without
  spinning out by the 3rd attempt; to "is it fun?" — "Yes, want more"
```

**Words without numbers are forbidden**: "smooth", "floaty", "responsive", "heavy", "juicy",
"pleasant", "natural", "fast". Each one is translated into a number (starting guidelines,
check against the reference):

| about | translate into | guideline |
|---|---|---|
| response | ms or frames from input to the first visible reaction | ≤100 ms, better 2–4 frames (a frame at 60 fps = 16.7 ms) |
| attack | startup / active / recovery frames | light 4–7 / 2–4 / 8–14; heavy 12–20 / 3–6 / 18–30 |
| hit | hit-stop, ms | 30–100 ms (2–6 frames), stronger hit — longer |
| camera | shake: ms, amplitude, decay; lag, s | 80–200 ms with decay, never constant |
| weight | time to accelerate to max and to stop | 0.1–0.3 s (platformer hero), 3–6 s (arcade car) |
| jump | time to apex, height, coyote, buffer | 0.3–0.45 s to apex; coyote and buffer ~0.1 s |
| air | air control, as a share of ground control | 50–100% |

Parameters come in three kinds: **feel** (the user tweaks them), **curve**
(a formula: damage, prices), **gates** (session length, event frequency). The first kind goes on the panel.

## 5. Prototype doctrine

- **The hypothesis is falsifiable**: "If the player [does X], they feel [Y] — visible in
  [Z]". Z can be noticed during a playtest: restarts on their own, tries a trick without a hint,
  says "again". Without Z you can't tell whether the hypothesis was confirmed.
- **The riskiest assumption first.** In drift it's the slide itself, not the nitro and not the score.
  No menus and results screens unless they are the mechanic themselves.
- **The mechanic's code follows `code.md` from the start** (numbers in data, logic in `systems/`): it goes into
  the vertical slice as is. Only the gym's scaffolding may be rough, and the game doesn't import from `gyms/`.
- **Sunk-cost stop**: ~2 hours of agent work or 3 tuning rounds in a row
  without "Yes, want more" — stop turning numbers. Rephrase the hypothesis, change a rule
  (risk, choice, reward for mastery) or the control model, or ask the user
  one question: pivot / simplify / cut.
- **3 pivots — cut it**: status `cut`, the taste decision — `decide --by user`. Cutting is right
  if two signals out of these agree: unclear after 2 playtests; not a single fun moment
  (a smile, "one more time", restarting of their own will); works only with explanations; 3 pivots.
- **The graveyard — one line** in the DESIGN.md "Changelog", so the next session doesn't
  walk into the same dead end:
  `| 2026-10-02 | M04 Grapple → cut | 3 pivots; boring: no choice of where to hook; release inertia worked; next time — anchor points as a puzzle |`

## 6. Gym: required contents

- **A separate scene, launched directly**, without a menu: Godot `res://scenes/gyms/drift_gym.tscn`,
  web `?scene=drift_gym`, Unity `Assets/Scenes/Gyms/DriftGym.unity` — named after the mechanic.
- **The mechanic in production code**, parameters — from the data file (§8).
- **An environment from the catalog** (§7) with markers: distances, angles, pit widths are labeled in the scene,
  so both the user and your frames read the numbers without guessing.
- **The same keys in all gyms** (the user learns them once): `R` — restart, `Tab` —
  tuning panel, `O` — overlay, `P` — save the panel values, `1`/`2` — presets A/B,
  `T` — slow motion ×0.25. F-keys on a Mac are media keys by default — don't use them. Bind by physical key code so that non-Latin layouts work too.
- **Minimal juice from day one**: a sound on the main action (even a placeholder from
  sfxr or a pack), particles or a flash on contact, one camera reaction (shake, FOV,
  lag), a scale-punch on the acting object. The user will call a silent mechanic
  boring even if the rule is good: without response the feel can't be judged.
- **Look**: phase 5 look-dev assets where they exist; otherwise a greybox in the art bible palette. Seed and
  fixed timestep (`code.md`) — so the capture is repeatable.

## 7. Gym catalog by genre

- **Racing — a test ring.** A straight with speed markers; a 180° hairpin, a fast 90°
  sweeper, a chicane, a decreasing-radius turn; a wall, a ramp, a different surface; a lap timer.
- **Shooter — a shooting range.** Dummies at 5/15/30/60 m with signs; targets running across,
  in circles and in jumps; a target behind cover; a hit counter and TTK; infinite ammo.
- **Melee — an arena.** Dummies react: flash, knockback, stagger, death and
  respawn after 2 s. A 1/3/6-enemy spawner on keys; a blocking dummy and an attacking
  dummy with a telegraph — for dodging and parrying. The overlay shows the attack phase and frames.
- **Platformer — a course with measured gaps.** Pits of 2/3/4/5 tiles, ledges at 1/2/3
  jump heights with labels, a low ceiling, a narrow and a moving platform, a wall for
  wall-jump, spikes. A trace of the last jump's trajectory.
- **Vehicles and physics — a proving ground.** Ramps of different steepness, bumps, ice and mud, a wall
  to crash into, a pile of crates, speed markers.
- **Puzzle — a sandbox.** 5–8 micro-levels from trivial to a single "aha", undo,
  hot reloading of levels from data, a "show solution" key.
- **RTS/TD — a sandbox with spawning.** Own units, enemies, wave N on keys; infinite
  resources; speed 1×/2×/4×; a path with a fork; DPS, damage, and leak counters.
- **UI flow.** A screen opens directly with an injected state (`--state=shop_full`),
  switching 16:9 / 9:16 / 4:3, keyboard and gamepad navigation; a frame of every screen.
- **Dialogue and cutscenes.** Launch any scene or dialogue by id, scrub, skip,
  replay, ×2 speed, branch choice, story variables on the panel.

The genre isn't on the list — assemble one from the closest: what the player does, what to measure it on.

## 8. Tuning panel and overlay

The user tweaks the parameters themselves while playing — that's many times faster than "tell me what to
change, I'll restart". Data flow:

```
data/tuning/<id> → load → ONE parameter object ← panel sliders (Tab)
                                ↓ the mechanic reads it every frame
       P: dump → .studioigor/captures/tuning/<id>-<time>.json (+ stdout)
       → you carry the values into the data file and commit with a reference to PT-NN
```

The mechanic reads parameters from the object every frame rather than copying them at start, otherwise
the slider changes nothing — a common mistake. Sliders are built from the parameter ranges, not
by hand. The panel lives in `debug/` and works only in a debug build. The dump doesn't write to data
itself: you carry the values over, and the change is visible in git next to the playtest entry.

**Godot** — parameters in `class_name DriftTuning extends Resource` with
`@export_range(0.0, 2.0, 0.01) var grip_rear := 0.8`, file `data/tuning/drift.tres`.
The panel is a CanvasLayer autoload; the gym calls `TuningPanel.bind(tuning, "M01")`:

```gdscript
extends CanvasLayer   # debug/tuning_panel.gd; don't register it in the release build
var target: Resource  # the same instance the mechanic reads
var mech_id := ""

func bind(res: Resource, id: String) -> void:
	target = res; mech_id = id; layer = 100; visible = false
	var box := VBoxContainer.new(); add_child(box)
	for p in res.get_property_list():
		if p["hint"] != PROPERTY_HINT_RANGE: continue
		var r: PackedStringArray = p["hint_string"].split(",")
		var s := HSlider.new(); var l := Label.new(); var n: String = p["name"]
		s.min_value = float(r[0]); s.max_value = float(r[1])
		s.step = float(r[2]) if r.size() > 2 else 0.01
		s.value = res.get(n); s.custom_minimum_size.x = 280; l.text = "%s = %s" % [n, s.value]
		s.value_changed.connect(func(v: float): _on_slider(n, v, l))
		box.add_child(l); box.add_child(s)

func _on_slider(n: String, v: float, l: Label) -> void:
	target.set(n, v); l.text = "%s = %s" % [n, v]

func _input(e: InputEvent) -> void:  # not _unhandled: Tab eats GUI focus
	if e is InputEventKey and e.pressed and not e.echo:
		if e.physical_keycode == KEY_TAB: visible = not visible
		elif e.physical_keycode == KEY_P: _dump()

func _dump() -> void:
	var d := {}
	for p in target.get_property_list():
		if p["usage"] & PROPERTY_USAGE_SCRIPT_VARIABLE: d[p["name"]] = target.get(p["name"])
	var dir := ProjectSettings.globalize_path("res://.studioigor/captures/tuning")
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open("%s/%s-%d.json" % [dir, mech_id, int(Time.get_unix_time_from_system())], FileAccess.WRITE)
	f.store_string(JSON.stringify(d, "  ")); print("TUNING ", JSON.stringify(d))
```

**Unity** — a `ScriptableObject` with `[Range]`. In Play Mode the user tweaks it right in the
Inspector, and changes to a ScriptableObject asset **persist after exiting Play** (unlike
scene components): convenient, but check the asset's `git diff` before committing. For
a build — an IMGUI panel in `OnGUI` (`GUILayout.HorizontalSlider` over fields with `[Range]`,
`GUILayout.Label` with the current value), the dump — `JsonUtility.ToJson(tuning, true)` to a file.

**Web** — `lil-gui` (`gui.add(tuning, 'gripRear', 0, 2, 0.01)`) or Tweakpane v4
(`pane.addBinding`). Parameters — JSON in `src/data/`, Vite picks up your file edits
on the fly. Dump: a key → `fetch('/__tuning', {method: 'POST', body})` to a dev middleware
from `configureServer` in `vite.config.ts` (10 lines, writes to `.studioigor/captures/tuning/`).

**Overlay** (`O`): fps and the worst frame per second in ms, the mechanic's state
(`DRIFT angle 32° speed 118`), key values, the "input → reaction" delay in frames,
seed. During self-check it's enabled by a flag so the frames show the state; for the user
it's off by default.

## 9. Self-check: run it and look

The user must not get a black screen or a crash. Compiling is not running.

1. **Run it in a window straight into the gym, with scripted input** (headless doesn't render). Godot —
   the `capture.gd` template, the binary as in ENV.md:
   ```bash
   godot --path . --resolution 1280x720 --fixed-fps 60 --script res://tools/capture.gd -- \
     --scene res://scenes/gyms/drift_gym.tscn --inputs tools/inputs/M01.json \
     --out .studioigor/captures/mech-M01/03 --duration 8 --every 0.5
   ```
   Web — `capture.mjs` (Playwright) with `?gym=M01&seed=7&overlay=1`; Unity — Play Mode and
   `unity command screenshot` or `StudioCapture.cs`. A state you can't reach by
   launching the scene — set it with an argument (`--state=…`), not with clicks.
2. **Read** the contact sheet and 2–3 key frames with the Read tool. Compare with the spec:
   are the action and the reaction visible, are the overlay numbers within range, are there no errors in the log,
   are there events in `metrics.json`.
3. **Keep the evidence**: frames stay in `captures/mech-<id>/NN/`, the path goes into the
   playtest entry. The result in one line: `Self-check: OBSERVED — …` or
   `NOT VERIFIED — why`.
4. **What frames won't show**: weight, timing, sound sync. Measure input latency in the
   engine: the frame number at input and at the first state change (with `--fixed-fps`
   that's an exact number). Don't claim "feels good" from screenshots — that's for the user to decide.

## 10. The user plays

**Launch.** RUN from ENV.md with the gym parameter, in the background (Bash `run_in_background`), so that
the window opens for the user. Then a normal short message: what we're testing (the hypothesis
in one phrase), controls and gym keys, **3–5 "things to try"** — each one
tests a piece of the hypothesis. For example: "Take the hairpin in a slide without touching the wall";
"Move grip_rear from 0.6 to 1.0 and press P where it feels better"; "Exit the slide on throttle before
the apex"; the last one — "just play for a couple of minutes however you like".

End your turn and wait. When the user returns, ask for feedback. If they've already written feedback
in words, don't re-ask what they said — ask only for what's missing, first of all "is it fun?".

**Watch silently, confusion is data.** Don't explain the mechanic beyond the controls. If they didn't understand
what to do, that's a finding about readability and onboarding: record it, don't explain after
the fact "you should have pressed…". The first play in a gym is the only "fresh" one, it's worth more than all the others.

**Feedback** — one `AskUserQuestion` call. Rating questions have no "(Recommended)"
mark: it suggests the answer. The second question lists concrete problems from this mechanic's
feel profile, not generic words.

```json
{"questions": [
 {"header": "Fun?", "multiSelect": false,
  "question": "M01 Drift: is it fun to take turns in a slide?",
  "options": [
   {"label": "Yes, want more", "description": "It's gripping — small tuning and I lock it"},
   {"label": "Okay", "description": "It works but doesn't grip — I'll look for what's missing"},
   {"label": "Boring", "description": "No reason to try again — I'll change a rule, not numbers"},
   {"label": "Annoying", "description": "Controls get in the way or it feels unfair — I'll fix the response"}]},
 {"header": "What's off", "multiSelect": true,
  "question": "Which of these did you feel? Check all that apply, your own — in Other.",
  "options": [
   {"label": "Slide lags", "description": "A pause between the handbrake and the slide (now ~150 ms)"},
   {"label": "Car slips away", "description": "Hard to hold the angle, like on ice"},
   {"label": "No risk", "description": "The wall isn't scary, the slide costs nothing"},
   {"label": "All fine", "description": "Nothing specific gets in the way"}]},
 {"header": "Next", "multiSelect": false,
  "question": "What do we try next?",
  "options": [
   {"label": "Grip 0.7 + sparks (Recommended)", "description": "Rear grip 0.8→0.7, sparks and a screech on slide entry"},
   {"label": "Two presets on 1/2", "description": "\"As it was\" and \"new\" on keys — compare yourself"},
   {"label": "Another approach", "description": "Slide from lifting the throttle instead of the handbrake"},
   {"label": "Lock it", "description": "The mechanic is done, moving on to the next one"}]}]}
```

**Record** in PLAYTESTS.md right away, feedback verbatim:

```markdown
## PT-03 — 2026-09-28 — M01 Drift (gym)
- build: a1b2c3d · launch: `godot --path . res://scenes/gyms/drift_gym.tscn`
- what we tried: hairpin in a slide; grip_rear 0.6–1.0; exit on throttle before the apex
- is it fun? Okay · what's off: Car slips away · next: Grip 0.7 + sparks
- feedback (verbatim): "the hairpin is great, but it slips away on the sweeper, and there's no sense of speed"
- self-check: OBSERVED, captures/mech-M01/03 · dump: captures/tuning/M01-1727533.json
- findings → actions: balance: grip_rear 0.8→0.74; design: speed lines; polish: screech → BACKLOG
```

Findings: **design** → spec, **balance** → data, **bug** → BACKLOG "Now", **polish** → "Later".

## 11. Tuning and lock

- **One group of parameters per iteration**, "before → after" in numbers: otherwise you can't tell
  what worked.
- **A/B presets on `1`/`2`** — the strongest technique when the user can't describe the
  difference: a live comparison beats a description from memory.
- **"Boring" is about rules, not numbers.** Go back to the spec: where are the risk, the choice, the reward for
  mastery, the pace? Numbers cure "annoying" and "okay", boredom — almost never.
- **Locking.** "Yes, want more" → final numbers in data, the result in the spec, a PT entry, status
  `locked`, then `studio.py commit "M01 Drift: locked" --tag mech/M01`. "Okay" — one more
  round of finding the fun; if the user still chose "Lock it", lock it and add to
  BACKLOG "return to M01 in polish". "Boring" and "Annoying" are never locked.
  Locked doesn't mean frozen: in the vertical slice a mechanic is changed per playtest, with a line in the changelog.

## 12. Gauntlet

Only for the core mechanic's feel (the 30-second loop) and on a trigger from SKILL.md: "Okay"
twice, "not it", or your capture clearly loses to the reference frames. Numbers first
(latency, hit frames, the juice checklist from `polish-release.md`), the judge at the end is still
the user. Rounds — `gauntlet.md`. The other mechanics are fine with a playtest.

## 13. Parallel gyms

While the user plays gym N, a subagent in a worktree builds gym N+1, if the files don't
overlap: its own `scenes/gyms/`, `systems/<mechanic>`, data file. Shared files (input
map, autoloads, `project.godot`, `package.json`) are edited only by the lead. Before launching,
commit your own work; merge one at a time, with a self-check after each. Details — `team.md`.

## 14. Tests

A test — only if a bug would silently break the game and isn't visible in frames: pure logic with
math (damage formula, drift score, cooldowns, economy); saving and migration;
a regression test for a bug that came back a second time (first watch the test fail). Not
written: UI and scene tests, "jump works", tests for every class, checks that a node
exists. A typical mechanic has 0–3 tests, and 0 is normal. The main check is the self-check
frames and the user playing. The full policy — `code.md` §10.

## 15. Narrative mechanics

Dialogue, cutscenes, choices, notes — the same cycle. Spec: a hypothesis ("the player reads no
more than 2 lines between actions and skips nothing") and numbers (characters per line,
seconds per line, cutscene length). Self-check: a frame of every window (does the text fit).
The first feedback question is "Interesting?" instead of "Fun?". Details — `narrative.md`.

## 16. Statuses and studio.py

`idea` — the row exists · `spec` — there's research and a card · `gym` — the gym is built, self-check
OBSERVED · `playtest` — the user played, there's a PT entry · `locked` — "Yes, want more" or
an explicit "Lock it", tag `mech/<id>` · `cut` — the user's decision and a graveyard line.
Change the status and the "scene" column in DESIGN.md at every transition. `studio.py mechanics`
shows the next step; `--check` — the phase gates (all `mvp` locked, each with research and a
playtest entry). At the end of the phase — the holism check (`design.md`), findings go into BACKLOG.md.

## 17. What to propose to the skill (learn.py)

The lead asks about saving at the end of the phase; your job is to record a proposal at the moment:
- a gym or tuning technique worked on the playtest the first time (proving-ground layout,
  A/B presets, starting numbers) — `learn.py propose --title "…" --phase 6 --kind technique
  --what "…" --when "…" --why "…" --source "PT-03"`;
- research found an approach or tool better than the one described here — `--kind tool` or `technique`;
- the same failure repeated on a second mechanic — `--kind fix`.
