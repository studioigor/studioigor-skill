# Assets and look-dev (phase 5; assets in phases 6–8)

Read in phase 5 and every time a new asset is needed in phases 6–8. Covers: research, inventory,
strategy (by default you make it yourself), what is needed from the user (Mixamo, Tripo), Blender and templates,
characters, 2D, VFX, audio, import per engine, budgets, the look-dev scene, licenses, parallel work.

## Contents
1. Phase 5 order · 2. Research · 3. Inventory and the card · 4. Strategy by category ·
5. Packs on the board · 6. What is needed from the user · 7. Blender: Python scripts ·
8. Stylized modeling · 9. Characters · 10. 2D, UI, VFX · 11. Sound and music ·
12. Export and import per engine · 13. Budgets · 14. Look-dev scene · 15. Licenses and credits ·
16. Parallel production · 17. Phases 6–8 and learn.py

## 1. Phase 5 order
1. Research → `.studioigor/research/assets.md` (section 2); inventory in ASSETS.md (section 3).
2. Strategy by category. By default you make everything yourself. Packs — only if they fit the style, and
   only after showing them on the board next to a trial asset of your own work (sections 4–5).
3. One `AskUserQuestion` for the strategy and everything that needs the user (section 6). Then
   `decide --by user`, `tick "strategy"`, `commit`.
4. Hero assets for look-dev: 2–3 props or pieces of environment, the main character, a HUD mockup.
5. Look-dev scene in the engine → CAPTURE → board → approval (section 14).
6. License registry (section 15) → `tick`, `commit`.

Don't produce the whole list in phase 5: this phase sets up the pipeline and the quality bar; mass
production happens for the gyms, the vertical slice and content (section 17). Things made in advance get redone.

## 2. Research
A file of up to 60–80 lines: date, links, findings, what it changes. Three questions: **packs for ART_BIBLE**
(style, license, format, how to download); **generators today** (prices, API, low-poly, rigs —
the market changes monthly); **import into the engine** (importer version, compression, collisions, animations).
Starting facts (verified 2026-09, re-check whatever you rely on):

| source | license | how the agent downloads | preview |
|---|---|---|---|
| Kenney (3D kits, 2D, UI, audio) | CC0 | direct zip: `curl -s https://kenney.nl/assets/<slug> \| grep -oE 'https://kenney\.nl/media/pages/assets/[^"]+\.zip'` | `preview.png`/`sample.png` on the page; 3D zips contain isometric PNGs |
| KayKit (stylized chunky low-poly, character rigs) | CC0 | `https://codeload.github.com/KayKit-Game-Assets/<repo>/zip/refs/heads/main` (10 repos); the rest on itch — by hand | render with `preview.py` |
| Quaternius + Universal Animation Library 1/2 (250+ clips on one humanoid rig) | CC0 | packs on Google Drive and itch (the user downloads); individual models — Poly Pizza | `quaternius.com/assets/images/fullres/<pack>.jpg` |
| Poly Pizza | CC0 or CC-BY per model | no key: page `/m/<id>` → `https://static.poly.pizza/<uuid>.glb` | `static.poly.pizza/<uuid>.jpg` |
| Poly Haven (HDRI, PBR, models) | CC0 | API without a key, but with a unique `User-Agent` | `cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=256` |
| ambientCG (PBR materials) | CC0 | `https://ambientcg.com/api/v3/assets?q=…&include=downloads,previews` | in the API response |
| OpenGameArt | mixed | HTML + direct files; take only CC0/CC-BY | on the page |
| Sketchfab | per model, mostly CC-BY | search without a key; download with the user's token | in the API response |
| itch.io, Fab, Unity Asset Store | each has its own | only the user, in the browser | — |

Generators: **Tripo** — API on prepaid credits, rig with Mixamo bone names, retargeting.
**Meshy** — API only from the Pro plan ($20/mo). **Rodin** — Business plan ($120/mo), expensive.
**Hunyuan3D 2.1 and TRELLIS.2** — locally on a Mac: slow, 400k-vertex meshes. **CSM** is dead.

