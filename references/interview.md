# Phase 1 "Idea" interview

Read at the start of phase 1 and on a pivot. Here: how to turn a phrase ("I want to make a
racing game") into an approved concept in 2–4 `AskUserQuestion` calls, question banks by
genre, ready-made payloads, the pitch card and what to record afterwards. General rules for
questions are in SKILL.md ("How to ask the user"), pillars and blueprints in `design.md`,
the story skeleton in `narrative.md`.

**Contents:** 1. Method · 2. Rounds and topic order · 3. Wording a question · 4. Banks
by genre · 5. Payloads and the pitch card · 6. What to record · 7. Autonomous · 8. Anti-patterns

## 1. Method: decide by default, ask by exception

You are a producer taking a pitch, not an examiner. The skeleton: rounds of independent
questions, a recommendation for each, and the agent looks up the facts. An unlimited
interrogation "until no assumptions remain" smothers the user, so assumptions are allowed
here as long as they are visible on the final card.

**1. Parse the phrase — before any questions.** Break it into CONCEPT.md slots and mark
each one: `[stated]` — said; `[implied]` — follows from the reference or genre; `[open]`.
"I want to make a racing game": stated — genre; implied — 30 s loop (steering on the edge),
failure (replay), single player, platform-driven controls; open — reference, scale, platform,
fantasy, loop twist, camera, story, progression, scale numbers.

**2. Filter.** Ask about a slot only if all of these are true at once: it is `[open]`; it is
expensive to change later (reference, scale, camera, story — the roots of the tree); the user
has taste here. Decide the rest yourself (in the example — progression, numbers, anti-pillars)
and put it on the card's "Assumed:" line. A silent assumption is bad, a visible one is fine.

**3. Never ask about facts.** What the reference contains, how many tracks it has, which
subgenres exist, what the platform can do — find out yourself (knowledge, WebSearch). An
unfamiliar reference ("a Balatro clone") — first a short search, then round 1.

**4. The budget is visible.** 2 content rounds + confirmation: 5–9 questions in 3
calls. The ceiling is 4 calls on your own initiative; a rich description or spec — straight
to Summary. In the text of the first question of a call write "Round 1 of 2": without a
visible end every question feels "not the last one yet". The `Pace` question in round 1
hands the length to the user: "Quick (Recommended)" — one more round, 3 calls in total;
"Detailed" — rounds 2 and 3 ("Round 2 of 3"), 4 in total; "You decide everything" —
straight to Summary.

**5. Stop words.** "Enough", "you decide", "good enough", "let's go already" in Other of any
question — stop asking, close the open slots yourself, go to Summary.

## 2. Rounds and topic order

Only independent questions go into one call: camera cannot be asked before the reference,
NFS and Mario Kart have different right answers.

| call | questions (`header`) | when |
|---|---|---|
| Round 1 | `Reference` (subgenre) · `Scale` · `Platform` (+ session length) · `Pace` | always; skip stated/implied |
| Round 2 | `Fantasy` · `Twist` (your own spin on the reference loop) · `Camera` (ASCII in `preview`) · `Story` (whether there is one + tone) | "Quick" and "Detailed" |
| Round 3 | `Progression` · `Failure` · `Won't do` (multiSelect of anti-pillars) | "Detailed", open slots only |
| Summary | `Summary`: pitch card in `preview` | always |

Replace a closed slot with a genre question (section 4) or simply leave the space unused.

**Vague idea** ("survival in the subway", "something cozy"): instead of `Reference` and
`Fantasy` — a single `Concept` with 3 radically different pitches ("Stalker raids
(Recommended)", "Station colony", "Fortress train"); in the `preview` of each, 5 lines: You ·
Loop 30 s · Level · Camera and reference · What makes it special. One click closes five slots:
reacting to something ready is easier than assembling a game out of attributes.

**"Clone of X":** almost everything is `[implied]` from X. Round 1 — `Differences`
(multiSelect: "What should differ from X? Anything unchecked stays as in X" — setting and
hero / story with cutscenes / core mechanic / progression) + `Scale` + `Platform` + `Pace`.
Round 2 — only about what was checked.

**Do not ask in phase 1:** visual style (phase 2, the board — style is not chosen in words),
engine and the exact platform list (phase 3), implementation, monetization.

**Answers.** A click is a decision, no "are you sure?". Text in Other is authoritative: the
slot becomes `[user]`, recompute the dependent defaults. If it changes a root (genre,
reference), reset the dependent `[implied]`/`[default]` and say so in a phrase in the next
question ("Since it's karting, not NFS — …"). "You decide" → `[default]`. Do not re-ask what
the user said and what is recorded in `.studioigor/`; on a pivot, ask only about the change.

## 3. Wording a question

- **Recommendation first, with "(Recommended)" in the `label`.** Derive round 2
  recommendations from round 1 answers: clicked through in a row, they should give a
  coherent game. Recommend the platform from context (for example, what the user's earlier
  projects targeted).
- **2–4 options, `label` 1–5 words, `description` — one line of trade-off**: what it
  gives and what it costs ("readable and cheap, weaker sense of speed"). Do not add your own
  "Other".
- **Positively and by name**: "For NFS-style arcade racing — which camera?", not
  "Not a first-person camera?" (agreement becomes "no") and not "based on answer 1".
- **All context goes in `question`, `description`, `preview`.** Write nothing above the
  widget: the question window will cover the text.
- **`preview`** (single-select only) — camera mockup, pitch card, mini concept card.
  **`multiSelect`** — only "how it differs from X" and "what not to do".
- **"You decide"** as a separate option — only in questions of pure taste where you have no
  strong opinion (setting, tone, twist), `description` "I'll pick to fit the pillars, you'll
  see it in the summary". In other questions "you decide" is a click on the recommendation.
- **`header` up to 12 characters** and names the decision: `Reference`, `Camera`, `Story`.

## 4. Question banks by genre

Format: `header` [round] → **recommendation** (trade-off) · option (trade-off) · …; append
"(Recommended)" to the recommendation's `label`, the trade-off goes into `description`.
Take only open slots, adjust the wording to the user's phrase. The recommendation is also the
default for "You decide everything" and autonomous mode. Recommend a story almost everywhere:
the user wants games with a story, heroes and cutscenes. Loops and systems — `design.md`.
Genre not on the list — take the closest one and the general questions from section 2.

### Racing
- `Reference` [1] → **Arcade like NFS** (speed, drift, forgives mistakes) · Kart racer like Mario Kart (power-ups, chaos, needs strong AI) · Derby like FlatOut (ramming, expensive physics) · Sim-cade like Forza (weight, racing line, higher barrier)
- `Format` [2] → **Circuits and sprints through the city** (dense, cheap on content) · Open city (freedom, but expensive and empty) · Police chases (tension, needs cop AI)
- `Twist` [2] → **Drift feeds nitro and money** (risk = reward) · A chase in every race (chaos) · Destructible shortcuts (the route is a choice) · You decide
- `Story` [2] → **Street drama: rookie vs. the king of the district** (cutscenes between races) · Comedy with colorful rivals (dialogue) · No story (career and records)
- `Progression` [3] → **Money → tuning and new cars** (clear why you race) · A ladder of district bosses (story-driven) · Only medals and records (pure arcade)
### Shooter
- `Reference` [1] → **Fast FPS like DOOM** (movement, crowds) · Tactical with cover (slower, low HP) · Top-down twin-stick like Enter the Gungeon (readable, cheap) · Extraction (loot and risk, heavy meta)
- `Camera` [2] → **First person** (immersion, precise shooting) · Third person (hero visible, needs animation) · Top-down (overview, simpler assets)
- `Structure` [2] → **Campaign of levels with cutscenes** (pacing, story) · Arenas and waves (replayable, cheap) · Hub and missions (freedom, more content)
- `Story` [2] → **Action flick: hero, villain, twist** (cutscenes, boss at the end) · Dark sci-fi mystery (notes, environment) · No story (arena)
- `Arsenal` [3] → **New weapons over the campaign, each one changes combat** · Upgrades and perks (build) · Loot with rarities (grind)
### Platformer
- `Reference` [1] → **Precise 2D like Celeste** (hard, fair, instant restart) · Metroidvania like Hollow Knight (abilities open paths) · 3D collectathon like A Hat in Time (exploration, more expensive) · Runner (one button, mobile)
- `Twist` [2] Main verb? → **Dash in any direction** (speed and precision) · Grappling hook (swing, physics) · Gravity or world switch (puzzles) · You decide
- `Difficulty` [2] → **Hard but fair, frequent checkpoints** · Gentle, for everyone (cozy) · Easy path + hard secrets
- `Story` [2] → **Quiet story told through the world + intro and ending** · Characters and dialogue (more text) · No story
### Action / RPG
- `Reference` [1] → **Isometric action like Hades** (fast combat) · Third-person soulslike (heavy combat, stamina) · Adventure like Zelda (puzzles + combat) · Turn-based party RPG (tactics, lots of content)
- `Hero` [2] → **A set hero with a backstory** (stronger story) · Your own character and classes (expression, replayability) · A party of companions (dialogue, more expensive)
- `Combat` [2] → **Fast: dodges and combos** · Heavy: parries and stamina · Tactical pause (decisions matter more than hands)
- `Story` [2] → **Dark fantasy, hero's arc, cutscenes** · Light adventure with humor · Science fiction
- `Progression` [3] → **Skills + gear, a breakthrough every 20–30 minutes** · Gear only · Abilities open the world
### Strategy / Tower defense
- `Reference` [1] → **Tower defense like Kingdom Rush** (placement against waves) · RTS-lite (base, army, one AI) · Turn-based tactics like Into the Breach (unhurried decisions) · Autobattler (composition, short)
- `Twist` [2] → **A hero on the field with abilities** (someone to play as) · The player builds the maze (space) · Cards instead of a shop (randomness) · You decide
- `Structure` [2] → **Campaign of 10–15 maps with a story** · Endless waves and records · Roguelite run across maps
- `Story` [2] → **Briefings with characters + cutscenes on key maps** · Lore in descriptions · No story
### Puzzle / casual
- `Reference` [1] → **Grid logic like Baba Is You** (pure "aha" moments) · Physics like Cut the Rope (rotate and place) · Merge or match-3 (short, mobile) · Words or numbers
- `Session` [1] → **Levels of 1–3 minutes** · Long puzzles of 10–20 minutes · Endless mode
- `Mistakes` [2] → **No failure: undo, restart** · Stars for optimal solutions (replayability) · Move limit or timer (tension)
- `Story` [2] → **Light frame: a character, a world, scenes between chapters** · The puzzles themselves reveal the story · No story
### Survival / crafting
- `Threat` [1] → **Environment and night: hunger, cold, monsters in the dark** · Zombie hordes (action) · Other survivors (AI, trading) · A disaster on a timer (urgency)
- `World` [2] → **A handcrafted island or zone** (control over pacing) · Procedural world (replayable, emptier) · Expeditions from a base (structure)
- `Base` [2] → **Free-form building** (expression, expensive) · Slot-based modules (cheaper) · No base, nomad
- `Story` [2] → **Escape: why you are here and how to get out, an ending** · A mystery told through notes and finds · Sandbox with no ending
- `Death` [3] → **You lose your bag, the world stays** · Hardcore: start over · Gentle: respawn at the bed
### Horror
- `Reference` [1] → **Run and hide, no weapons, like Amnesia** · Survival horror with scarce ammo like RE · Psychological exploration (story over threat) · Co-op horror (expensive, networking)
- `Length` [1] → **2–3 hours, one night** · Episodes of 30–40 minutes · Short runs
- `Threat` [2] → **One stalker with smart AI** (tension builds) · Different monsters (variety) · Unseen and paranormal (anxiety)
- `Camera` [2] → **First person** (scariest) · Third person or fixed angles · 2D side view (cheaper, stylized)
- `Story` [2] (mandatory in horror) → **Mystery through notes, environment and a few cutscenes** · Characters and dialogue · Minimal words, atmosphere only
### Roguelike
- `Reference` [1] → **Action like Hades** (hands-on combat) · Deckbuilder like Slay the Spire (decisions) · Auto-combat like Vampire Survivors (cheap, mobile) · Turn-based dungeon
- `Run` [1] → **20–30 minutes** · 5–10 minutes (mobile) · An hour or more
- `Meta` [2] → **Unlocks change the next run** (new options, not +%) · Player knowledge only (pure roguelike) · Stat upgrades (grind)
- `Build` [2] → **Item synergies** · Character classes · Deck
- `Story` [2] → **Story through death, like Hades: every run moves the plot** · Lore in descriptions · No story
### Simulation / management
- `Reference` [1] → **Your own business, like Stardew or a café** (orders, characters) · City or colony (systems, crises) · Logistics and factory (optimization) · Idle (offline progress)
- `Rhythm` [2] → **Days with an end-of-day summary** (a natural stopping point) · Real time with pause · Idle
- `Pressure` [2] → **Soft goals and orders, failure is rare** · Crises and events (tension) · Sandbox without goals
- `Story` [2] → **Residents with their own stories and errands** · A framing goal (save grandpa's farm) · No story
- `Progression` [3] → **New zones and buildings, a breakthrough every in-game week** · Prestige and restart · Story chapters

## 5. Payloads and the pitch card

**Round 1 for "I want to make a racing game"** (everything is open except the genre):

```json
{"questions": [
 {"header": "Reference", "multiSelect": false, "question": "Round 1 of 2. Racing — what should it resemble most?",
  "options": [
   {"label": "Arcade like NFS (Recommended)", "description": "Speed, drift, nitro; forgives mistakes — easiest to make fun"},
   {"label": "Kart racer like Mario Kart", "description": "Power-ups and chaos, cartoony; needs strong rival AI"},
   {"label": "Derby like FlatOut", "description": "Ramming and destruction; body physics is the most expensive part"},
   {"label": "Sim-cade like Forza", "description": "Weight, racing line, tuning; for fans, higher barrier to entry"}]},
 {"header": "Scale", "multiSelect": false, "question": "How big is the game? I'll check exact numbers against the reference.",
  "options": [
   {"label": "Small game (Recommended)", "description": "1 city, 6–8 tracks, 5–6 cars, a 1–2 hour story — a real game, realistic to finish"},
   {"label": "Demo slice", "description": "1 track and 10 minutes of play — tests the idea, not a game yet"},
   {"label": "Big game", "description": "A 5+ hour career, 20+ tracks — months of work"}]},
 {"header": "Platform", "multiSelect": false, "question": "Where and for how long at a time will people play? We'll pick the engine later, in phase 3.",
  "options": [
   {"label": "PC, 20–40 minutes (Recommended)", "description": "Keyboard and gamepad, full 3D, a PC store or your own site"},
   {"label": "Browser, 5–10 minutes", "description": "Web portal or your own site, one-click entry; simpler graphics"},
   {"label": "Mobile, 3 minutes", "description": "Touch steering, short races, simplified controls"}]},
 {"header": "Pace", "multiSelect": false, "question": "How many more questions before we start? Whatever I don't ask, I'll decide and list in the summary.",
  "options": [
   {"label": "Quick (Recommended)", "description": "One more round of 3–4 questions, then the game card for approval"},
   {"label": "Detailed", "description": "Two more rounds: fantasy, loop, camera, story, progression, what not to do"},
   {"label": "You decide everything", "description": "No more questions — straight to the card for approval"}]}
]}
```

**Camera in round 2** (ASCII screen mockup in `preview`, single-select only):

```json
{"header": "Camera", "multiSelect": false, "question": "Round 2 of 2. NFS-style arcade racing — which camera?",
 "options": [
  {"label": "Behind the car (Recommended)", "description": "Conveys speed and drifting best; the NFS standard",
   "preview": "+--------------------------+\n|   ~~~ city lights ~~~    |\n|     |              |     |\n|       |    ^     |       |\n|         [==CAR==]        |\n| 212 km/h         LAP 2/3 |\n+--------------------------+"},
  {"label": "Cockpit", "description": "Immersion and risk; drifts and rivals behind are harder to see",
   "preview": "+--------------------------+\n|     |     road     |     |\n|  ======================  |\n|  |  gauges    ( O )   |  |\n|  |  212 km/h  wheel   |  |\n|  [  rear-view mirror  ]  |\n+--------------------------+"},
  {"label": "Top-down", "description": "Like GTA 2 or Micro Machines; readable and cheap, weaker sense of speed",
   "preview": "+--------------------------+\n| ## |        |  ##  ##    |\n| ## |   ^    |  ##  ##    |\n|    |  [M]   |            |\n| ## |________|  [map]     |\n| pos 3/8          LAP 2/3 |\n+--------------------------+"}]}
```

**Summary.** The preview IS the summary: the concept is visible whole, not pieced together
from memory.

```json
{"questions": [{"header": "Summary", "multiSelect": false,
 "question": "Summary. Do you approve the game? I decided everything on the 'Assumed' line — change any of it via Other.",
 "options": [
  {"label": "Approve (Recommended)", "description": "I lock the concept; next — visual style on a board with references",
   "preview": "<pitch card below, lines separated by \\n>"},
  {"label": "Bolder", "description": "Same concept, twist pushed to the edge: a chase in every race",
   "preview": "<the same card with Pitch, Loop 30 s and Pillars rewritten bolder>"},
  {"label": "Change one thing", "description": "I'll ask in one question what to replace; the rest stays as is"}]}]}
```

The pitch card is about 12 lines, monospaced, lines up to ~60 characters:

```
NIGHT DRIFT — arcade racing (working title)
Pitch:       NFS Underground where drift is currency; night city
Fantasy:     a street-racing rookie who takes over the district
Loop 30 s:   throttle → drift on the edge → nitro for drift → pass
Loop 10 min: race → finish place → money and reputation
Session:     2–3 races in 20 minutes, tuning between them
Camera:      behind the car · PC, keyboard and gamepad
Story:       street drama, 5 cutscenes, district boss at the end
Scale:       small game — 1 city, 8 tracks, 6 cars
Pillars:     speed on the edge · drift feeds all · living city
Won't do:    open world, multiplayer, realism
Assumed:     progression, failure = replay, 8 tracks, controls
```

"Assumed:" is mandatory and lists EVERY `[default]` slot: this keeps "you decide" honest —
every decision you made is visible when the user looks. "Bolder" is a full card in its own
`preview`; choosing it is already an approval. "Change one thing" — one `Edit` call "What
should change?" with 3–4 alternatives from "Assumed" (`label` — the new value: "Cockpit
camera"). Apply it, show the card as text and write; do not confirm again — the edit is the
approval. This is the only call beyond the ceiling, and it is on the user's initiative. Apply
an edit typed in Other the same way.

## 6. After approval: what to record and where

Briefly, a line per slot: the concept is a working tool, not an essay (SKILL.md, rule 1).

1. **CONCEPT.md.** The pitch is one sentence. Every slot is a line with a source tag:
   `[user]` answered, `[stated]` was in the phrase, `[implied]` from the reference or genre,
   `[default]` you decided. `- **Camera:** behind the car — [user]`;
   `- **Failure:** lost the race → replay with no penalty — [default] genre`.
   Replace ALL `<…>`: `studio.py` counts them as unfilled, and the phase will not close. In
   "What the agent decided" — the same slots as in "Assumed".
2. **Pillars and anti-pillars** (same file). 3–5 falsifiable pillars, each one forbids
   something: "Drift feeds everything — nitro, money and reputation come only from drifts",
   not "fun driving". Anti-pillars — 1–3 lines from `Won't do` or your `[default]` choices.
   Derive them from the answers, do not ask separately. Pillar tests — `design.md`.
3. **STORY.md.** If there is a story — the skeleton per `narrative.md`: logline, the world in
   1–2 lines, 2–4 characters, 5–7 arc beats, cutscenes with status `idea`. If not — the whole
   file is one line `No story: <why>`.
4. **DESIGN.md, `## Mechanics`.** 6–10 rows from the blueprint and the twist. M01 is the
   mechanic of the 30-second loop, it is built first in a gym. Each is tied to a pillar;
   without a pillar — cut it or add a pillar. Status `idea`, scene `—`. In a story game
   dialogue and cutscenes are mechanics too. In "Progression and meta" — 2–3 lines with
   breakthrough points, not "+10%".
   ```
   | M01 | Driving and drift → nitro | mvp | Drift feeds everything | idea | — | 30-s loop |
   | M02 | Cutscenes and dialogue | mvp | Living city | idea | — | intro, ending |
   | M03 | Police chases | full | Speed on the edge | idea | — | |
   ```
5. **SCOPE.md.** "Reference inventory" — a line of facts about the reference (find out
   yourself). "Contract" — 3–6 lines from the scale; counters appear after phase 4:
   `- [ ] tracks: 8 pcs — count: manual: after phase 4`.
6. **Decisions, gates, commit** — in one Bash call. `decide` — only key decisions,
   4–8 lines, not every slot:
   ```bash
   S=<skill>/scripts/studio.py
   python3 $S decide "concept: arcade racing like NFS, drift feeds nitro and money" --by user --why "pitch card approved" --options "arcade NFS / kart / derby / sim-cade" --phase 1
   python3 $S decide "scale: 1 city, 8 tracks, 6 cars; platform (prelim.): PC, 20–40 min" --by user --why "round 1; phase 3 will refine the platform" --phase 1
   python3 $S decide "camera behind the car; story — street drama, 5 cutscenes" --by user --why "round 2" --phase 1
   python3 $S decide "progression: money → tuning and cars; failure = replay" --by agent --why "blueprint default, shown in 'Assumed'" --phase 1
   for g in "interview" "falsifiable pillars" "story skeleton" \
            "draft mechanics" "pitch card"; do python3 $S tick --phase 1 "$g"; done
   python3 $S note "concept approved" "phase 2: style directions and references"
   python3 $S commit "studioigor: phase 1 — concept 'Night Drift' approved"
   ```
   Tick `manual` gates only when the file is actually filled. "Approved the pitch card" is a
   `user` gate: only after "Approve", "Bolder" or the user's edit. After that `status` must
   show phase 2.
7. **A lesson for the skill.** If the user irritably asked again, skipped a question as
   unnecessary or said "that's how it should have been from the start" — that is a signal.
   Record it: `learn.py propose --kind process --phase 1 …`. A direct "always do it this
   way" — straight to `learn.py prefer "…" --phase 1` (this game only; `--global` only for a
   rule about how to work with the user in any game).

## 7. Autonomous mode

A run in a loop without the user (`/loop`, "work while I'm away"): do not ask a single question — a night-time question blocks
work until morning. Close every open slot with the recommendation from section 4 tagged
`[default]`, build the card, record everything per section 6 with `decide --by agent`. Do not
tick user gates — skip them and put the card into `## Now` via `note`:
`studio.py tick --phase 1 "pitch card" --skip "autonomous: waiting for the user"`.
On autopilot (independent development, `autopilot.md`) — `tick … --proxy`.
When the user returns, show Summary as the first call; after "Approve" — `tick` and
`decide --by user`.

## 8. Anti-patterns

| symptom | why it's bad | what to do |
|---|---|---|
| Round after round with no end | "surely this is the last one" — the user runs out of steam | budget 2+1, ceiling 4, "Round N of M", the `Pace` question |
| Wall of text above the widget | the question window covers the text, no time to read | context only in `question`/`description`/`preview` |
| Feels like an exam | the user designs the game for the agent | recommendation first, click = decision, "You decide" |
| Question about a fact | "how many tracks are in NFS?" — that's your job | find out yourself; ask only about taste and scale |
| Re-asking, "are you sure?" after a click | what was said is already decided; repetition annoys most of all | `[stated]`/`[user]` are never asked |
| Cold confirmation | "confirm" with no summary: the concept is pieced together from memory | Summary with the card in `preview` and an "Assumed:" line |
| Silent defaults | the user doesn't know what was decided for them | every `[default]` goes into "Assumed" and "What the agent decided" |
| 10 questions about attributes of a vague idea | assembling a game from attributes is hard | one `Concept` with 3 pitch cards |
| A multi-page concept essay | goes stale, nobody reads it | a line per slot; edit only when a decision changes |
