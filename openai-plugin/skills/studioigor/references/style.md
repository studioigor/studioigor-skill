# Phase 2 — Style

Read in phase 2 and on "let's go back to the style". Here: how to come up with directions,
collect real references (`refs.py`), show the board, run rounds from feedback and write
ART_BIBLE.md. The overall phase order and the rules for questions are in SKILL.md, the gates in
PIPELINE.md.

**Contents:** 1 Input and output · 2 Directions · 3 The stack ceiling · 4 Which source for
what · 5 refs.py commands · 6 Parallel hunters · 7 Generated concepts · 8 Board
and feedback · 9 Rounds and locking · 10 ART_BIBLE.md · 11 Anti-generic · 12 Copyright ·
13 Gauntlet and phase 5 · 14 learn.py · 15 Typical failures

## 1. Input and output

Input — CONCEPT.md: genre, reference games, fantasy, tone, camera, platforms. The engine has
not been chosen yet (phase 3), so for each direction write which class of stack it requires.
The chosen style becomes the input for `stack.md`.

Output: `refs/<set>/` with images and `sources.json`, boards `boards/style-r1…`,
a filled-in ART_BIBLE.md, a `--by user` decision and a commit.

Rounds: R1 directions → R2 variations within the chosen one → R3 game-screen frames in this
style → lock. 2–3 are usually enough. Ask nothing before the first board: directions
are derived from the concept, the user chooses on the board. Paths below are from the game root,
`SK=<skill>/scripts` (the scripts folder; in other references `$S` is studio.py).

## 2. Directions: 3–5 with an opinion

Make 4 by default. Three are mandatory:
- **close to the references** — what the user named ("like Hades"), but with a twist;
- **bold** — one axis pushed to the limit: monochrome plus one color, enormous scale,
  a grotesque silhouette;
- **stolen from another medium** — a film, an album cover, architecture, a poster,
  risograph, engraving, ukiyo-e, a school of animation.

The fourth is whichever best serves the main pillar, or the cheapest strong option for
our production.

Direction card, each field is one line:
- **An opinionated name:** "neon noir in the rain", "sun-bleached Soviet seaside", "a blueprint
  come to life". Test: an artist can paint a key frame from the phrase alone and land
  close. "Stylized and colorful" fits any mobile game — that is not a name.
- **A visual rule** that settles any argument: "danger glows, everything else is
  desaturated", "everything moves", "beauty in decay".
- **Mood** — a precise emotion and the character of the light: warm or cold, contrast, time
  of day. "Gloomy" won't do.
- **Shape** — what silhouettes are made of (long horizontals, chunky slabs, thin verticals,
  soft blobs) and what is deliberately absent.
- **Color** — the palette direction and what the reserved accent means.
- **Can we pull it off:** do the player, enemies and pickups read at game scale; the mobile
  or browser budget; the required stack class (section 3); is it within the pipeline's reach
  (stylized Blender, procedural 2D, image generation). Photorealism = Tripo, Meshy or
  paid packs — that is a cost, write it in the cons.

Write the card into the set before the hunt — the user will see it on the board:

```bash
python3 $SK/refs.py meta .studioigor/refs/neon-noir --title "Neon noir in the rain" \
  --text "Rule: every light source appears twice — in the air and in the wet floor. Mood: loneliness in a big city, cold key light and warm signs. Shape: tall narrow verticals, no rounded corners. Color: blue-black base, pink accent = danger." \
  --tags "3D,night,needs post-processing" --pros "recognizable from one frame; bloom + reflections are cheap" \
  --cons "dark image on a phone in daylight; Canvas 2D can't pull it off"
```

Directions must differ in rule, light and shape. If only the palette differs, they are
variations of one direction — they belong in R2.

## 3. The stack ceiling: a catalog of techniques

The visual bar is the stack's ceiling, not "decent". Signature techniques come from here. A
technique that fights the direction is a minus: bloom on flat graphics, grain on clean
vector art. The order for raising the look (also in phase 5 look-dev): palette and light →
post-processing → the dominant technique at full strength → motion in the frame → asset
materials and silhouettes.