## 3. Inventory and the asset card
Sources: DESIGN.md (what each mechanic has to show and make audible), STORY.md (characters,
locations), SCOPE.md (quantities: N levels → how many kit pieces), CONCEPT.md (from what
distance the camera sees the asset, hence the level of detail). Write into the `## Inventory` section of ASSETS.md.
One line per asset, and that is the card:

```
- A012 · SM_Lantern · prop/environment · wrought metal, warm glass, palette metal/glass · ≤600 tris, 16px atlas · Blender · done
```

Fields: ID · name · category · style notes (grounded in ART_BIBLE) · budget · source · status.
Statuses: `plan → wip → done → approved`, plus `cut`. Don't copy a shared asset — reference its ID.
The generation prompt and the model script are sources, not documentation: they live next to the asset in
`art/`. Don't write prose about assets.

- **Layout.** `art/` — sources (.blend, model scripts, .aseprite, .svg, prompts);
  `art/_downloads/` — pack zips (in .gitignore; only what is used goes into the repo); export for
  the engine — Godot `res://assets/`, Unity `Assets/Art/`, web `public/assets/`. Godot: an empty
  `art/.gdignore`, otherwise it imports the sources. Unity: `art/` outside `Assets/` is not imported.
- File names — ASCII without spaces, case exactly as in the code: macOS forgives a case mistake,
  a portal's web server doesn't. Spaces and Cyrillic in names break some stores/portals and loaders.

## 4. Strategy by category
By default you make it yourself. Models work well in Blender today (Python scripts, `Blender -b`), and your
own work goes straight into the art bible, needs no licenses and can be refined by script.

| category | default | alternative |
|---|---|---|
| props, environment, modular kits | Blender, a script per asset (section 8) | a pack, if it passed the style test |
| vehicles, weapons, buildings | Blender | a pack (Kenney car/city, KayKit) |
| stylized characters and creatures | Blender yourself: base mesh + rig + animations (section 9) | KayKit/Quaternius, if the style matches |
| realistic characters | Tripo/Meshy with the user's key | the user generates on the web |
| textures | procedural (Blender bake, numpy, shader); painterly — image generation, if available | realistic PBR — ambientCG/Poly Haven |
| sky and lighting | gradient or shader per the art bible; Poly Haven HDRI | — |
| 2D sprites and tiles | procedural (SVG, code), pixel art via the Aseprite CLI; painterly — image generation, if available; a unit pose sheet — generation or a Blender render with an ortho camera; 3D→2D by rendering | Kenney 2D |
| UI and icons | SVG in code → PNG, 9-slice | Kenney UI Pack, if the style matches |
| VFX | engine particles and shaders + procedural textures | — |
| SFX | jsfxr/ZzFX, Kenney audio, Openverse CC0 | Freesound (key), Sonniss |
| music | the user decides (section 11) | CC0/CC-BY |

**A 2D game** uses Blender only when the style calls for it (pre-rendered sprites, isometric tiles from
models). Otherwise procedural and image generation, if available.

