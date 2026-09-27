# Production — building the vertical slice (phase 7) and content (phase 8)

Read in phases 7 and 8. Phase 7: how to build the first real piece of the game from locked
mechanics with the full screen flow, the game-ness checklist, the playtest and the slice verdict.
Phase 8: the scope contract, content as data, level craft, variety,
the contact sheet, story through content, parallel building, cutting scope. Synergies after the slice and
each level's signature moment are invented by the game-designer layer — `gamedesigner.md`.

**Contents.**
- Phase 7: what a vertical slice is · the validation question · build order · the full game flow ·
  game-ness checklist · build speed · playtest and verdict
- Phase 8: scope contract · content is data · level craft · variety ·
  contact sheet · story through content · parallel building · batch playtest · cutting scope
- What to propose to the skill (learn.py)

# Phase 7 — Vertical slice

## What a vertical slice is

A vertical slice is 3–5 minutes of continuous play or one full cycle of the genre (a race, a level,
a day, a set of waves). It is built from locked mechanics at real quality: assets and
light from look-dev, sound, HUD, story delivery. And it is wrapped in the full flow, from the title
screen to the restart. From this point on the project has a game, not a set of gyms.

**Cut scope, not quality.** One level at final quality tests more than
five grey ones; a slice that doesn't look like the future game proves nothing. Longer is not
more convincing: volume is phase 8. Lay the architecture per `code.md` before the first line
(screen states, data separate from code, save schema version): everything
done in a hurry, phase 8 will multiply.

## The validation question — before building

Write it down before the first line of code: a question invented afterwards gets fitted to what
came out.

> Does a newcomer who was told nothing live through <the fantasy from
> CONCEPT.md> within <N> minutes — and have fun? And can such a piece be built at real quality?

N — from the genre, usually 2–5 minutes (the genre table in `polish-release.md`). Both
halves matter: a fun slice that took a month to build fails the question just like a quick and
boring one. Record: `studio.py decide --phase 7 --by agent "slice question: …" --why "before building"`.

## Build order

The whole flow in grey first, then the filling. Without a menu, pause and restart the game looks
like a tech demo, and bolting them on at the end costs more.

1. **Flow skeleton**: all screens from the section below, empty, but the transitions already work.
2. **Mechanics from the gyms — as is**: their scenes, scripts and data files, which hold the
   already approved numbers. Don't delete the gyms, in phase 9 they are the tuning rigs.
3. **One unit of content** per level craft (phase 8).
4. **Look**: light, post and materials from the look-dev scene, real assets instead of cubes.
5. **Sound**: music in the menu and in the game, SFX on every action and every UI click.
6. **Story delivery** (if story-driven): intro, first goal, final beat — `narrative.md`.
7. **HUD, pause, settings, saving.**
8. **Game-ness checklist**, then capture, self-check, playtest.

Commit after every item. At the start of the phase, tell the user the deadline by which
the full "start → challenge → resolution" cycle will be visible. If the cycle isn't there by then, don't push on:
either the slice scope or an architectural assumption is wrong. Tell the user directly.

## The full game flow

```
launch → title → main menu ─┬─ New game → game ⇄ pause
                            ├─ Continue → game     (only if there's a save)
                            └─ Settings · Quit (desktop)
game  → result (win | loss) → Again | Next | To menu
pause → Resume | Settings | Restart | To menu
```

| screen | minimum for the slice | how to check |
|---|---|---|
| title, menu | in the game's style, with music; the next action is the most visible | from launch to gameplay ≤ 2–3 presses |
| pause | Esc / Start / a button on touch; time, timers and world sound stop; auto-pause on focus loss | 10 s of pause → nothing changed in the world |
| result, restart | outcome, what was gained, what's next; a new attempt at the genre's rhythm (platformer < 2 s, racing < 3 s) | the capture reaches both outcomes; measure by frames |
| settings | music and effects volume separately, display, controls | restart → everything is in place |
| saving | autosave at checkpoints, schema version in the file | kill the process → "Continue" leads to the same place |

The capture scenario (CAPTURE from ENV.md) goes through the whole flow on an input schedule and
shoots every screen: that's cheaper than a manual check and repeats after every merge.

## Game-ness checklist

Gates of phase 7 and again of phase 9. Each item makes the project a game, it's not polish "for
later". An honest minimal version is enough for the slice. Skipping an item — only by
the user's decision (`decide --by user`), for example "no story" for an arcade game.

- [ ] **Title screen and main menu** in the game's style, not the engine's default UI.
      Check: the cold-launch frame next to the look-dev — one world.
- [ ] **HUD** — only what the player decides on right now. Check: for every
      element you can say "the player decides X by it"; the center of the screen is free.
- [ ] **A clear goal** at any moment. Check: from three random still frames it's clear
      what to do next (marker, task, level geometry).