- **Three.js / WebGL:** post-processing (`postprocessing` by pmndrs or `EffectComposer`):
  selective bloom, vignette, grain, LUT, SSAO/N8AO, DoF, god rays. Light: 2–3
  authored sources (warm key, cold fill), emissive + bloom, `FogExp2`, env
  map via PMREM. Shaders where they show: fresnel rim on the player, dissolve, water.
  Instancing, GPU particles, speed-driven FOV, camera roll.
- **Canvas 2D / Phaser:** parallax of 3+ layers, one in front of the action. Light without
  sources: `lighter` and `multiply` with punched-out circles. Phaser: Light2D with normal maps,
  preFX/postFX (glow, bloom, vignette, pixelate). Juice: shake with rotation, hit-stop,
  a 5–10% flash, palette shift by state, trails. 4–6 colors is already a style.
- **Godot 4:** WorldEnvironment (glow with an HDR threshold, SSAO, SSIL, SDFGI/VoxelGI, volumetric
  fog, SSR, AgX, LUT), GPUParticles with trails, decals, `.gdshader` (dissolve,
  outline, wind, toon). 2D: CanvasModulate + PointLight2D + LightOccluder2D. Web export
  is Compatibility: no SSAO, SSIL, SDFGI or volumetric fog.
- **Unity URP:** Volume (Bloom, Tonemapping, Color Lookup, Vignette, Film Grain, DoF),
  Renderer Features for SSAO, outlines, pixelation. Decal Projector, Adaptive Probe
  Volumes, Shader Graph, VFX Graph (not WebGL), 2D Renderer with lights. Setup — a Global
  Volume with a profile and Post Processing on the camera, features in URP Renderer Data.
- **Unreal 5:** Lumen, Nanite, Virtual Shadow Maps, Height Fog + volumetric fog, Post
  Process Volume, Niagara. Stylization via a post-process material. Not on the web; on mobile
  Lumen is turned off.

## 4. Which source for what

| what to show | source | command |
|---|---|---|
| how it looks in a real game: camera, HUD, readability, the genre bar | Steam screenshots of reference games | `steam` |
| motion, pacing, effects, the camera in action | YouTube gameplay frames, Steam trailer | `youtube`, `steam --trailer` |
| mood, concept art, stylization | Are.na channels, ArtStation | `arena`, `artstation` |
| another medium: architecture, painting, posters, photos, museums, costume | Wikimedia Commons, Openverse | `wikimedia`, `openverse` |
| a find from WebSearch/WebFetch: a film still, a cover | direct URL or a page with og:image | `urls` |
| a pixel palette | Lospec | `lospec` |

Per direction — 6–10 images: 2–4 game screenshots, 1–2 motion frames (if motion is the
essence of the style), 2–3 for mood, 1–3 from another medium. Each direction has its own games:
one game in every set erases the difference.

Queries are in English. Steam: title or appid. Wikimedia and Openverse: concrete
nouns ("brutalist housing estate"), abstractions return junk. Are.na: aesthetic
words ("liminal space", "risograph"), download a good channel whole by slug. YouTube:
"<game> gameplay no commentary", the right moment — `--at`.

**Curation is mandatory.** Open every image (Read). Junk — off-topic, watermarks,
all-UI, a repeated mood — remove with `drop`. For each remaining one write a
`note`: what we take. "Rim light separates the hero from the background", not "pretty". The note
is the caption on the board: it is how the user understands why the image is there.

**Limitations.** Pinterest, Behance, DuckDuckGo are unavailable without login: pins from the
user go as direct image URLs into `urls`. ArtStation returns square covers of ~600
px and may be closed off by Cloudflare — the script will suggest a replacement itself. Openverse
without a key: 20 requests per minute and 200 per day, the script keeps a shared limit per machine
(including for subagents); when it runs out, use Wikimedia or Are.na.

## 5. refs.py commands

Every command appends to `<set>/sources.json`. Duplicates by sha1 and URL are filtered out,
non-images are skipped, everything is downscaled to 1600 px, a summary is printed at the end.

