# Narrative — story, dialogue, cutscenes, ending

When to read: in phase 1 — §1–4 (the STORY.md skeleton); in phase 6 — §6–8 and §11 (dialogue and
cutscenes as mechanics); in phases 7–8 — §5, §7, §9, §12 (story in the vertical slice and
content); in phase 10 — §9–10 (credits, subtitles, localization). The user wants real games with
a story, characters and cutscenes, so narrative here is a full layer of the game, not decoration.

**Contents:** §1 Is a story needed and how much · §2 STORY.md — a skeleton in lines · §3 Structures ·
§4 Ludonarrative harmony · §5 Delivery tools · §6 Dialogue · §7 Cutscene pipeline ·
§8 Cutscenes by engine · §9 Intro, ending, credits · §10 Voice, subtitles, localization ·
§11 Narrative in DESIGN.md and STORY.md · §12 Checklist · §13 What to propose to the skill

## 1. Is a story needed and how much

How much story the game will have is decided by the user: it is a question of taste and scale.
The question is part of the interview rounds (`interview.md`), no separate round is needed.
Base the recommendation on the genre. By default recommend at least a "frame": the user wants
games with a story, not tech demos.

| genre | typical weight | main delivery | example |
|---|---|---|---|
| arcade racing, sports | frame: a rival, a career, 4–6 beats | briefings between races, intro, ending | NFS Most Wanted — a blacklist of 15 racers |
| platformer, puzzle | frame or theme-metaphor | environment, short dialogue, mechanic as metaphor | Celeste, Braid |
| roguelike | medium, through repetition | dialogue in the hub, a beat per death or run | Hades |
| action/RPG, adventure | full: arc, characters, quests | dialogue, cutscenes, quests | The Witcher 3 |
| horror | medium, understatement | environment, notes, rare cutscenes | Amnesia, Resident Evil 7 |
| shooter with a campaign | medium | briefings, radio barks, scripted scenes | Half-Life 2 |
| TD, RTS, idle, management | frame | mission briefings, advisor characters | Kingdom Rush |
| survival | light: "get out" or "survive" | environment, notes, ending | Subnautica |

**"No story" is a legitimate decision** (Tetris, Mini Motorways): STORY.md is one line
"No story: …" with the reason. Meaning is still carried by the theme and the fantasy: the title,
setting, art, music, interface text, victory screen. Such a game still needs a title screen and
an ending with results and credits. A story costs production (cutscenes, lines, portraits, voice
acting), so its volume — beats, cutscenes, characters — is recorded as numbers in SCOPE.md, like
any content.

## 2. STORY.md — a skeleton in lines

By the end of phase 1 STORY.md has a logline, the world, 2–4 characters, 5–7 arc beats with their
place in the game and 2–5 cutscenes with status `idea`; after that the skeleton grows in phases 6–8. For a small game the whole file is about 60 lines. Do not write world
bibles and lore documents in advance: everything not in STORY.md lives in the dialogue files and
in the levels. You write the skeleton yourself from the interview answers. Show the logline and
the arc as the "Story:" line of the pitch card at the final interview confirmation (interview.md
§5) — there is no separate question. A separate question about the story — only if the story is
`[default]` and the user picked the "Detailed" pace.

- **Logline** — one sentence: "[hero] must [goal], or else [stakes], but [obstacle]".
- **World** — 2–4 lines: where and when; one world rule that changes the gameplay; the tone in one
  word and a reference; "Structure: …" (§3); the truth behind the mysteries — the answer to every
  riddle, even if the player never learns it (without it the story will start contradicting
  itself).
- **Characters** — each serves the gameplay: rival-boss, mentor-shop, quest giver. In the
  "trait/voice" column — how the character talks, plus a sample line of up to 120 characters. All
  of their lines are written after this sample. Lines of different characters must not be
  interchangeable.
- **Arc** — the "where in the game" column names a specific moment: a level, an unlock, a boss
  or a mechanic id. An empty cell means the beat is not in the game.