- [ ] **Progression and rewards** are visible. Check: after a run the player has something they
      didn't have, and it changes the next run, not just a number.
- [ ] **Story and cutscenes** (if story-driven): intro, first goal, a beat at the end of the slice.
      Check: cutscenes can be skipped, input doesn't break after them, statuses in STORY.md.
- [ ] **Music and sound on everything**, including UI. Check: the sound event log of a 60-second
      session against the list of actions — 0 silent actions (`polish-release.md`).
- [ ] **Win, loss, restart.** Check: the capture reaches both outcomes, each
      has its own screen, a new attempt comes at the genre's rhythm.
- [ ] **Pause and settings** at any moment. Check: pause freezes the world,
      volumes are separate, settings survive a restart.
- [ ] **Saving and continuing.** Check: play, kill the process, launch —
      "Continue" returns you to the same place. A test is appropriate here: saves break silently.
- [ ] **Teaching through play**: the level introduces mechanics, one at a time, without walls of text.
      Check: the user starts without explanations; where they got stuck is where the hole is.
- [ ] **Ending and credits**: the slice has an end (a screen or a "to be
      continued" cutscene), the game has credits from the license registry. Check: there's no void at the end.
- [ ] **Juice**: the main action responds with a chord — motion, flash or
      particles, sound — within the same 2–3 frames. Check: a frame-by-frame capture of the key
      action, it shows ≥ 5 lines of the juice checklist (`polish-release.md`).

Result — a line in PLAYTESTS.md: how many items out of 12 and which ones are still in their minimal version.

## Build speed

The slice is the first honest measurement of the cost of a content unit on this stack. Write it in one line
into the verdict decision: "level ≈ 2 sessions, UI screen ≈ 0.5, cutscene ≈ 1" (from the session
log in STATE.md and `git log --oneline` for the phase). Multiply by SCOPE.md. If at this speed
the contract doesn't fit into what the user is willing to invest, say so before phase
8, not in the middle of it. Their options: accept the timeline; make production cheaper (level
templates in data, procedural placement, a modular asset kit); cut along the
ladder (below). The user decides.

## Slice playtest and verdict

Self-check first: capture the whole flow and 60 seconds of play, look at the frames yourself, fix
the obvious. Don't call the user to a slice with a white screen instead of a menu.

Then the user plays. Launch RUN and **explain nothing**: "without hints" is exactly what's being
tested. Say only "play it as a player, from the title screen". If the game writes
metrics (deaths and where, time per section, restarts), collect them for the session.

In one `AskUserQuestion`: "Is it fun?" (Yes, I want more / In places / Boring / Didn't get what
to do) · "Was it clear what to do?" (Right away / On the second try / No) · "What stuck
with you?" (best and worst moment — in Other). Feedback verbatim — in PLAYTESTS.md,
findings — in BACKLOG.md by bucket: design, balance, bug, polish.

**Verdict** — with a second call, with a recommendation:
- **Continue** — fun, clear, builds at a reasonable speed. Impossible if the answer to
  "is it fun?" is "boring" or "didn't get it": content doesn't cure a failed validation question.
- **Rework** — what exactly, as a list in BACKLOG `[P7]`; fixed → another playtest.
- **Pivot** — fundamentally doesn't work. Back to phase 1 with a specific change
  (`tick … --reopen`); list which mechanics and assets stay.

**Honest stop.** If two or more items hold, tell the user directly and
offer a pivot or pausing the project; they decide. Items: the mechanic is unclear after two or
more playtests · there wasn't a single fun moment (a smile, "one more time" of their own will) ·
this is the third pivot · it works only once explained · playing it is a chore, not
excitement (ask the user).

Record: `studio.py decide "slice: continue" --by user --why "<verbatim>"`, check off the
gates, `studio.py commit "slice: verdict" --tag slice`. A save from this build will be needed
at release to check save compatibility.

# Phase 8 — Content

This is where the game gains volume. Solo projects most often skip exactly this stage, and
it is exactly what separates a game from a demo. A content unit is what's counted in SCOPE.md:
a level, a track, an arena, a biome, a wave, an enemy type, a character.

## Scope contract

1. **Reference inventory.** Count what the reference games have: levels, tracks,
   enemy types, bosses, weapons, cars, music tracks, cutscenes, hours of play. Sources:
   wikis, the store, playthroughs; a subagent without a worktree can do it. Write it as a table above
   `## Contract`, **without `- [ ]`**: the checkbox is the contract line syntax for `scope.py`.
2. **Scale.** Translate the inventory into the scale from phase 1 (the "Scale" slot in CONCEPT.md),
   adjusted for the slice's speed. Show it in `AskUserQuestion` with `preview`: on the left the
   reference, on the right the proposed numbers, the recommended option first.
3. **Lines**, 6–10 of them; each `count:` counts real things:
   ```
   - [ ] levels: 12 pcs — count: ls data/levels/*.json | wc -l
   - [ ] enemy types: 8 pcs — count: jq '.enemies | length' data/enemies.json
   - [ ] music tracks: 5 pcs — count: ls assets/music/*.ogg | wc -l
   - [ ] cutscenes: 6 pcs — count: grep -cE '^\| *CS[0-9]+ .*\| *final *\|' .studioigor/STORY.md || true
   ```
   `manual:` — only if there's no way to count it: nobody checks such a line.
4. `studio.py decide "scope contract: …" --by user`; `scope.py .` — the phase gates.

Rules that make the contract a contract:
- **Numbers are not lowered silently.** When it gets hard, it's tempting to quietly make 8 instead of 12.
  Lowering is allowed only by the user's decision, recorded in DECISIONS.md.
- **Lines are not deleted.** A completed one — `[x]`. A cancelled one gets `BLOCKED` with a
  reason and date after the unit. Don't touch the name before the colon: `scope.py` remembers names
  and treats a rename as a deletion.
  `- [ ] levels: 12 pcs — BLOCKED: 8 done, cut by the user's decision 2026-10-02 — count: …`
- Checking off an unfulfilled line is the same as deleting it; `scope.py` catches that.

## Content is data

A unit is a data file plus shared code, not a copy of a scene with scripts. A new level =
a new file: `count:` counts it, it can be handed to a subagent without conflicts, shared
behavior is edited in one place.
- Godot: `levels/L03.tscn` (only a layout of instances of shared scenes) + `data/levels/L03.tres`
  or `.json`; logic — in a shared `level.gd` and the enemy and prop scenes.
- Unity: ScriptableObject + a layout scene or prefab; logic — in components.
- Web: `data/levels/L03.json` (for 2D — an export from Tiled/LDtk) and one loader.

Build the list of levels by searching files (a glob over `data/levels/`), not with a hand-kept registry:
a shared list is the main source of conflicts in parallel building. Keep difficulty and rewards
in the unit's data, so the curve can be tuned without code.

## Level craft

Each unit is a row of the `## Content` table in DESIGN.md, and it needs no more documentation
than that. Statuses: `sketch → blockout → art → final`.

| id | what's new | signature moment | difficulty 1–10 | axes of difference from the neighbor | story beat | status |
|---|---|---|---|---|---|---|
| L03 | collapsing bridges | a chase across a falling bridge | 4 | layout (vertical), pace (peak in the middle) | meeting Ira | blockout |

**The unit's arc**: setup → build-up → signature moment → resolution. The signature
moment is what the player will retell to a friend; invent it first and build the unit around
it. A sign of failure: the second half of the level just continues the first.

**Teaching through the level.** A new element is introduced in four beats: show it in a safe
place → let them try it with a low cost of failure → test it → twist it (a new
combination). Two new elements in one encounter — not allowed. A skill introduced and
tested in the same place is a difficulty spike; a skill introduced nowhere is a wall.
The first failure should teach: if the cause can't be read from the screen, the player blames the game.

**The difficulty curve** (the overall one — in DESIGN.md "Difficulty", `design.md` §8) is laid out
across units as a sawtooth, not a straight line: a unit rises to a peak and lets go, after a hard peak —
a breather where the player feels strong. A new element — no more often than once every 5–15 minutes.
Look at the difficulty column as a whole: three "8"s in a row are a wall, not a challenge.

**A sketch before the blockout** — five minutes of ASCII are cheaper than an hour of rebuilding:
```
S . . C . . ! . . R            S start · E exit · C encounter · P puzzle
      ? . . C C . B . . E      R reward · ! story · ? secret · B boss · @ NPC
intensity: ▁▂▃▂▄▆▃▂▅▇█▂        peak — signature moment
```

Landmarks and sight lines guide without arrows: the goal is visible before it's reachable.
There is one critical path, side branches give a reward or a secret. Work order:
sketch → blockout (grey, playable, the agent plays through it with a capture) → art → light and
sound → final. Art on an untested blockout is wasted work.

## Variety: at least two axes

A unit counts only if it differs from its neighbor on at least two axes:

| axis | example of a difference |
|---|---|
| layout and geometry | horizontal chase ↔ vertical climb |
| dominant mechanic or threat | drifting on switchbacks ↔ slipstreaming in traffic |
| palette and mood | dawn at the port ↔ night under neon |
| pacing shape (where the peak is) | peak at the end ↔ peak in the middle and a quiet finale |
| optimal strategy | stealth around ↔ breaking through by force |

The first question for a pair: what does the player do **differently** here? Difficulty is not an axis: faster doesn't
mean different. Lore is not an axis: a difference that isn't visible in the frame doesn't count. The same
track with a different texture is one unit, whatever the counter shows. Enemies,
weapons and cars have their own axes: silhouette, pattern, counter-strategy, role in an encounter.

## Contact sheet on the board

Monotony isn't visible one unit at a time; it's visible when they all lie side by side.
1. Shoot every unit with one scenario and in one framing: start, signature
   moment, wide shot → `.studioigor/captures/content/L03-{start,peak,overview}.png`.
2. Look at it yourself first by stitching a sheet; two similar thumbnails are one unit, redo it
   before showing:
   `magick montage .studioigor/captures/content/*-peak.png -tile 6x -geometry 320x180+4+4 .studioigor/captures/content/sheet-peak.png`
3. The board — one option per unit, `.studioigor/boards/content/board.json`:
   ```json
   {"title": "Content — all units", "mode": "multi",
    "question": "Which units are too similar or boring?",
    "options": [{"id": "L03", "title": "L03 — Collapsing bridge",
      "text": "new: bridges · peak: chase · axes: vertical, pace", "tags": ["blockout", "4/10"],
      "media": [{"src": "../../captures/content/L03-start.png", "caption": "start"},
                {"src": "../../captures/content/L03-peak.png", "caption": "signature moment"}]}]}
   ```
   `board.py build .studioigor/boards/content/board.json`, then in the background
   `board.py serve .studioigor/boards/content --open --until-feedback`. Marked
   pairs — into BACKLOG `[P8]`. Update the sheet after every batch: it's a phase gate.

## Story through content

If the game is story-driven (how to write and stage it — `narrative.md`):
- Every beat of the arc from STORY.md is tied to a unit (the "where in the game" column) and to its row
  in DESIGN.md. A beat without a place in the game is not story but intention.
- Place beats at unit boundaries and at signature moments. Before the player first gets control —
  only a short intro: the player came to play.
- Cutscenes go through the statuses `idea → storyboard → blockout → final`, the contract counts
  `final`. Each one can be skipped.
- Before the gates, go through the story from the intro to the credits in one run — with a capture, then
  by the user. Holes in logic and lost beats are visible only this way.

## Parallel building

Hand out independent units to subagents in worktrees, no more than three at a time (`team.md`):
- each unit has its own files (data, layout, asset folder); shared code is changed by the lead;
- commit your own work before handing out: a worktree doesn't see uncommitted changes;
- in the task: the unit's row, ART_BIBLE.md, "Level craft", the capture command; return:
  path, 3 frames, up to 5 points;
- the lead looks at the diff, merges one at a time, after each merge runs the game and the flow
  capture. Nobody pushes.

## Batch playtest

A batch is 2–4 new units. Self-check with a capture first, then the user plays
the new units in a row, starting from the previous one. Questions: "Is it fun?" — first · "Which of the
new ones is the best, which is the worst?" · "What happened in L03?" — if the signature moment isn't named,
it isn't there. Feedback verbatim — in PLAYTESTS.md, findings — in BACKLOG. `count:` will also count
a boring unit, so it goes first in the rework queue, and the "the user played the new content"
gates are not closed with it.

## When time runs out — the cutting ladder

Signals: the speed shows the contract doesn't fit, or the user says
"we need to wrap up". Lowering silently is not allowed: the user decides on cuts. The check for
every step: **"if work stops here — can this be released?"** Arrange the
remaining work so that after every step the answer is "yes".

What to cut, in order: (1) what serves no pillar; (2) the expensive with little
effect — an expensive cutscene for a single beat, a mode for 5% of players; (3) simplify to the
minimal version that still serves the pillar (20% of the work — 80% of the effect: an in-engine cutscene
→ comic panels with voice-over); (4) never cut the pillars, the core loop and the game-ness checklist:
without them it's a tech demo again.

Cut scope, not quality: 8 distinct levels are better than 12 of which four are copies.
Offer 2–3 options in one `AskUserQuestion`, the recommended one first, with what
stays in the `preview`. The chosen one: the SCOPE.md lines get `BLOCKED: cut by the user's
decision <date>`, the decision — `decide --by user`, what's postponed — into BACKLOG "Later".

## What to propose to the skill (learn.py)

Two natural moments. **Slice verdict**: something worked on the first showing (build
order, goal delivery) or a failure from a previous project repeated. **Batch playtest**:
a level-design technique or a content pipeline (a template in data, procedural placement)
noticeably raised the speed or the answer to "is it fun?".

```bash
python3 <skill>/scripts/learn.py propose --phase 8 --kind technique \
  --title "Blockout from the signature moment" --what "build the unit around the peak" \
  --when "every new unit" --why "3 of 3 levels were memorable right away" --source "PT-07"
```
Only propose; when to ask about saving — in SKILL.md.