**3D without Blender** (the user declined it, or it won't install): make 3D however works, still to the
art bible. Procedural meshes in engine code (Godot `SurfaceTool`/`ArrayMesh`/CSG, Three.js geometry,
Unity `Mesh` API) saved as scenes or prefabs; a GLB written from Python (a small glTF writer, or
`trimesh` in a venv) for low-poly props; a 3D generator, if the environment has one (Tripo/Meshy with
the user's key); CC0 packs that pass the style test. Previews come from the engine's CAPTURE instead of
`preview.py`.

**Style test for a pack:** shape (proportions, thickness, bevels), palette, detail density,
how it fits with the rest. Packs from different authors clash side by side, so keep one family per game.
Kenney, KayKit and Quaternius color models with one palette atlas: replace the atlas with the
ART_BIBLE palette and the pack is recolored in a minute. This is the main way to fit a pack to the style.

## 5. Packs on the board
Show packs as images, not names. Always add a "I make it myself" option with a trial
asset made in 10 minutes in the target style: the user compares what they will see in the game.

1. Previews. Kenney — `preview.png` and `sample.png` from the page; the zip has isometric PNGs, and
   the file list can be read without downloading (Python `zipfile` over HTTP Range). GLB packs
   (KayKit, Poly Pizza, your own trial) — headless render:
   ```bash
   B=/Applications/Blender.app/Contents/MacOS/Blender; T=<skill>/scripts/templates/blender
   $B -b --factory-startup -P $T/preview.py -- --glb a.glb --glb b.glb --out .studioigor/boards/packs/media --size 512
   ```
2. `board.json` in `.studioigor/boards/packs/`: option = pack, `media` — 3–6 previews, `tags` —
   license, `pros`/`cons` — match with the style. Paths are relative to the board.
3. `board.py build .studioigor/boards/packs/board.json`, then in the background
   `board.py serve .studioigor/boards/packs --open --until-feedback`.

Mixamo animations — the same way; the catalog is open without login (GIF previews in the response): header
`X-Api-Key: mixamo2`, `GET https://www.mixamo.com/api/v1/products?page=1&limit=20&type=Motion%2CMotionPack&query=walk`.

## 6. What is needed from the user
Ask in one `AskUserQuestion` together with approving the strategy. Name the price and the number of
actions right in the question, recommendation first. Example: "Asset strategy" — "I make everything myself in Blender
and procedurally (Recommended)" / "Myself + pack X for the environment" / "You decide"; "Characters" — "I stylize them
myself, animations — Quaternius UAL (Recommended; you download 1 zip, ~1 minute)" / "Animations from Mixamo (needs your
Adobe login, ~10 minutes)" / "Realistic via Tripo (~$1 per character with 5 animations, needs a key)".

**Mixamo** (free, needs an Adobe ID; bipedal humanoids only). Prepare
`art/characters/<hero>/<hero>_mixamo.fbx`: T- or A-pose, facing -Y, feet at z=0, one
joined mesh, applied scale, under ~100k polygons. Show the file in Finder
(`open -R <file>`) and give the user exactly these steps:
1. Open mixamo.com and sign in with your Adobe ID.
2. Upload Character → drag in `<hero>_mixamo.fbx`.
3. Auto-Rigger: markers on the chin, wrists, elbows, knees and groin. Skeleton LOD: "Standard"
   (with fingers) or without fingers for low-poly. Next → wait → confirm.
4. Download: FBX Binary, Pose — T-pose, Skin — With Skin. Save as `character.fbx`.
5. Animations: find <the exact list of clips for the mechanics: Idle, Walk, Run, Jump, Attack, Hit,
   Death…>. For walk, run and strafes, tick "In Place".
6. Each clip: FBX Binary, Skin — Without Skin, 30 fps. File name — `anim_<clip>.fbx`.
7. Put everything into `art/characters/<hero>/mixamo/` and type "done".

Then you take over: `bpy.ops.import_scene.fbx` (ignore leaf bones, no Apply Transform; Mixamo
is in centimeters, the armature comes in at scale 0.01) → clips as actions on one armature (bones
`mixamorig:*`) → one GLB with all clips. Name looping clips with the `-loop` suffix: Godot
will loop them.

**Tripo** (realistic or complex organic models, generation from a concept). The user:
account → platform.tripo3d.ai → API Keys → buy credits (separate from the web subscription) →
`export TRIPO_API_KEY=…` in `~/.zshrc` (not in the repository). Then you do everything via API v3:
generation (P1.0 and Smart Low-poly) → rig-check (free) → rig with the Mixamo spec (25
credits) → retarget presets (10 per clip) → GLB. Price: 1 credit = $0.01; a textured character with a rig and 5 clips — about 105 credits
(~$1.05). The no-API path — studio.tripo3d.ai in the browser (free tier: models are public,
CC BY 4.0). Meshy — the same, but API only from Pro ($20/mo). After generation: Decimate to budget,
scale and forward direction per section 8, texture at 1–2K, a line in the license registry.

**Paid packs, itch, Fab, Asset Store** — the user buys or downloads and puts the zip into
`art/_downloads/`. From there it's your job.

## 7. Blender: Python scripts
All Blender work is Python scripts in headless Blender, run by the lead and subagents in parallel:
`$B -b [file.blend] --factory-startup --python-exit-code 1 -P script.py -- args`. No MCP is needed.

- **Headless.** `--factory-startup` — without the user's settings and addons; `--python-exit-code 1`
  — an exception yields an exit code; `--online-mode` — for network access. In 5.x the engine is `BLENDER_EEVEE`.
- **The source of truth is the asset script** `art/<category>/<name>.py`: it can be re-run,
  recolored, handed to a subagent. Work in `art/…/<asset>.blend`.
- **A Blender MCP the user already has** may be used by the lead only, for a quick look. First check
  `bpy.data.is_dirty` and `bpy.data.filepath`: if there is someone else's unsaved work, ask before
  opening your file. Carry any edits made there into the script.

Call the templates directly from `<skill>/scripts/templates/blender/`:

| template | what for |
|---|---|
| `example_prop.py` | the procedural prop pattern: palette atlas, bevel, weighted normals, origin at the bottom, .blend + GLB. Copy into `art/…/<name>.py` and adapt |
| `export_glb.py -- --out x.glb [--collection C] [--engine godot\|unity\|web] [--draco\|--meshopt] [--webp] [--max-tris N]` | export with an engine preset; prints tris, materials, textures, dimensions, size; exit code 3 — budget exceeded |
| `preview.py -- --out DIR [--glb f] [--turntable 8] [--engine workbench\|eevee\|cycles] [--ortho --transparent]` | studio render for boards, uniform scale across the whole turntable |

The loop per asset: script → `export_glb.py` → `preview.py` → you look at the PNG yourself (Read) →
edit. Show the user only what you have already looked at yourself. Iteration is cheap: on Blender
5.2 the lantern from the example (512 tris) is built and exported in ~1 s, EEVEE 768px — ~1.3 s,
a Workbench turntable 8×512 — 0.5 s.

## 8. Stylized modeling
- **Scale and axes.** Metric, 1 unit = 1 m, real sizes: door 2.1 m, character 1.7–1.8 m,
  kit step 1, 2 or 4 m. The model faces -Y (Front view); export with Y-up gives +Z forward — that is
  what Godot, three.js and glTFast expect.
- **Origin.** For a prop and a character — bottom center, for a kit piece — a grid corner. Before export
  apply rotation and scale (`export_glb.py` does this itself where it's safe).
- **Shape.** Primitives and bmesh (extrude, inset, taper), large masses. The silhouette must read
  at 128 px (`preview.py --size 128`); small details become noise at gameplay distance.
- **Bevels.** Bevel with `limit_method=ANGLE`, width 2–5% of the part's thickness, 1–2 segments,
  `harden_normals`; on top, Weighted Normal (`keep_sharp`) and smooth shading. Bevels catch the light, and
  low-poly stops looking cheap. For a faceted style — flat shading without bevels.
- **Color.** A 16–256 px palette atlas with `interpolation=Closest`: faces are colored by moving UVs to the center
  of a cell. One material for all props — one draw call, recoloring = swapping the atlas. Emission —
  a second atlas in Emission Color, still one material. For large surfaces — a trim sheet
  512–1024 (procedural or generated).
- **UV.** A palette needs no unwrap; a trim sheet — `smart_project`/`cube_project` and alignment to
  rows. AO baked into the atlas or vertex colors gives depth without runtime AO.
- **Names.** `SM_` — static mesh, `SK_` — skinned, `M_` — material, `T_<name>_<map>` —
  texture; clips `idle`, `run-loop`; collections by category. Godot collisions — suffixes:
  `-convcolonly` (convex proxy, cheap), `-colonly` (concave, static only), `-col` (mesh +
  collision), `-navmesh`, `-rigid`. A GLB for Unity and web must not contain such objects: there they
  become visible.
- **Modular kit.** A fixed grid (wall 2 × 3 m, thickness 0.2 m), all pieces in one
  .blend, one object per piece, a shared material. Before export, assemble a test layout and
  render it: seams and repetition become visible. In Godot, a kit from one GLB → MeshLibrary for GridMap.
- **LOD.** Godot generates LODs on import itself; Unity — `_LOD0/_LOD1` in one FBX; web —
  `THREE.LOD` or Decimate in Blender (0.5 → 0.25). Only for things seen many times from afar.

## 9. Characters
**You make a stylized character yourself.**
1. **Proportions** per the art bible: chibi — 2–3 heads, stylized — 4–6, heroic — 7–8. Head,
   hands and feet larger than real: at gameplay distance only they read.
2. **Base mesh.** Fast — the Skin modifier on a "skeleton" of edges, then Mirror and bmesh edits;
   or assembly from primitives with Remesh.
3. **The face** reads at camera distance: large shapes (eyes as geometry or an atlas decal,
   brows, a wedge nose), no wrinkles. Check — a render from the gameplay camera distance at its resolution.
4. **Pose and scale.** T- or A-pose, facing -Y, feet at z=0. Budget — section 13.
5. **Rig** — in increasing order of cost: a bone per rigid part (`parent_type='BONE'`) for
   robots and simple creatures; **Quaternius's UAL skeleton as your own rig** — fit the mesh to its
   proportions, `parent_set(type='ARMATURE_AUTO')`, and all 250+ clips work without retargeting
   (the cheapest path to rich animation); Rigify (`armature_human_metarig_add` → generate) for
   hand animation, only DEF bones go to the engine (`use_armature_deform_only`); Mixamo auto-rig —
   a user step (section 6); Tripo auto-rig — only for Tripo models.
6. **Animations.** Quadrupeds and simple cycles — keys in code (fcurves + Cycles modifier).
   Humanoids — UAL or Mixamo. Retargeting: Godot — BoneMap + SkeletonProfileHumanoid on import;
   Unity — Humanoid Avatar; three.js has no retargeting, bone names must match.
7. **Procedural animation in the engine** — bobbing, squash-stretch, leaning into turns, head
   look-at, foot IK, spring secondary motion, attack tweens. Cheap juice; for a simple character it is often
   enough instead of clips.

The main character is a critical part: if the user isn't impressed or the capture is clearly weaker than the bar —
mini-rounds per `references/gauntlet.md`. **A realistic character** — via Tripo or Meshy
(section 6) and cleanup in Blender; don't do realism by hand: it takes long and comes out worse than the generator.

## 10. 2D, UI, VFX
- **Procedural 2D.** You write SVG in code (shapes, gradients, `feTurbulence`), rasterize with
  `rsvg-convert -w 256 -h 256 in.svg -o out.png` or
  `magick -background none -density 384 in.svg -resize 256x256 out.png`; export 1× and 2×. Noise —
  Python with numpy and Pillow (fBm, Worley, domain warp; tiling — sampling on a torus), to the palette
  — `magick in.png -dither None -remap palette.png out.png` (palette from Lospec or from ART_BIBLE).
  Runtime generation works too: Godot `Image`, `NoiseTexture2D`, `FastNoiseLite`; three.js
  `CanvasTexture`, `DataTexture`. A shader (toon ramp, triplanar, dissolve) is often better than a texture.
- **Pixel art — Aseprite CLI** (`A=/Applications/Aseprite.app/Contents/MacOS/aseprite`): sheet —
  `$A -b hero.aseprite --sheet hero.png --data hero.json --format json-array --sheet-type packed --list-tags --trim-sprite`;
  atlas — `$A -b *.png --sheet atlas.png --data atlas.json --sheet-pack`; `--scale 4`;
  automation — `--script gen.lua`. Nearest filtering, integer scale. Frame grids —
  `magick montage *.png -tile 8x -geometry +0+0 -background none sheet.png`.
- **3D → 2D.** `preview.py --ortho --transparent --azim <angle>` for 8 or 16 directions, then
  pixelization and `-remap` to the palette: the sprites stay consistent with the 3D kit.
- **Painterly 2D** (concepts, backgrounds, portraits, icons, textures) — an image generation
  tool, if the environment has one (not required), with a prompt from ART_BIBLE (palette, light,
  shape, prohibitions); for sprites — a flat background for keying. A unit pose sheet (idle, attack, hit, death…) —
  by generation or by drawing/rendering in Blender with an ortho camera; one character, one scale, one
  frame grid.
- **UI.** 9-slice with explicit corners (16 px on a 48×48 source): Godot `NinePatchRect` /
  `StyleBoxTexture`, Unity Sprite Border + Image Sliced, Phaser `add.nineslice`, Pixi v8
  `NineSliceSprite`, CSS `border-image`. Fonts and colors — from the UI section of the art bible, no emoji.
- **VFX** — engine particles and shaders, textures procedural (soft circle, spark, noise) or a
  flipbook from Blender. Godot `GPUParticles` (on web/Compatibility, if there are problems — `CPUParticles`);
  Unity Particle System (VFX Graph is not for WebGL and weak mobile devices); three.js — instanced
  sprites/points with a custom shader. Effects discipline — in `polish-release.md`.

## 11. Sound and music
- **SFX — procedural first.** jsfxr (presets `pickupCoin`, `laserShoot`, `explosion`,
  `hitHurt`, `jump`, `powerUp`, `blipSelect`) → WAV, or ZzFX — one line of parameters per sound,
  stored in code. The license is equivalent to CC0, sounds are ready immediately.
- **Libraries.** Kenney audio — CC0, direct zips (`impact-sounds`, `interface-sounds`,
  `rpg-audio`, `sci-fi`). Openverse without a key —
  `https://api.openverse.org/v1/audio/?q=<query>&license=cc0&page_size=20` (HQ Freesound previews,
  usually enough; 20 requests per minute). Freesound API — the user's key, filter out NC. Sonniss
  GDC bundle — royalty-free, no attribution, 7+ GB, the user downloads it.
- **Music.** Taste and money — the user decides in the same `AskUserQuestion`: "I'll pick
  CC0/CC-BY to match the mood (Recommended for the vertical slice)" — OpenGameArt, incompetech (CC BY 4.0,
  attribution required); "you have your own music or a composer"; "generation" — ElevenLabs
  Music (paid key, commercial use on a paid plan). Suno has no official
  API and the disputes aren't over; Udio doesn't allow downloads. Chiptune — ZzFXM in code.
- **Processing.** `ffmpeg -i in.wav -af loudnorm=I=-16:TP=-1.5 -c:a libvorbis -q:a 4 out.ogg`.
  Music — a seamless loop; SFX — mono, short, no silent tails. Everything from libraries goes into the registry.

## 12. Export and import per engine
Check every export in the engine: import, the object in the scene, CAPTURE from the gameplay camera. A Blender
preview doesn't show the engine's axes, scale and lighting.

**Godot 4.**
- `export_glb.py --engine godot` → `res://assets/…/x.glb`. After external changes —
  `godot --headless --import --path .`, otherwise export and CAPTURE see the old version. Commit `*.import`
  and `.uid`; not `.godot/`. Suffixes work directly in the GLB: `-convcolonly` → StaticBody3D +
  ConvexPolygonShape3D (verified on 4.6); clips with `-loop` loop.
- Extract materials you want to edit into `.tres` (Advanced Import Settings), otherwise a reimport overwrites them.
  Draco isn't needed: the mesh is converted on import. GLB is more reliable than importing `.blend` directly: it
  doesn't require Blender for subagents.

**Unity 6.**
- `export_glb.py --engine unity --out x.fbx` (FBX without 100× and -90°: scale all, -Z forward, Y up,
  bake space transform) or GLB via glTFast (`com.unity.cloud.gltfast`). Model: Scale Factor
  1, Read/Write off; characters — Rig Humanoid, clips without a skin — Avatar "Copy From Other Avatar".
  Textures: ASTC on mobile and web, BC/DXT on PC. Materials — remap to URP Lit or toon. Work
  through the `unity` CLI and the editor MCP; 2D — Sprite Atlas (Create → 2D → Sprite Atlas, packing
  per scene); WebGL — Brotli compression, Code Stripping High, ASTC textures, no unnecessary packages.

**three.js / web.**
- `export_glb.py --engine web --meshopt` (or `--draco`). Decoders:
  `loader.setMeshoptDecoder(MeshoptDecoder)` from `three/addons/libs/meshopt_decoder.module.js` or
  `DRACOLoader` with the decoder files in `public/`. On the lantern: 24 KB → meshopt 12 KB → Draco 6 KB.
- `--webp` — only for large painterly textures; keep Closest palettes as PNG. KTX2/Basis and
  `simplify` — via `npm i -D @gltf-transform/cli` when needed. Closest arrives as a
  NEAREST sampler; base color — `SRGBColorSpace`.

## 13. Budgets
The totals go in TECH.md "Budgets", the asset card holds only its own budget. `export_glb.py --max-tris N
--max-kb N` fails with exit code 3 when exceeded.

| | web / portals | mobile | PC |
|---|---|---|---|
| triangles per frame | 100–300k | 50–300k (weak devices — 50–100k) | 0.5–2M |
| draw calls | < 100–200 | < 100–150 | up to ~2000 |
| materials per asset | 1 (atlas) | 1 | 1–3 |
| hero / prop texture | 1024 / ≤512 or atlas | 1024 / ≤512 | 2048 / 1024 |
| build size | the store/portal limit — from research; initial download — the smaller the better (guideline ≤ 20–50 MB) | guideline ≤ 150 MB | unlimited |

Assets in triangles: small prop 50–500, furniture 300–1.5k, kit piece 12–500, tree 200–2k,
car 1–5k (hero 5–20k), NPC 1–5k, hero 3–10k (stylized on PC — up to 15–30k). Engine base:
Godot web — ~40 MB wasm uncompressed (subtract from the store/portal limit before assets); an empty Unity
web build — 6–10 MB compressed. Music and textures weigh the most (a 3-minute track in OGG q4 — ~3 MB).
Check size with `du -sh` on the build folder, not by eye.

## 14. Look-dev scene
Goal: the user sees what the game will look like before mass production. The scene lives **in the
engine**, not in Blender: the final look comes from the engine's lighting, post-processing and shaders.

1. **Scene** — `scenes/lookdev/` (Godot), `Assets/Scenes/LookDev.unity` or `?scene=lookdev`
   (web): a 10–20 m piece of environment, 2–3 hero assets (what the player sees most often), the main
   character (idle, if available), an enemy or NPC depending on the genre, one VFX, sky/fog/background, a HUD mockup with
   real fonts and colors.
2. **Lighting and post** — strictly per ART_BIBLE: key light direction and color, ambient, fog,
   tonemapping (Godot Environment; Unity — Global Volume with a URP profile: Tonemapping, Bloom; three.js
   `toneMapping` + EffectComposer), glow/bloom, AO, color grading. Signature techniques — on screen
   and at full strength.
3. **Camera** — the gameplay one: FOV, height, angle and resolution from CONCEPT and ART_BIBLE, not a pretty
   angle that won't exist in the game.
4. **CAPTURE** with the command from ENV.md with `--out .studioigor/captures/lookdev` (frames
   `frame_NNN.png` + `sheet.png`): gameplay view, character closer up, wide shot, HUD.
5. **Self-check before showing:** the frame next to the references (`magick montage cap.png ref1.jpg
   ref2.jpg -tile 3x -geometry 640x360+4+4 cmp.png`), value structure in grayscale (`magick
   cap.png -colorspace Gray g.png`), no forbidden colors, silhouettes and signature techniques read.
   Close an obvious gap yourself.
6. **Board** `.studioigor/boards/lookdev/board.json`: option = a look-dev version (A/B on
   lighting or post is possible), `media` — frames (`../../captures/lookdev/…`) and 1–2 references alongside, question
   "Is this how the game will look?". `board.py build …`, then in the background
   `board.py serve .studioigor/boards/lookdev --open --until-feedback`.
7. **Approval** — `AskUserQuestion`: "Approve (Recommended)" / "Close — adjust" / "Not it".
   After a "yes": `decide --by user`, `tick "approved the look-dev"`, `commit --tag lookdev-v1`.
8. **Not impressed** ("cheap", "not it", a second rejection in a row) — 3–6 mini-rounds per
   `references/gauntlet.md` (target "look-dev and key frame"), then show again.

The look-dev scene remains the reference: every new asset in phases 6–8 is first placed in it and captured.

## 15. Licenses and credits
The ASSETS.md license registry — one line per pack or third-party asset, not per file:
`| KayKit Dungeon Remastered | github.com/KayKit-Game-Assets/… | CC0 | Kay Lousberg | assets/dungeon/ | not required (we'll credit anyway) |`.
- Prefer CC0; CC-BY is acceptable if the attribution is collected. Don't take CC-BY-SA, GPL and NC for a closed
  commercial game without the user's explicit consent.
- Don't put your own work (Blender, procedural) in the registry: these are project sources. Do record generated content:
  image generation → "generated (<tool>)", `generated:true`; Tripo/Meshy → plan and license
  (free tier — CC BY 4.0, the model is public). Mixamo — royalty-free for games, "Mixamo (Adobe)".
- References from `refs/` never go into the build, or into a generator as "make it exactly like this".
- Credits in phase 10 are assembled from the registry. Once per phase, check that everything in `assets/` has a
  source: your own work, a registry line or generation.

## 16. Parallel production
Hand out a batch of independent assets (12 kit pieces, 8 props) to tech artists (`.claude/agents/`; common
rules — `team.md`).
- **No more than 3 in parallel**, each in a worktree (`isolation: "worktree"`). Before launching,
  commit your own work: the palette, the adapted `example_prop.py` as the style reference, the look-dev scene.
- **The brief inside the prompt, not a path to a document:** IDs and card lines, palette hex, conventions
  (section 8), budgets, `art/…` and `assets/…` paths, the `export_glb.py` and `preview.py` commands,
  the reference asset the style is matched to.
- **Headless only** (live Blender stays with the lead); each asset has its own `.blend` and script. Return:
  GLB paths, tris, preview PNG, a "deviations from the brief" line; commit — in its own branch.
- **The lead** assembles a contact sheet of previews (`magick montage`) on the board, rejects what falls out of
  style, merges one at a time, places the assets in the look-dev scene and runs CAPTURE.

## 17. Phases 6–8 and learn.py
- **Phase 6 (gyms).** Gray primitives are acceptable, but in the ART_BIBLE palette and at real scale:
  the feel of a mechanic must not depend on future assets. Make the asset a mechanic needs (weapon,
  car) once the mechanic is already fun.
- **Phase 7 (vertical slice).** Everything in the slice's frame is real: assets, animations, VFX, a sound for every
  action, music. The inventory narrows to "what is visible in the slice".
- **Phase 8 (content).** In batches per SCOPE.md lines. Neighboring units differ on at least two
  axes (shape, color, size, silhouette, sound). The batch contact sheet goes on the board.
- **For every new asset:** inventory line → script or source → `export_glb.py` →
  `preview.py` → look-dev scene and CAPTURE → registry line (if third-party) → commit. That's it.

**learn.py** — propose when a technique nailed the style on the first try (recoloring a pack with an atlas, the UAL
skeleton as a rig, a trim sheet for a kit), when an import failure repeated and a fix was found (axes,
scale, normals, collisions), or when research found a pack or generator better than those described:

```bash
python3 <skill>/scripts/learn.py propose --title "UAL skeleton as the rig for your own character" \
  --phase 5 --kind technique --what "the mesh is fitted to the UAL skeleton, ARMATURE_AUTO — 250 clips without retargeting" \
  --when "a stylized humanoid without Mixamo" --why "rig and animations in an hour, CC0" --source "<project>, A003"
```

The lead asks about saving at the end of the phase, not in the middle of work.