Sample lines for racing (the table headers are already in the template):
```
- Street racer Lex must win the night series against the Shades gang, or he'll lose his father's garage,
  but the gang controls both the tracks and the police.
- a wet neon city in the '90s; until 3 a.m. the streets belong to the gang, the police stay out
- tone: thrill with bitterness (Drive + NFS Underground) · Structure: escalating chapters
| Lex | hero | win back the garage and his father's name | a man of few words, jokes when scared: "Well, at least it's not boring." |
| Red | leader of the Shades, final boss | prove the street is hers | mocking, gets personal right away: "Late for your own funeral?" |
| 1 | the gang collects the father's debt | intro CS01 → race 1 | cutscene |
| 3 | twist: Red knew his father | after the chapter 1 boss, nitro unlocked (M04) | cutscene CS02 |
```

## 3. Structures

Pick one and write it into "World".
- **Three acts** (the default for linear games): setup ~25% (world, goal, tutorial) →
  confrontation ~50% (the midpoint twist is the best place for a big mechanic breakthrough) →
  resolution ~25% (final boss or race).
- **Kishōtenketsu** — introduction → development → twist → reconciliation, conflict is optional.
  For cozy games and puzzles; a single level is built on the same scheme (that's how Nintendo
  does it).
- **Escalating chapters** — chapter = new location + new opponent or stakes + new mechanic;
  in phase 8 a chapter = a content batch. The NFS Most Wanted blacklist, Hotline Miami.
- **Story through repetition** (roguelike) — beats are tied to counters (deaths, runs, boss
  encounters), not to the level number; hub characters remember what happened. Failure moves
  the story and stops being a loss. Hades.
- **Fragments.** The story is assembled from the environment and notes in any order, but the
  main event is still delivered explicitly. Suits horror and metroidvanias.

## 4. Ludonarrative harmony

Story and mechanics must say the same thing. The term "ludonarrative dissonance" came from
a critique of BioShock (Clint Hocking, 2007): the story told you to help others, while the
mechanics rewarded self-interest.
- **Beat = gameplay event.** Story beats are a new ability, an unlocked zone, a boss, a
  progression breakthrough (`design.md` §6). Nitro appears because the mechanic set it up after
  the first win, not "on level 5".
- **What the story praises, the game rewards.** A protector hero does not get points for
  destruction. Check any contradiction you find against holism item g in `design.md`.
- **Mechanic as metaphor.** The dash in Celeste is the heroine's anxiety. In Brothers: A Tale of
  Two Sons the ending hits through controlling two brothers with one gamepad. Ask yourself: which
  verb of the game can say what the story says in words?
- **Playing beats watching.** Take control away from the player only if the staging gives more
  than the gameplay. The best beats are played by the player: a chase, an escape, the final blow.
- **Difficulty follows the story.** A crisis in the story is pressure in the game, the
  resolution is a breather.

## 5. Delivery tools

| tool | what for | cost | trap |
|---|---|---|---|
| in-engine cutscene | 3–5 key beats: intro, twist, ending | high: cameras, animation, sound | takes away control; ≤60–90 s, always skippable |
| comic panels + text + music | intro and transitions in 2D and small games | low–medium (frames from the engine, drawing or image generation) | the style must match the game |
| dialogue (box, name, portrait) | characters, quests, choices | medium: system, text, portraits | wall of text; ≤3 lines in a row without action |
| barks (lines during gameplay) | character and the world's reaction | low, but many are needed | repetition is infuriating: 3+ variations, cooldown |
| environment | the history of a place, the world without words | medium, together with the level | may go unnoticed — don't put anything mandatory there |
| notes, logs, collectibles | lore for the curious | low | don't hide the main story there |
| UI and meta text | level names, item descriptions, briefings | very low | — |
| scripted event | a collapse, a chase, a boss appearance without taking control | medium | must read on the first viewing |

In a small game the bulk of the story is carried by dialogue, barks, environment and scripted
events. Keep cutscenes only for the 3–5 main beats.

## 6. Dialogue