```bash
R="python3 $SK/refs.py"; D=.studioigor/refs/neon-noir
$R steam "Cyberpunk 2077" --out $D --n 4 --trailer 2   # screenshots + 2 trailer frames
$R youtube "ruiner gameplay no commentary" --out $D --frames 3   # or a URL/id and --at 1:20,4:05
$R arena "neon noir" --out $D --n 3        # searches channels, prints the slug; `arena <slug>` — the whole channel
$R artstation "neon noir city concept" --out $D --n 3
$R wikimedia "Hong Kong neon signs night" --out $D --n 2   # openverse … [--license-type commercial]
$R urls found.txt --out $D        # lines: URL | page | credit | license | what we take; "-" = stdin
$R add $D /tmp/concept1.png --generated --prompt "…" --note "concept: …"
$R note $D steam-1a2b "wet asphalt doubles every sign"   # file or prefix
$R drop $D arena-9f8e openverse-77aa   # remove; won't be downloaded again
$R meta $D --title … --text … --tags "3D,night" --pros "a; b" --cons "c" [--palette "#0b0f1a,#ff2e88"]
$R palette $D --n 6                    # palette from the set's images (ImageMagick)
$R palette $D --liked .studioigor/boards/style-r1/feedback.json   # likes only, from any sets
$R lospec endesga-32 --out .studioigor/refs/pixel-crisp
```

`palette` sorts colors by share; the last one is an accent candidate (a rare saturated color
that quantization would otherwise swallow). Names in Latin characters: R1 sets
`refs/<direction>/`, R2 `refs/<direction>-<variant>/`, R3 `refs/<direction>-frames/`; boards
`boards/style-r1…r3`.

## 6. Parallel hunters (subagents)

Hand the hunt out to subagents: one per direction, no more than three at a time.
The main benefit is context: viewing 40 images costs tens of thousands of tokens, let the
subagent spend them. No worktree needed: each writes only to its own `refs/<set>/`. First
write the cards yourself (`meta`), then all Agent calls in a single message
(`subagent_type: general-purpose`, no `isolation`). After they return, check each
`sources.json`: 6+ images, a note on every one. Prompt:

```
You are a reference hunter for the direction "<name>" of the game "<title>" (<genre>, <camera>).
Rule: <one line>. Mood: … Shape: … Color: …
Reference games for this direction: <2–3>. Other medium: <what we steal>.
Work ONLY through python3 <skill>/scripts/refs.py <command> … --out <abs.path>/.studioigor/refs/<set>
You need 8–10 images: 3 game screenshots (steam), 1–2 motion frames (youtube or steam --trailer),
2–3 for mood (arena, artstation), 2 from another medium (wikimedia, openverse; or find them
via WebSearch and download with the urls command). Open every image (Read) and look at it.
Remove junk with refs.py drop. For each remaining one — refs.py note: what we take (light, silhouette,
material, composition), in one line. Do not generate images, do not touch other files, do not commit,
do not ask questions. Return 3 lines: what you found, what was missing, the 2 best files.
```

## 7. Generated concepts

Requires an image generation tool, if there is one in the environment (optional: without it
this section is skipped). Concepts supplement real references, never replace them.
A real image honestly shows how the game will look; generation flatters and hides the cost of
production.

1–2 per direction: in R1 — only where real images are scarce (usually for the "stolen" one),
in R3 — the main material. Generate into a scratch folder, then
`refs.py add <set> <file> --generated --prompt "…" --note "<what we are checking>"` — the board
will show a "generated" badge.

