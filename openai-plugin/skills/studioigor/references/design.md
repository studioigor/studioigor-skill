# Game design — the craft of phase 1 and living design

Read in full in phase 1: after the interview, before the pillars and the mechanics table.
Return to it in phase 6 before ordering the gyms (§5), at the end of phase 6 for the holism
check (§10) and on any noticeable change to DESIGN.md (§13). The interview and showing the
pitch card are described in `interview.md`, story in `narrative.md`, the spec and gym of a
single mechanic in `mechanics.md`. This file is the craft; how to invent new things (signature
hooks, synergies) is in `gamedesigner.md`.

**Contents:** §0 Documents — as lines · §1 Fun: "works" ≠ "fun" · §2 Concept card
and MDA · §3 Pillars and anti-pillars · §4 The loop at three scales · §5 Systems → gym order ·
§6 Progression and meta · §7 Economy · §8 Difficulty and its curve · §9 The player's path (60 s,
first session, day 2) · §10 Holism check · §11 Numbers — free checks · §12 Genre
blueprints · §13 Living design · §14 What to propose to the skill

## 0. Documents — as lines, not essays

An experiment: four versions of the same game were built from one brief with different
processes. The variant with 30 documents before the first line of code was ranked last by
blind reviewers and a live playtest: the documents gave traceability, but did not make the
game better. Therefore:
- All design lives in CONCEPT.md and DESIGN.md, story in STORY.md. Do not create separate GDD,
  systems-index, economy-model or level-doc files. The templates in this file are mental
  checklists, and their result is lines in sections that already exist.
- One line — one decision with a number or a checkable condition. If it turns into a
  paragraph, the decision has not been made yet. A decision changed — edit the line, write the
  reason in "Changelog".
- In phase 1 DESIGN.md is a draft: the mechanics table in §5 order, 2–4 breakthroughs (§6),
  resources (§7) and the difficulty philosophy (§8) as guess lines. Mechanic specs are written
  in phase 6.

```
bad:     Drift is a key element of the gameplay that lets the player feel…
good:    | M01 | Drift | mvp | Speed on the edge | spec | scenes/gyms/drift_gym.tscn | builds nitro; spinning out >70° burns a charge |
         - ~5 min: first win → garage (breakthrough: car choice) · story beat 2
         - credits: race 100–300 → tuning 50–400, cars 500–2000; sink/source ≈0.8
         - philosophy: accessible entry, depth on demand; frustration ≤3 attempts, then a hint
```

## 1. Fun: "works" ≠ "fun"

A mechanic can faithfully follow its rules and still be boring. Fun cannot be written into
a spec: it is found in the gym by turning parameters and asking "is it fun?" every time.
It is made of these ingredients:

| ingredient | check | if missing — what to turn |
|---|---|---|
| meaningful choice | every 5–15 s there is a decision, and the player sees its consequence | a fork (route, risk, resource); remove the obviously correct option |
| risk and reward | the risky option pays off noticeably better than the safe one | widen the reward gap; make the risk readable (telegraph, sound) |
| mastery curve | after 10 minutes the player does the same thing better and notices it themselves | a skill ceiling (timing, combo, line); a number that shows growth |
| surprise | something new happened in the last 2–3 minutes | enemy and event variations, a rare event, two systems colliding |
| self-expression | two players play differently | builds, playstyles, your own garage or base |
| juice | an action answers with a "chord" within 2–3 frames: motion, flash, particles, sound | the minimum — right away in the gym; the full checklist in `polish-release.md` |
| pacing | tension rises and falls, there is a peak | waves, breathers, a memorable moment at the end of a level |

If the user says "boring":
1. Ask which moment was the best. Amplify it and subordinate everything else to it.
2. Turn one knob at a time to the extremes (×0.5, ×2): fun often lives at the edge.
3. Add pressure — time, threat, scarcity. Many actions are boring until there is a stake.
4. Remove steps between wanting and doing: menus, confirmations, long animations.
5. Three tuning iterations without "fun" — do not lock the mechanic. Propose changing its verb
   or cutting it (`cut`). Cut it if two or more signs are true: unclear after two
   playtests; never a voluntary "one more time"; three pivots; only works with an
   explanation.

