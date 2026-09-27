# Polish (phase 9) and release (phase 10)

Read in phases 9 and 10. Polish: the "one gap" round, facets with a bar and a
professional's eye, juice, sound, the first 60 seconds, HUD and accessibility, budgets, gauntlet,
when to stop. Release: platform research, ship gates, platforms, store materials,
credits, patch notes, publishing, the final report, the retrospective. Moments of delight
(surprises, secrets, rare events) — `gamedesigner.md`, only with the user's "yes".

**Contents.**
- Phase 9: polish round · facets · typical numbers · juice · sound log · the first 60
  seconds · HUD, UI, accessibility · budgets · gauntlet and audit · when to stop
- Phase 10: platform research · ship gates · what to find out about the platform · platform types ·
  store materials · credits · versions and patch notes · publishing · final report ·
  retrospective

# Phase 9 — Polish

The goal is not to "beat AAA", but to bring the game to a level the user will call
"good enough". The bar is external (references), but finite.

## Polish round

1. **Facet** — where the gap is biggest: per the user's words, otherwise per your
   comparison. Don't linger on `visual`: it's the easiest to capture and the most pleasant to
   improve, so polish drifts there and stays there.
2. **"Before" capture** with a frozen scenario (angle, input, seed — don't change them between rounds,
   otherwise an improvement can't be told apart from reframing) → `.studioigor/captures/polish/<facet>/NN-before.png`.
3. **Comparison** with the bar and with the previous round. **One** gap as an observable
   difference: "the bar has X, we have Y". "Looks cheap" is not a gap.
4. **One change.** Everything else you noticed — a line in BACKLOG `[P9][<facet>]`.
5. **"After" capture** with the same scenario; `studio.py commit "polish <facet>: <gap>"`.
6. Once every 3–5 rounds — a board for the user: options "before" (the first round), "after",
   "bar"; `board.py build`, then `serve --open --until-feedback` in the background.

## Facets: the bar and a professional's eye

Before a round, read only your facet's row and look through its owner's eyes: what they
see first, what they don't forgive, by what sign they spot an amateur within two seconds.

| facet — who's looking | bar | a professional's eye |
|---|---|---|
| **play** — game designer | 30–60 s of the reference doing the same activity, a storyboard at the same interval | First looks for a player decision that meant something. Doesn't forgive flat pressure and progress that happens by itself. Amateur: 30 seconds of the same verbs at the same intensity. |
| **feel** — feel specialist | a number: frames from press to reaction (the references have 2–4, < 100 ms) | First counts the responses to the key action and how fast the first one comes. Doesn't forgive speed that steps instead of accelerating. An amateur gives an arpeggio response (hit, flash, sound one after another), a pro — a chord within the same 2–3 frames. |
| **ux** — UX designer | the reference's flow screen by screen: presses to gameplay, what it explains and when | First checks whether the next action is the most visible thing on the screen. Doesn't forgive dead ends, a tutorial instead of the first attempt, state that lives only in the player's memory. Amateur: everything at one volume. |
| **audio** — sound director | a clip of the reference and a count: distinct SFX per 30 s, whether the music reacts to state | First writes a list of actions that are silent for us and audible in the bar. Doesn't forgive one sound for everything and mush in the midrange. An amateur fills every second; a pro leaves silence, and the loud lands. |
| **visual** — art director | references in the same frame + ART_BIBLE.md: the stack's ceiling and signature techniques, not "roughly like the screenshot" | Looks at the silhouette at 128 px, values without color, material under light, signature techniques, layer density (light, post, particles, background, camera). Doesn't forgive default lighting and post tuned down to invisibility. An amateur lights everything evenly. |
| **perf** — performance analyst | the budgets below; `fps_min` and the frame time curve, not the average | First looks for the worst moment and checks whether it coincided with something important for the design (boss, swarm, level start). Amateur: spikes in a rhythm — the garbage collector or per-frame allocations. |
| **meta** — progression designer | the reference's meta inventory: upgrades, tiers, time to "everything unlocked", what persists | First asks whether the player can say without a hint what they're working toward. Doesn't forgive rewards that don't change the next run. Amateur: +10% per level forever; a pro has breakthrough points where something new becomes possible. |

Feel is poorly checked from frames: for `feel` the final judge is the user.

## Typical numbers, if the reference can't be measured

| genre | to the first action | one cycle | failure → retry | distinct SFX per 30 s |
|---|---|---|---|---|
| arcade racing | < 20 s | a race of 60–180 s | < 3 s | 10–15 |
| platformer | < 15 s | a level of 45–120 s | < 2 s | 8–12 |
| survival, crafting | < 45 s | 5–10 min | soft failure, waves | 10–14 |
| roguelike, arena | < 20 s | a run of 3–8 min | < 5 s | 12–18 |
| tower defense | < 30 s | a set of waves of 2–5 min | replay the wave | 8–12 |
| idle, management | < 10 s | a decision of 30–90 s | stagnation = failure | 6–10 |

It's better to measure the reference from video frames (`refs.py youtube <url> --frames N`): first
action, failure, peak; per 30 s — verbs, state changes, sounds; frames to response.

## Juice checklist

Check ours and the bar's side by side — the gap becomes a number. On the main action first.

- [ ] hit-stop: a 2–6 frame freeze on a significant hit
- [ ] screen shake with rotation, scaled to the event, never constant
- [ ] flash: the target flashes on hit; on big events — a screen tint ≤ 10% for 1 frame
- [ ] particles on hit, movement (dust, trail), destruction, pickup
- [ ] squash & stretch or scale-punch on the acting object
- [ ] easing on everything that moves in the UI and camera: nothing linear
- [ ] sound within the same 2–3 frames as everything else
- [ ] feedback at the input source: gamepad or phone vibration, visual recoil
- [ ] slow motion or zoom at the climax — rarely
- [ ] idle motion: nothing on screen stands dead

The eleventh line is **restraint**: ten effects at full blast are noise. A good
bar has "everything there, and all of it quieter than you'd expect". Shake and flashes get a slider in the settings.

## Sound event log

Listening to a mix is awkward, counting is easy. In a dev build, the single SFX playback point
writes a line `t, event, sound` (web — into `window.__metrics`, engines — into a file next to
metrics.json). Run a 60-second scenario and compare:
- player and UI actions against what sounded → silent actions; distinct SFX per 30 s — against the bar;
- a sound more often than 3 times a minute — 3+ variations or random pitch; SFX — in the action's frame;
- priority: damage to the player → player actions → enemies → UI → ambience; a hit on the player
  ducks everything else by ~3 dB for ~200 ms; the music changes with state.

Music — around −14 LUFS integrated, peaks up to −1 dBTP:
`ffmpeg -hide_banner -i assets/music/theme.ogg -af ebur128=peak=true -f null - 2>&1 | grep -E '^ +(I|Peak):'`.

## The first 60 seconds

Everything seems clear to the one who made it, so you need a capture, not an opinion.
1. **Cold start**: delete the save and settings (web — incognito), launch with one
   command, a frame every 2 s for the first 60–90 s. Read it as a stranger: presses to gameplay,
   when the first meaningful action happens (target — in the genre table), where it's unclear where to look.
2. **The user** already knows the game: have them let someone who hasn't seen it play, silently
   (or play it themselves from a clean save). Questions: "What is the game about?", "What does it mean
   to win right now?", "What would you come back for?".
3. The menu and the first 60 seconds are a critical part: with a clear gap — gauntlet.

## HUD, UI and basic accessibility

**HUD.** An element earns its place if the player decides by it right now. Information
is: always / situational / on request / hidden (conveyed by the world or sound).
At 1080p: up to 8 elements, up to 12% of the screen in calm play and 22% in combat, the central 40%
free, text from 18 px, icons from 40 px; notifications of one type within 500 ms merge,
≤ 3 visible, critical ones skip the queue.

**UI.** hover 80 ms ease-out · press 60 ms · screen change 250 ms · modal 200/150 ms ·
tooltip after 300–400 ms. A screen has "loading / empty / data / error" states
and a way back. Touch targets from 44 px. The UI reads state and sends events, but doesn't store it.

**Accessibility.** The basic level — always; the standard level — if the platform or genre expects it.

| basic (always) | standard |
|---|---|
| music, effects and voice volume separately; pause at any moment | fully remappable controls |
| text at 1080p: menu 24 px, subtitles 32 px, HUD 20 px; subtitle contrast 7:1 | colorblind modes |
| up to 3 flashes per second; a shake and flash slider | reaction time multiplier 0.5–3× |
| color is not the only carrier of meaning; holding can be replaced with toggling | a required action doesn't disappear faster than 5 s |

## Performance budgets

Measure the **worst moment**: 60 on average with 20 at the minimum is a broken game. Budgets go in
TECH.md; the web columns come from web game practice, PC and native are guidelines, adjust them for the project.

| metric | web desktop | web mobile | PC | mobile native |
|---|---|---|---|---|
| fps at the worst moment | 60 | 30 | 60 on the min. target machine | 30, target 60 |
| frame time p95 | < 20 ms | < 37 ms | < 20 ms | < 37 ms |
| memory after 30 min | JS heap < 250 MB, flat | < 150 MB, flat | flat, ceiling in TECH.md | assets < 512 MB, flat |
| draw calls per frame | < 200 | < 100 | < 2000 | < 500 |
| cold load → gameplay | < 5 s | < 8 s | to the menu < 10 s | < 10 s |
| download size | < 50 MB | < 25 MB | no hard limit | store limit — from research |

Loading an asset mid-game — up to 500 ms. Handheld PC: 1280×800, a stable 30 fps —
a guideline (not verified). Memory growth after returning to the menu is a leak; spikes in a rhythm are
per-frame allocations (`code.md`). Measure with the engine's profiler and `fps_min` from the capture's metrics.

## Gauntlet and audit

A normal round is almost always enough. Gauntlet (`references/gauntlet.md`: blind A/B
against the bar via `scripts/ab.py` and `scripts/reveal.py`, 3–6 mini-rounds) — only
if the user is not impressed ("not it", "cheap", a second rejection in a row) or it's a critical
part (core mechanic feel, key frame, hero asset, the first 60 seconds and the menu, capsule
or trailer) and the capture shows a clear gap. If it's still not it after that, offer in one
`AskUserQuestion`:
- **long autonomous refinement of the facet** with the same procedure in a loop — only with the
  user's consent; then a merge and a playtest;
- **a fresh-eyes audit** — the art-director or qa-tester role from `team.md` with a plan
  (retention, UI, visuals), when "something's off" but the gap can't be articulated, or players drop off.

## When to stop

The user stops it, not the bar. Once every 3–5 rounds, together with the "before /
after" board, ask: "Keep polishing: <next gap>" / "Good enough, on to release".
Recommend "good enough" when the game-ness checklist and juice on the main action are passed,
the first 60 seconds go without explanations, and the budgets hold. Then `decide "polish is good
enough" --by user`, check off the gates, gaps — into BACKLOG "Later" and into the report.

# Phase 10 — Release

Everything before this made the game good, release makes it robust: the mistakes here only show up
on someone else's machine, on the second evening or in the first 30 seconds.

## Platform research — first

The user chooses the platform (phase 3, `PLATFORMS` in TECH.md). Platform requirements
change, so they aren't listed here — for each chosen platform the procedure is the same:

1. **Research** — `research/release-<platform>.md` (60–80 lines): date, links to the
   platform's official docs (the primary source, not retellings), items per the "What to
   find out about the platform" template below, "what this changes in the plan". Unverified — "(not verified)".
2. **Checklist** — every hard requirement from the research becomes a line
   `- [ ] <requirement> — <how to check>` in the same file; recommendations — as a separate list.
3. **Gates** — the release candidate passes every line: by a command, a capture or by eye with
   evidence; a line that doesn't pass is BLOCKED with a reason, not a quiet skip.

Steps with waiting (account verification, a mandatory period from payment or the store page to
release, a closed test with testers) — raise them as early as phases 8–9, otherwise they'll become the
longest stage.

## Ship gates

### Placeholders and debug

Only what was intended goes into the build: remove every match or hide it behind a debug check.

```bash
P='lorem|placeholder|TODO|FIXME|XXX|test123|asdf|dummy|cheat|godmode|noclip'
grep -rniE "$P" --include='*.[jt]s' --include='*.html' --include='*.css' --include='*.json' src/ public/   # web
grep -rnE 'console\.(log|debug|warn)|debugger' src/ | grep -vE ':\s*//'                                  # web
grep -rniE "$P" --exclude-dir=.godot --exclude-dir=addons --include='*.gd' --include='*.tscn' --include='*.tres' .  # Godot
grep -rnE '^\s*(print|print_debug|breakpoint)\b' --exclude-dir=.godot --exclude-dir=addons --include='*.gd' .      # Godot
grep -rniE "$P" --include='*.cs' --include='*.json' Assets/                                                # Unity
grep -rn 'Debug\.Log' --include='*.cs' Assets/   # Unity: keep only under #if UNITY_EDITOR || DEVELOPMENT_BUILD
```

The build is a release build: Godot `--export-release`, Unity without Development Build, web —
a production bundle. By eye (grep won't catch it): grey cubes, a debug camera, god mode, level
skip, an FPS counter, default names ("Player"), `alert()`, a test save as
the initial state. All of this is usually in the menu and the first level — they were looked at least often.

### Soak session

A run for the target session length (30 min — several hours) with a bot or a looped capture,
measurements at T+0/15/30/45/60. It catches what isn't in a 30-second storyboard.

| what to watch | failure | threshold |
|---|---|---|
| memory | grows and doesn't come back after a scene change | > 20% over T+0 after unloading the scene |
| frame time | fps drifts down | p95 grows from point to point |
| state accumulation | breaks after N repetitions: inventory, counter, AI, list | any case |
| content exhaustion | everything has been seen, but the loop keeps asking for more | per the contract and the capture |
| fun fatigue | what's great at minute 2 is tiring by minute 40 | the user's answer |

Thresholds are relative to T+0 of the same session; a short soak doesn't give a "pass". The last two rows are for
the user: a normal evening session and the question of where it got boring.

### Saves, response, first launch

**Saves** (broken ones hit the most loyal players hardest): load a save from the oldest
live build (tag `slice` and others) in the release candidate and play a full cycle. For
every schema version — a migration function (`code.md`); a test is justified here.

**Response.** Every action responds with **sound** and **motion**: a silent one reads as
broken. Most often forgotten: menu navigation, an invalid action, damage, pickup,
saving, an error, goal completed, failure, level start and end. Then the mix: nothing
hurts the ears, gets lost, or fights with the music.

- [ ] starts with one command or click on a clean machine, without a save or unlocks
- [ ] reaches the main action without explanations, within the genre's target
- [ ] every screen has an exit; a failure is visible and explains what happened
- [ ] state survives a reload; no path goes "silent" instead of showing an error
- [ ] web: sound after the first gesture (otherwise the browser silently blocks it), touch, no external requests

## What to find out about the platform

The `research/release-<platform>.md` template. An empty item means "not found out", not "no
requirements".

| item | what to find out |
|---|---|
| size and format | build limit (initial download, total, compressed or uncompressed), package format (a zip with `index.html`, exe/app, AAB/IPA…), limits on the number of files and names, browsers and OSes |
| SDK and integration | whether the platform's SDK is mandatory, how it's connected, a stub for local runs; achievements, leaderboards, cloud |
| lifecycle events | the "loaded and playable" signal, gameplay start and stop, pause and silence during ads and on focus loss, return |
| monetization and ads | models (paid, ads, purchases), where ads are allowed, reward only after viewing, the platform's share |
| input | touch, keyboard (any layout — `event.code`), mouse, gamepad and glyphs; screen rotation, on-screen keyboard |
| language | required languages for the game and the store page, how the platform reports the player's language |
| saves | local, cloud or through the platform's account; survive a reload and an update |
| store page materials | icon, cover and capsules, screenshots, texts (title, descriptions, "how to play"), trailer — sizes, formats, languages |
| account and money | registration, fees, identity verification, bank and taxes, waiting periods |
| moderation | what's checked, how long it takes, typical rejection reasons |
| rating and legal | age rating, privacy and data collection, export control, agreements |
| what a human does | accounts, payment, 2FA, agreements, the "publish" button |
| upload | CLI or web form, API keys, draft, rollback to a previous build |

## Platform types

What's almost always true for the type; specific numbers — only from research.
- **Web portal** (the game in an iframe on someone else's page): a small initial download, the platform's
  SDK, pausing the game and sound during ads and on focus loss, no external requests or links,
  relative paths, touch and keyboard, localStorage may be unavailable (incognito) —
  in a try/catch.
- **Your own site or an indie game storefront** (a zip with `index.html` or a downloadable build): release the
  same day and a playtest channel; with several platforms — a convenient first step.
- **PC store**: a developer account and a fee, a mandatory period before release, a "coming
  soon" page in advance, review of the page and the build; a build for each OS (macOS — signing and
  notarization); gamepad and handheld PCs — per the platform's requirements.
- **Mobile store**: an account with identity verification, signing (keys — back them up and keep them out of git:
  without them you can't ship an update), the package format and target SDK/API — from research, some
  stores require a closed test before production, privacy forms, age rating.
- **Console** — not a first target: platform holder approval (often an NDA and a pitch), devkits,
  certification, usually through a publisher or a porting studio; only research and an honest plan.

Builds by stack: Godot — an export preset for each OS (a Mac builds Windows and Linux),
Unity — `unity build` with the modules from phase 4 (from a Mac, Windows is Mono only), Unreal —
a Windows build only on a Windows PC, a web stack — a production bundle (desktop — via
Electron/Tauri, mobile — via Capacitor).

## Store materials

- **Screenshots** — real captures of the best moments, not generated: the storefront promises what
  the game actually has. Capsule and screenshot sizes — from the platform's current docs (they change).
- **Capsules, icon, cover** — a composition from real captures, ART_BIBLE.md and the logo
  (Blender/engine/`magick`); an image generation tool, if available, is an addition on top,
  marked "generated". They read as a thumbnail, hook immediately, match the game's style. This is
  a critical part: with a gap to the capsules of strong games in the genre — gauntlet.
- **Trailer** — cut gameplay clips (Godot `--write-movie`, Playwright `recordVideo`,
  Unity Recorder) and edit them with `ffmpeg` or any video editor; voice-over — any
  available TTS or text only. A hook in the first 3 seconds, the logo and a call to action at the end.
  The set and sizes of materials — from the "store page materials" item in the platform research.

## Credits

Built from the ASSETS.md license registry, not from memory: every line that requires
attribution (CC-BY and similar) → author, title, license, link on the credits screen and in
`CREDITS.md` next to the build (CC0 — optional, but it's good form). Fonts (OFL and others) —
the license text goes into the build. Godot requires the text of its MIT license and the licenses of third-party
components (the "Complying with licenses" doc); other engines' terms — into the research.
Cross-check: everything third-party in the assets is in the registry; a line without a file in the build doesn't go into the credits.

## Versions, patch notes, hotfix

- Version and tag: `studio.py commit "release 1.0.0" --tag v1.0.0`; the version — in the build name and in the menu.
- **Patch notes** — for players: "New / Changed / Fixed", balance as "before →
  after". Every line comes from a commit that made it into the build (`git log v1.0.0..HEAD
  --oneline`). Don't make things up: a note about a save fix in a game without saves is a
  real failure of such pipelines.
- **Hotfix**: the user approves before any code; the change is minimal; the rollback plan comes first
  (the previous build is kept: a zip, a build id or a version on the platform); check it on the
  release build, not in the editor; then the change goes into the main branch.

## Publishing — only by the user's decision

Prepare everything yourself: builds, store pages, materials, upload scripts. Uploading, submitting for
review and making it public — only after an explicit answer in `AskUserQuestion`: per
platform and separately "draft" and "make public". Money, accounts, logins, 2FA codes,
agreements — the user does these themselves, you guide them step by step. `git push` — only on request.

## Final report

It starts with what was **not** done: a report of total victory usually means the bar
was low. Source: `grep -nE 'SKIP:|BLOCKED:' .studioigor/{PIPELINE,SCOPE}.md` and `scope.py .`.

```
## <game> <version> — <date>
### Not done
- BLOCKED: <gate or contract line> — <why>
- SKIP: <…> — <why>
### Shipped
- <platform>: <build or link>, <size>, <draft | in review | published>
- scope: <N of M contract lines>, content units, hours of play
### Open gaps
- <facet>: the bar has X, we have Y
### Next
- human steps and waiting periods, BACKLOG "Later"
```

## Retrospective → lessons for the skill

At release or when the project is paused — a short review, line by line: what worked (**why**, **how to
repeat it**), what went badly (**root cause**, **how to prevent it**), where we got
**lucky** (hidden risks). Pick the 1–3 main lessons. Candidates: a platform fact
that research found different from what the skill says; ship gates that caught a real bug; the facet
that ate the most rounds, and what worked. When to ask about saving — in SKILL.md.

```bash
python3 <skill>/scripts/learn.py propose --phase all --kind process \
  --title "…" --what "…" --when "…" --why "…" --source "retro <game> <version>"
```