Build the prompt from the card and the likes, not from adjectives: (1) the game frame — genre,
camera (angle, height, FOV), moment, with or without HUD; (2) the direction name and rule
verbatim; (3) light — source, key and fill color, shadows, fog; (4) the hex palette with roles,
accent only on <meaning>; (5) silhouette shape and what is absent; (6) signature techniques, the
dominant one large; (7) elements of the liked references in words ("rim light, like on wet
asphalt at night"), not "make it like image X" — we don't copy other people's work; (8) negative:
the "Forbidden" lines, "no text and no watermarks", "no photorealism" if the style isn't that.

## 8. Board and feedback

```bash
python3 $SK/board.py from-refs --out .studioigor/boards/style-r1 --title "Style — round 1" \
  --subtitle "<game>: 4 directions" --question "Which direction is closer? Like images and write what to take" \
  .studioigor/refs/neon-noir .studioigor/refs/soviet-seaside .studioigor/refs/blueprint …
python3 $SK/board.py serve .studioigor/boards/style-r1 --open --until-feedback
```

Run `serve` via Bash with `run_in_background: true` and say one line: "Opened the
board in the browser: pick a direction, mark images "Like" / "Not it", write what to
take, and press "Send"". Wait for the notification, do not poll and do not do anything that
depends on the choice. On "Send" the process exits and prints the feedback (in full —
`feedback.json`, field `latest`). If the user answered in chat — accept it and stop the server
(TaskStop). For R2, where a mix is possible, — `--mode multi`.

How to read the feedback:
- **selected** — the direction choice. If missing — look at where there are more likes.
- **Likes** — look for a common trait, not a common theme: light, palette, angle, material,
  density. Write the hypothesis in one line: "likes: rim light, warm base,
  close-up".
- **Dislikes** — what they have in common becomes a candidate for "Forbidden".
- **Comments** — verbatim into `--why`.
- **Likes across different directions** — R2 needs a mixed variant.

```bash
python3 $SK/studio.py decide "style R1: chose 'Neon noir', taking the sun-bleached palette from 'Seaside'" \
  --by user --why "<comment verbatim>; likes: rim light, wet floor"
python3 $SK/studio.py commit "style: round 1"
```

## 9. Rounds and locking

- **R1 — directions.** 3–5 sets of real references, 0–1 concept per direction.
- **R2 — variations within the chosen one.** 3–4 variants, each changes one group of axes:
  palette (warm, cold, limited), light (time of day, hardness, fog),
  camera (angle, distance, FOV), detail (flat, textured, painterly). A variant has
  4–6 images: R1 likes plus new targeted ones. Palette — via `refs.py palette`, optionally
  one concept. If R1 likes were spread across directions, add a mix.
- **R3 — the game screen in this style.** 2–3 concept frames of a real gameplay moment from
  the gameplay camera: hero, enemy or pickup, HUD. Next to them 2–3 anchor references. Check
  readability: squint or shrink to 25% — the player, the threat and the goal must read.

**Locking** — one `AskUserQuestion`, header "Style": "Lock it (Recommended)" →
ART_BIBLE; "One more round" (the description says which axis we turn); "Mix …" specifically
("light from 'Neon' + palette from 'Seaside'"). "Other" is added automatically.

**When to stop.** Usually after 2–3 rounds. If after R1 the comment is clear and the choice
strong, offer locking right away: R2 and R3 are optional. No convergence by the fourth
round — the problem is not the images: ask one thing, which feeling or pillar the game's look
carries, or offer "you decide". In autonomous mode build the board for the record, but do not
wait: take the direction with the strongest support in the concept, `decide --by agent`.

## 10. ART_BIBLE.md

Fill in the template as lines. The goal is that assets and look-dev can be made from it without
additional explanations.

- **Direction** — the name and the rule.
- **What we steal from** — the medium and what exactly: "from Rodchenko posters — the diagonal
  and two colors", not "constructivism".
- **Palette:**
  `refs.py palette .studioigor/refs/<final> --liked .studioigor/boards/style-rN/feedback.json --n 6`,
  then the roles by hand: dominant, secondary, two supporting, a **reserved accent** with
  a single meaning (danger, interactive or reward — nowhere else), forbidden colors.
  The player contrasts with the background; the accent is not the only signal — shape or an icon
  goes with it (color blindness).
- **Light** — source and color, key and fill temperature, shadow hardness, fog, post
  (tonemapping, bloom threshold, grade). Light is 80% of the look.
- **Shape and materials** — silhouettes and prohibitions; surfaces (flat, toon, PBR,
  painterly); texel density or pixel size.
- **Camera and composition** — angle, FOV, distance, movement.
- **UI** — style, specific fonts, icons, no emoji.
- **Signature techniques, ≥3.** Taken from the catalog in section 3 and visible on a static
  screenshot. The first is the dominant one at full strength, the rest support it. "Wet
  asphalt doubles every light source" is a technique; "atmospheric lighting" is not. The last
  line: "Requires from the stack: …" (post-processing, volumetric fog, normal maps in 2D) — phase 3
  will take it into account.
- **Forbidden** — 3–5 lines, mostly from the dislikes on the boards.
- **References** — paths of the sets and boards, 3–5 key images in the format "file — take X,
  avoid Y". The references complement each other, no two pull in the same direction. Mark 1–3 of
  them "look-dev bar" (section 13).

Run the anti-generic check (section 11), then:
```bash
python3 $SK/studio.py decide "style locked: '<name>'" --by user --why "<answer>"
python3 $SK/studio.py tick "user locked the style"
python3 $SK/studio.py tick --phase 2 "art bible"
python3 $SK/studio.py commit "style: art bible"
```

## 11. Anti-generic check

Run it on the finished art bible before the commit:
- Could it be attached to any decent game of the genre without anyone noticing? Then
  nothing in it has been chosen. Rewrite until at least one line makes the producer
  nervous.
- Can an artist paint a frame close to the board from this document alone?
- Is there one dominant at 100%? Ten effects at 10% each are mush, not a style.
- Are the three techniques visible on a static screenshot, or are they adjectives? Is there a
  reserved accent and forbidden colors?
- Are there empty words without a technique: "stylish", "atmospheric", "colorful", "epic", "cozy"?

A bold direction done timidly looks like a mistake; the same at full strength looks like intent.
When in doubt, push the slider further. Polish will roll it back, with evidence.

## 12. Copyright

References are a private moodboard, almost everything in it belongs to someone else. We do not
put it into the build and do not publish it (store, trailer, website). Images in
`.studioigor/refs/` are in .gitignore (`studio.py init`), `sources.json` with the sources is in
git. We do not trace over them and do not give them to a generator as "make exactly this" — we
describe the elements in words. CC images from Openverse and Wikimedia are also only
references; if something becomes an asset, that is phase 5 and the ASSETS.md license registry.
If the user wants to show the board in a video, warn them that it contains other people's work
(authors are in the board captions).

## 13. Gauntlet and phase 5

Phase 2 does not need the gauntlet: the judge is the user at the board. The key frame and
look-dev are a critical part per `gauntlet.md`, but the look-dev scene is built in phase 5. The
1–3 "look-dev bar" images from ART_BIBLE are handed over there (the best liked real reference at
the gameplay angle and the R3 concept) — they become `ref/` in BAR.md if look-dev goes through
the gauntlet.

## 14. What to propose to learn.py

Propose without asking: the lead will ask about saving at the end of the phase. Reasons:
- a source or query that quickly gave strong references (an Are.na channel, a query template);
- a direction recipe or concept prompt that was locked in the first round;
- a repeated failure: concepts rejected as "AI-looking" a second time, a source consistently
  returns junk.

```bash
python3 $SK/learn.py propose --title "Are.na channels for a style moodboard" --phase 2 --kind tool \
  --what "search arena channels by aesthetic and download a whole channel by slug" \
  --when "R1, a direction from another medium" --why "8 curated on-topic images in 1 command" \
  --source "<game>, R1"
```

## 15. Typical failures

| symptom | what it really is | what to do |
|---|---|---|
| directions differ only in color | they are variations of one | separate the rule, light, shape, the source of the steal |
| a board of only generated images | no truth about how the game looks | real references first, generation as an extra |
| "stylish and colorful" | nothing has been chosen | an opinionated name, a rule, the anti-generic check |
| the user can't choose | the directions are weak or similar | R2 with a mix; ask which feeling the game's look carries |
| the platform can't handle the style | the stack wasn't considered | "Can we pull it off" in the card, "Requires from the stack" in the bible |
| empty captions on the board | not curated | a `note` on every image, junk — `drop` |
| one game in every set | the directions stuck together | each has its own games and its own medium |
| a fifth round with no convergence | looking in the wrong place | a question about the feeling or pillar, or "you decide" |