**Research is mandatory** before the dialogue gym (`research/mech-<id>.md`): which plugin version
fits the engine version from TECH.md, the license, whether the project is alive, how the reference
games present dialogue (box or bubbles, portraits, text speed). The starting point below was
checked against GitHub releases on 2026-09-27 — re-check before work.

| engine | recommended | alternative |
|---|---|---|
| Godot 4.6+ | Dialogue Manager 4 (nathanhoad) v4.1.0: text `.dialogue` files, conditions and mutations, bubbles, line export; MIT. For Godot 4.4–4.5 — the v3.10 branch | Dialogic 2 (2.0-alpha-20, Godot 4.5+): visual editor, portraits, visual-novel style. Still alpha, the API changes between releases |
| Unity | Yarn Spinner for Unity v3.2.8: `.yarn` scripts, line view, localization by line id | ink + ink-unity-integration 2.0.0: strong branching and state |
| Web | inkjs v2.4.0: the ink runtime for JS, `.ink` compiles to JSON | your own JSON format if there are only dozens of lines |
| Unreal | research from scratch: Inkpot (ink for UE), Yarn Spinner for Unreal. Versions not verified | — |

Choose text formats. The agent writes and edits lines as files, the git diff is readable,
translation is exported. A visual editor is needed only if the user wants to edit dialogue
themselves.

The system must support (these are implicit systems, `design.md` §5): a speaker with a name and
portrait (portraits per `assets.md`); named substitutions `{player_name}`; choices and conditions
on flags; mutations (flag, item, quest, money); events for gameplay (cutscene, animation,
camera); flags in the save; skipping and fast-forwarding text; string export for translation.

Text rules:
- Lines live in data files (`dialogue/*.dialogue|.yarn|.ink`), not as strings in code.
- A line is up to 120 characters, one thought; no more than 3 lines before an action or a choice.
- The voice comes from the "trait/voice" column. Cover the name: is the speaker recognizable?
  Read it aloud.
- A choice either changes something in the game or reveals the character.
- Duplicate anything important for progression as an objective in the HUD: someone who skipped
  the dialogue must not get stuck.
- If there are many lines, write them with a subagent in a worktree (`team.md`), handing it the
  voices from STORY.md.

Dialogue gym: two NPCs, a branch with a flag and a condition, a mutation (giving an item), skip,
name substitution, a max-length line at the minimum resolution. The first feedback question for
narrative is "Is it interesting?" instead of "Is it fun?", then "readable? pacing? do you want to
read on?"

## 7. Cutscene pipeline: idea → storyboard → blockout → final

Each step ends with a visible artifact and a user decision. Do not start final animation before
the blockout is approved: rework at blockout is dozens of times cheaper.

1. **idea.** A line in STORY.md → "Cutscenes": what happens, which beat, target length.
2. **Script = storyboard.** There is no separate script file. Shots are cards on the board
   `.studioigor/boards/cs-<id>/board.json`, one per shot: `title` — "3. Close-up: Red",
   `text` — action, line, duration "4 s", `media` — the frame. Capture frames from the engine with
   placeholders in the look-dev scene (cheap and honest about the angle) or with image generation,
   if available, following the art bible and marked "generated". The norm is 5–15 shots per minute. `board.py build`,
   then in the background `serve --open --until-feedback`; `mode: multi`, the question "mark the
   shots to redo". Status → `storyboard`.
3. **blockout** in the engine: cameras per shot, placeholders or rough animations, lines as
   subtitles, temp music. This is where timing is locked. Record a video (Godot
   `--write-movie`, Playwright `recordVideo`, Unity Recorder), convert it to mp4 with ffmpeg and
   put it on the board — the board supports video. Ask about pacing, clarity and emotion. Status →
   `blockout`.
4. **final**: animation, lighting, VFX, music, sound, voice (§10), subtitles. Capture the result,
   get the user's approval. Status → `final`, then `studio.py commit "…" --tag cs/<id>`.

**Staging:** first a wide shot (where are we), then a medium, a close-up for emotion; the 180°
rule (the camera does not jump the line between the speakers); one shot — one camera move, no
shorter than 2 s; on a line, the frame shows the speaker or the one reacting; lighting per the art
bible, the hero's silhouette reads.