## 2. Concept card and MDA

Showing the card is in `interview.md`. Here — what it consists of and how to check that the
concept is strong. The result is the "Pitch" section and the CONCEPT.md slots.

- **A 10-second pitch:** "A game where you [verb] in [world] to [goal]". A person who has
  heard nothing about the game understands what they will be doing.
- **Verb first.** The player's most frequent action is the game; M01 comes from it (§5).
- **"Like X, AND ALSO Y".** Y is tied to the fantasy and changes the gameplay, not just the
  picture. Good: "like a roguelike, and also death moves the story" (Hades). Bad: "like NFS,
  and also pretty graphics".
- **Fantasy** — who the player feels like, in one phrase. **Main aesthetic** — 1–2 from MDA.
- **Main risk** — the most expensive unanswered question ("will drifting feel good on a
  keyboard?"). The first gym starts with it.

The pitch in CONCEPT.md is one sentence, ideally right away in the form "Like X, AND ALSO Y"
("NFS Underground where drift is currency"). Write the main risk in the notes of the M01 row
in DESIGN.md; if the risk is not in the verb, put the risky mechanic first. If the idea is vague, offer 2–3 concepts in one question, built from a verb ("build",
"flee"), from a mash-up ("farm + cosmic horror") or from an emotion (MDA in reverse).

**MDA in short.** Mechanics (the rules you write) produce dynamics (behavior in the
game), and those produce aesthetics (the player's feeling): you build mechanics, you judge by
feeling. Eight aesthetics: sensation, fantasy, narrative, challenge, fellowship, discovery,
expression, submission; every mechanic serves one of the main ones. The key dynamic is "what
will the player start doing on their own, without a hint?"; no answer — the mechanics do not
produce it yet.

## 3. Pillars and anti-pillars

Pillars are 3–5 principles of what the game is. Every decision (design, art, sound, story,
code) serves at least one; a system without a pillar is scope creep with a pretty name.
A pillar is valid only if it is **falsifiable** (a build can refute it: "fun combat" is not a
pillar, "combat rewards patience, not aggression" is), **constraining** (forces you to turn
down plausible ideas; a pillar that can be satisfied for free does not work),
**cross-disciplinary** (says something to art, sound, story and code) and **memorable**.

| game | pillars | why they work |
|---|---|---|
| God of War (2018) | brutal combat · a father-and-son journey · one continuous camera · reimagined myths | "one camera" gave up an entire cinematic tool; "father and son" constrains the story, the levels and combat |
| Hades | fast fluid combat · story through repetition · every run teaches | "story through repetition" justified the roguelike narratively: death is the story |
| Celeste | hard but fair · accessibility without compromise · story and mechanics are one | the dash is the heroine's anxiety, a mechanic is never "just gameplay" |
| Hollow Knight | atmosphere instead of explanations · earned mastery · the world tells its own story | no tutorials: level design has to teach |
| Dead Cells | any weapon is viable · combat as a dance · permadeath gives meaning | "any weapon" is a deliberately chosen never-ending job of balancing |

In CONCEPT.md each pillar has a decision test — "if we argue X or Y, the pillar picks __":
`- **Speed on the edge** — only those who risk spinning out get the best time; test: a wider and safer track or a narrower and faster one → narrower and faster`
The set must include at least one pillar about mastery, one about choice and one about
self-expression (§4).

**Anti-pillars** — 1–3 things the game deliberately does not do, even though it is tempting.
"This is not a strategy game" is useless; useful is "no open-world drives between events",
"no crafting", "no grinding for numbers". The agent checks every decision against them
without the user.

## 4. The loop at three scales

- **30 seconds (micro):** an action that is enjoyable in itself, before any reward. If it
  is bad, nothing on top will save it. Without it — "feels bad".
- **5–15 minutes (meso):** goal → effort → reward, the "one more" unit: a run, a match,
  a level, a race. The start sets the goal, the end resolves it. Without it — "aimless".
- **Session (macro):** what grows, where the natural stop is, why come back tomorrow (§6,
  §9). Without it — "played it once, and that's it".

Inside the meso loop keep the arc: entry → build-up → peak → release → hook into the next cycle.
Three questions from self-determination theory; a "no" is a phase 1 hole, not a polish task.
**Competence:** does the player grow and see that they grew themselves, not the upgrades?
**Autonomy:** does every cycle have a real choice with consequences (route, build, risk)?
**Ownership:** is there something in the game that is theirs — a style, a build, a base, the
ghost of their best run?

## 5. Systems → gym order

This section feeds phase 6: the "Mechanics" table and its order come from it.
1. **Explicit systems** — from the loop and the genre blueprint (§12).
2. **Implicit systems.** Each explicit one pulls in hidden ones; write them out right away,
   otherwise at the vertical slice it turns out death and restart were forgotten.

| explicit | pulls in |
|---|---|
| combat | damage calculation, health, hit detection and hit reactions, enemy AI, death and restart, health UI |
| driving | controller and physics, chase camera, track as data, rival AI, start → finish → results, HUD |
| platforming | controller (coyote time, jump buffer), checkpoints, hazards, look-ahead camera |
| inventory, loot | item database in data, slots, UI, saving |
| progression | currency or XP, unlocks, progress screen, saving |
| crafting | recipes in data, resource gathering, crafting UI, recipe unlocks |
| dialogue, cutscenes | lines, UI with portraits, flags, cameras, timeline, skip, subtitles (`narrative.md`) |
| open world | streaming, map, points of interest, fast travel |

3. **Dependency layers:** foundation (input, movement, camera) → core (the main verb) →
   what stands on the core (enemies, power-ups, upgrades, economy) → presentation (HUD,
   dialogue, cutscenes, music) → meta and progression. Within a layer the riskiest goes first.
4. **Gym order.** M01 is the main verb of the 30-second loop; it usually also holds the main
   risk, so the fun is proven first. Next — whatever gives the verb pressure and a goal
   (an enemy, a track, a timer): without it "is it fun?" cannot be answered. Then the meso
   loop (reward, end of run) and progression. In a story game dialogue and the cutscene system
   come before the vertical slice: the phase 7 slice needs an intro and a first goal. The
   foundation does not get its own gyms — it grows inside the first gym in exactly the needed
   amount. Saving, menus and settings are part of the vertical slice (`production.md`), unless
   they are themselves part of the fun (bonfire saves in a souls-like).
5. **The row order in the table is the build order.** `status` names the first unlocked mvp
   row as the next one. Priority changed — reorder the rows.
6. **tier:** mvp — without it the slice cannot answer "is it fun?"; full — after the slice.
   Usually 4–8 mvp mechanics; more than 10 — the scope is bloated, discuss with the user. Every
   row has a pillar (§10f).

## 6. Progression and meta

"+10% per level" is a table, not a path. Real progression rests on **breakthrough points** —
moments when something new becomes possible, not just something bigger. A double jump
opens routes on old levels; nitro lets you cut through ramps; the third tower finally hits
flyers. Mix kinds of progress, a single "power" gets old fast:
- **power** — numbers grow; **capabilities** — new verbs, tools, abilities;
- **access** — new zones, tracks, modes; **knowledge** — the player's own skill and secrets;
- **story** — story beats (breakthrough = beat, `narrative.md` §4); **ownership** — cosmetics, base.

Rhythm: the first breakthrough within 5–10 minutes, in the first hour — every 10–20 minutes,
new mechanics no more often than one per 5 minutes. The next goal is visible in advance: a car
that is shown but locked pulls harder than a surprise. In DESIGN.md → "Progression and meta" —
a line per breakthrough:
`- ~20 min: nitro (breakthrough: shortcuts over ramps) · beat 3` / `- session: tier ↑, next car visible → reason to come back`
Check: no dead zones (15+ minutes with nothing new) and no game-breaking power jumps; the
player names their own goal.

## 7. Economy

Write out every resource (currency, XP, materials, health, ammo, time, wanted level) with its
sources and sinks. Write rates even as a guess: a wrong number can be fixed, a missing one
cannot.

| state | sign | what the player feels |
|---|---|---|
| source without a sink | accumulates forever | the late game is trivial, the resource is worthless |
| sink without a source | drains to zero | the system silently becomes unavailable |
| source ≫ sink | surplus | rewards stop feeling like rewards |
| sink ≫ source | permanent scarcity | grind and walls |
| positive feedback | more resource → easier to earn more | snowballing, no tension |
| no catch-up mechanic | falling behind accelerates | hopeless states, the player quits |

Guidelines: sink/source 0.7–0.9 (a slight surplus — the player feels rich); the first
meaningful purchase within the first 5–10 minutes; everything random has a guarantee (the rare
thing no later than the N-th attempt); no pay-to-win.

## 8. Difficulty and its curve

**Philosophy** — pick one and write it down, otherwise tuning will slide into a faceless
"balanced": 1) difficulty is the product (Dark Souls); 2) accessible entry, depth on demand
(Hades, Hollow Knight); 3) difficulty serves the story's pacing (The Last of Us); 4) a relaxed
game, failure is soft and rare (Stardew Valley). Then decide explicitly how much frustration
is allowed: how many failed attempts before the design steps in. The cost of failure is
inverse to its frequency: frequent failures — a restart no longer than 3 seconds.