Rules for any cutscene:
- Always skippable — by holding a button with an indicator, so it can't be skipped by accident.
- Does not repeat after death: the checkpoint is after it, the "watched" flag is in the save.
- No longer than 60–90 s; longer — split it or make it playable.
- Leads into gameplay without a jolt: the last camera blends smoothly into the gameplay camera.
- A cutscene is data (a timeline or animation resource) and is triggered by a story flag, not
  hard-coded in the level code: that way saves and replays work.

## 8. Cutscenes by engine

Exact APIs and versions are in the mechanic research. Below is where to start.
- **Godot 4.** AnimationPlayer serves as the timeline. Its tracks: transform and `current` of
  Camera3D/Camera2D, properties, method calls (starting a Dialogue Manager line, events),
  audio, triggering character animations. A camera dolly — Path3D + PathFollow3D. Smooth
  blends between cameras, like in Cinemachine, come from the Phantom Camera addon (v0.11.0.3,
  2026-07). Capture — Movie Maker (`--write-movie <file> --fixed-fps 30`), with a window.
- **Unity.** Timeline (PlayableDirector) + Cinemachine 3: virtual cameras, blends,
  dolly. Signal tracks — events for dialogue; Yarn Spinner drives Timeline with commands.
  Capture — Recorder. Work in the editor goes through the `unity` CLI and the editor MCP. Package
  versions — in the research.
- **Unreal.** Level Sequencer + Cine Camera Actor + Camera Rig Rail, capture — Movie Render
  Queue. Not verified, research is mandatory.
- **Web.** Three.js — your own mini timeline (an array of `{t, action}`: camera tweens, fades,
  subtitles) or a GSAP timeline (free, but not MIT — check the license in the research). Phaser —
  `cameras.main.pan / zoomTo / fade` and tweens. Capture — Playwright.

## 9. Intro, ending, credits

**Intro.** Title screen with music → "New game" → intro (skippable) → control.
The intro sets up the fantasy and the first goal; the player has control no later than 60–90 s
after "New game", unless the user decided otherwise. From cheap to expensive: a playable intro
(the first level is the intro, story through barks) → comic panels → in-engine cutscene. The intro
is CS01, its pipeline runs in phases 6–7: without an intro the vertical slice does not close.

**Ending.** Order: resolution of the stakes from the logline → final cutscene → epilogue (what
became of the world and the heroes, 2–4 lines or frames) → results (time, deaths, things found) →
credits → menu with a "completed" mark and whatever unlocked (new game+, free mode). Never end on
a frozen frame or a silent return to the menu.

**Credits** are assembled from the ASSETS.md license registry, not written by hand: a small
script generates `credits.*` from the registry rows (asset, author, license, link). Add the engine
and its required notices (Godot requires the text of its license and the licenses of third-party
components — the "Complying with licenses" page), fonts, music, sound, dialogue and camera
plugins, a mark on generated assets. The credits scroll to music and can be skipped. This is a
phase 10 gate.

## 10. Voice, subtitles, localization

**Voice** is the user's decision: it is money and taste. Options by cost:
1. **Text only plus voice "blips"** — a short sound per letter pitched to the character
   (Undertale, Animal Crossing). Cheap and cute. The default for a small game.
2. **TTS.** `say` on macOS (`say -v <voice> -o line.aiff "…"`, a voice for the game's language) — robotic:
   good for a blockout draft or for robot characters. Also — any TTS available in the
   environment; cloud services — only with the user's account. Source and terms go into the
   ASSETS.md registry.
3. **Live voice.** The user records lines from a list, the agent cuts and normalizes them with
   ffmpeg.

**Subtitles** exist for every spoken line and are on by default: the speaker's name in the
character's color, no more than 2 lines, a backing box or contrast ≥7:1, size no smaller than the
HUD text, on screen for no less than ~1 s, speed no higher than ~17 characters per second.

**Localization — the basics, even for one language.** All player-facing strings live in files
with keys, not in code. Substitutions are named (`{count}`); do not glue a phrase together from
pieces — word order and grammatical cases differ between languages, numbers need plural forms. In
the UI leave 30–40% headroom: text grows in translation. Check a font covering all target scripts at
look-dev, not at release. Tools: Godot — TranslationServer + CSV/PO (Dialogue Manager exports
strings); Unity — the Localization package (`com.unity.localization`, String Tables) and Yarn line ids;
web — JSON by keys. The release languages are determined by the platform research in phase 10.

## 11. Narrative in DESIGN.md and STORY.md

**Systems are mechanic rows.** Dialogue and cutscenes are mechanics with a gym, research and
a playtest, like all the others; their place is after the core loop, before the vertical slice
(the slice needs an intro and a first goal). In a small game a single "Cutscenes and dialogue"
row is enough.
```
| M05 | Dialogue (system + UI) | mvp | Living city | idea | scenes/gyms/dialogue_gym.tscn | Dialogue Manager 4; flags in the save |
| M06 | Cutscenes: system + intro | mvp | Living city | idea | scenes/gyms/cutscene_gym.tscn | AnimationPlayer + cameras, skip, subtitles; intro = CS01 |
| M07 | Barks during races | full | Living city | idea | — | 3+ variations, 8 s cooldown |
```
**Individual cutscenes are content, not mechanics.** Do not add CS02 and later as mechanic rows,
or the table will bloat. They live in STORY.md → "Cutscenes" and go through the §7 pipeline in
phase 8. Statuses strictly: `idea` / `storyboard` / `blockout` / `final`. Sample row:
`| CS01 | Intro: "Late for your own funeral?" | 60 s | blockout |`.

**Volume** is recorded in SCOPE.md as a number with a counter:
`- [ ] Cutscenes final: 5 pcs — count: grep -cE '^\| *CS[0-9]+ .*\| *final *\|' .studioigor/STORY.md || true`

**Arc → gameplay.** The "where in the game" column holds mechanic ids, levels and unlocks from
`design.md` §6. After the vertical slice and each content batch, walk the "Arc" table: every beat
must be in the build where it is recorded.

## 12. Checklist "the story is felt in the game"

Go through it at the gates of phases 7 ("…story presentation") and 8 ("story played from start to
finish"). Check everything except the last two items yourself from captures and the build; those
two — with the user.
- [ ] Within the first 2 minutes it is clear who the hero is and what they want. This is visible from the game, not from a description.
- [ ] Every arc beat happened in the build where it is recorded in "where in the game".
- [ ] The main progression breakthroughs are explained by the story.
- [ ] Main characters are recognized by name, silhouette or portrait and the voice of their lines.
- [ ] Every location has at least one environmental detail that tells a story without text.
- [ ] No wall of text: no more than 3 lines without action, anything important duplicated as an objective.
- [ ] Cutscenes are skippable, do not repeat after death, last no longer than 90 s and lead into the game without a jolt.
- [ ] The tone is consistent: music, art, text and mechanics say the same thing.
- [ ] Every spoken line has subtitles. All strings live in data files.
- [ ] Ending: resolution of the stakes → epilogue → credits from the license registry → menu with a "completed" mark.
- [ ] After finishing, the user retells the story in two sentences.
- [ ] The user names a favorite character or moment. If they can't, the story doesn't grab:
      find the strongest beat and make it playable (§4).

## 13. What to propose to the skill

Record a proposal in two cases (the lead will ask about saving it at the end of the phase):
- cheap delivery worked at a playtest on the first try (a six-panel comic instead of an
  animated cutscene, blips instead of voice acting) — `--phase 8 --kind technique`;
- research found a dialogue or cutscene plugin better than the §6 and §8 tables, or a version
  that breaks compatibility — `--kind tool`, with the research file in `--source`.

```bash
python3 <skill>/scripts/learn.py propose --title "Comic intro" \
  --phase 7 --kind technique --what "an intro of 6–8 comic panels + subtitles + music instead of animation" \
  --when "a 2D or small 3D game, no ready animations by the vertical slice" \
  --why "the user approved it on the first showing; an hour of work instead of a day" --source "STORY.md, CS01"
```