**Axes** — do not tune just one: execution (can I do it), decision (do I know what's right),
resource (do I have enough), time (can I make it), information (do I understand what's going
on). When the wrong axis is overloaded, players say "confusing", not "hard". For each axis
decide whether the player can lower it through choice, build or a setting.

**The flow channel.** Sketch two curves for the first hour: what the game demands and what the
player can do (skill plus unlocked power). Flow is where the demand is slightly above the
ability. Demand stays flat while power grows — boring by minute 20; demand jumps faster than
power — this is where players quit. Every bend in the curve coincides with a breakthrough
from §6.

The curve — as lines in DESIGN.md → "Difficulty":
```
- curve: 0–5 min 2/10 teach the verb · 5–20 4/10 rivals · 20–35 7/10 gang boss · 35+ 5→8 tiers
- entry: ≤3 new concepts before the first success; never two new mechanics in the same encounter
- first failure: ~3 min, the cause is visible without explanation, restart ≤3 s
- first competence: "first clean drift through the S-bend", no later than 10 min
- peaks: gang boss → breather + reward; the player leaves feeling "I did it", not "drained"
- skills: drift — taught by track 1, first hard test on track 3
```
Traps: a skill introduced and tested in the same encounter is a sudden spike. A skill that is
assumed but never introduced is a knowledge wall. Scarcity together with combat is a death
spiral, a catch-up mechanic is needed.

## 9. The player's path: 60 seconds, first session, day 2

| stage | the player's question | what the game must provide | if not |
|---|---|---|---|
| first 60 seconds | what do I do here and does it feel good? | the verb in hand no later than 60 s after "New game", the first juicy response, a clear goal | closed the game |
| first session (10–30 min) | where is this going? | first win, a failure with a clear cause, the first breakthrough, a story hook, the next goal visible | "neat", but won't come back |
| day 2 | why come back? | unfinished business: the next unlock, an untold story, their own build or garage, a record | didn't come back |

In "Progression and meta" mark as lines the 5–8 critical moments (first death, big win,
a system unlocking, "the world opened up", first boss) and what happens if the moment does not
land. At the playtests of phases 7 and 9 ask: "without looking at the menu — what is the game
about?", "what does winning look like right now?", "what will you come back for?".

## 10. Holism check (8 items)

When: at the end of phase 6 (a PIPELINE.md gate) and on a major change to DESIGN.md — a new
system, a pillar changed, 3+ mechanics cut or added, the economy rebuilt. These problems are
not visible in any screenshot, they live in the connections between systems. The check takes
minutes, run it yourself, without a subagent. Findings — lines in BACKLOG.md with a label
(`- [ ] [P6][holism c] ranged combat dominates → give melee a stagger`); these are holes, not
blockers.

a. **Competing loops.** One progression loop dominates, the others feed it. Three systems
   each calling itself the main one and paying out the same currency — a game about nothing.
b. **Attention budget.** More than 3–4 active systems at once in the core loop is overload.
c. **Dominant strategy.** High reward at low risk, an "obviously correct" choice. Ranged
   combat with 80% of melee damage and no risk kills half of combat until melee gets
   something ranged does not have (stagger, area damage).
d. **Sources and sinks.** The §7 table for every resource, in both directions.
e. **Mismatched curves.** Enemy health ×2 per zone against player damage +10% per level:
   by zone 5 that is 32× against 1.5×. Everything that grows with progression grows compatibly.
f. **Pillar drift.** A mechanic without a pillar — add a pillar, rework it or cut it.
   Violating an anti-pillar is a bug, not a compromise.
g. **Coherent fantasy.** All systems speak about the same role, the story does not argue with
   the mechanics (`narrative.md` §4). "Ruthless warrior" in combat and "kind farmer" in the
   meta are two games.
h. **Learning budget.** Before the first meaningful success — no more than ~3 new concepts; a
   new system only after the previous one has been used. Fix: postpone a system, merge two
   controls, make something passive at the start.

Then walk through 2–3 scenarios where systems trigger at the same time (a boss with empty
potions and ammo, an upgrade in the middle of a chase): what fires first, what the player
sees, whether there is double crediting or an infinite loop.

## 11. Numbers — free checks

Balance is arithmetic, it can be checked without a critic or a playtest. Here a test is
justified (rule 1 in SKILL.md): a small script over the data files prints a table and fails on
an obvious error. **Combat:** DPS and time to kill (TTK) per tier, an option strictly better
than all others, defense with invulnerability. **Progression:** XP and power curves, dead
zones, jumps. **Loot:** time to each rarity, guarantee arithmetic. **Economy:** accumulation
per session, infinite loops. Do not automate the rest — the playtest checks it.

## 12. Genre blueprints

Proven starting shapes. Start from a blueprint and earn the differences: every deviation
serves a pillar. A design that never deviates from the blueprint has not been invented yet.
How much story a genre needs — `narrative.md` §1.

- **Arcade racing.** 30s: steering through traffic at the edge of control · 5–15m: a race or chase with results · session: a
  career or wanted-level tier, the next reward visible. mvp: arcade car physics, track from data, rubber-banding rivals,
  start → finish → results, currency + upgrades. Axes: execution + risk (shortcuts, traffic). Sink — entry to the next tier.
- **Platformer.** 30s: running and jumping, cleanly linked · 5–15m: a level with a secret found or missed · session:
  a world completed, a mechanic unlocked. mvp: controller (the feel is the product), levels from data, hazards, collectibles,
  checkpoints. Axes: execution + information; difficulty through levels, not stats. Death costs only a little time.
- **Survival, crafting.** 30s: gathering under threat · 5–15m: day and night or a sortie · session: the base grows, a biome or
  recipe unlocks. mvp: needs meters, respawning resources, recipes in data, a threat that grows at night, a base, saving. Axes: resource
  + time. The economy is the design: write the §7 table first, the danger is "source ≫ sink by day three".
- **Roguelike, arena.** 30s: combat with dodge and aim decisions · 5–15m: a run, power visibly accumulates · session:
  a meta unlock changes the options of the next run. mvp: combat, rooms and waves from data, upgrade choice, run results,
  meta, seeds. Axes: execution + decision (synergies); randomness is bounded — a run is not dead from the deal.
- **Tower defense.** 30s: building and upgrading ahead of a wave · 5–15m: a map to victory · session: new towers, maps,
  mutators. mvp: path or grid, towers and waves in data, enemies with counters, build/upgrade/sell, fast-forward.
  Axes: decision + resource, no reflexes. Trap — a dominant tower (§10c): counters must be structural.
- **Idle, management.** 30s: a purchase that noticeably raises the rate · 5–15m: a decision (automate,
  reallocate, prestige) · session: a new order of magnitude. mvp: tick, generators with exponential cost,
  automation, offline progress, prestige. Mismatched curves (§10e) are fatal — graph cost against production before code.
- **RTS-lite, autobattler.** 30s: "economy or army" · 5–15m: a battle with a readable turning point · session: rating or
  roster growth. mvp: units in data, economy, combat resolver, AI with 2–3 readable strategies, match flow. Axes: decision +
  information (scouting). Strictly limit active systems (§10b), guard against snowballing.
- **Shooter.** 30s: aim → shoot → cover, a hit reads clearly (hit marker, enemy reaction) · 5–15m: an arena or
  mission with waves and a peak · session: a new weapon or chapter. mvp: controller and camera, weapons in data (damage, rate,
  recoil, spread), AI of 2–3 archetypes (cover, flank, rush), hit reactions, health and armor, ammo. Axes: execution
  + decision + resource. A new weapon is a breakthrough with a different role, not +damage; a TTK table catches a dominant gun.
- **Action/RPG.** 30s: a weighty strike and dodge, enemies telegraph · 5–15m: clearing a location, loot · session: a level,
  a skill or gear, a story quest. mvp: combat (hitboxes, stamina, dodge i-frames), 3–4 enemy archetypes,
  stats and loot in data, equipment, dialogue and quests, saving. Axes: execution + resource + decision (build).
  Danger — stat inflation without breakthroughs (§6, §10e).
- **Horror.** 30s: moving in the dark with incomplete information, sound as a signal · 5–15m: a goal in a dangerous zone with a
  threat peak and a breather · session: a chapter, a new zone. mvp: slow controller, flashlight as a resource, a threat with hearing and
  sight, positional audio, safe rooms, notes and cutscenes. Axes: information + resource + time. Fear
  is anticipation: show the threat rarely, scarcity is deliberate but without dead ends.
- **Puzzle.** 30s: one action changes the board predictably · 5–15m: a level with an "aha!" moment · session: a new
  rule every 3–6 levels. mvp: deterministic board (tests are justified here), instant undo and restart,
  levels in data, hints. Axes: decision + information. A level teaches one idea: introduce → develop → twist → combine.

## 13. Living design

The game is found through playtests. The design changes constantly, but by rules:
- **After every playtest** edit a line, not a section (status and notes in the table, a
  parameter in a data file) and add a line to "Changelog":
  `| 2026-10-02 | M01 nitro_rate 1.0→1.4 | "builds up too slowly" — playtest 3 |`
- **The agent changes on its own** parameters, specs, gym order, implicit systems, numbers —
  with a changelog entry.
- **Only by the user's decision** do the pillars and anti-pillars, fantasy, aesthetic, genre,
  scale, a mechanic's tier and cutting an mvp mechanic change: AskUserQuestion with evidence
  (a playtest quote, a capture) → `studio.py decide … --by user` → edit CONCEPT.md → changelog.
- **Signal to change a pillar:** it is fun where the game breaks a pillar (the player does not
  do what was intended, and enjoys it). That means the game has been found — propose rewriting
  the pillar around it.
- A locked mechanic changed in substance — status back to `playtest`; after a major change
  repeat the affected §10 items. Do not write ahead.

## 14. What to propose to the skill

Record a proposal when (the lead will ask about saving it at the end of the phase):
- a technique from §1 turned "boring" into "fun" on the first try — `--phase 6 --kind technique`;
- the holism check caught a problem that a playtest later confirmed, or the same design
  mistake repeated in a second project — `--kind fix`;
- a genre blueprint not in §12 worked on the vertical slice — `--phase 1 --kind technique`.

```bash
python3 <skill>/scripts/learn.py propose --title "Pressure before tuning" \
  --phase 6 --kind technique --what "in a boring gym, first add a threat or a timer, then turn the knobs" \
  --when "the user said 'boring' at the first playtest of a mechanic" \
  --why "the drift gym became fun after adding a chase; tuning before that did not help" \
  --source "PLAYTESTS.md, M01"
```
