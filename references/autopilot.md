# Independent development — autopilot

Read when the user asks to make the game without them: "make the game yourself", "without
me", "on your own", "while I sleep", "in autonomous mode", "headless". And in
every autopilot tick. Here: how to ask and launch, how a tick works, how to
decide for the user, what is forbidden, how to finish and how to hand decisions back to the
user.

Contents: 1 Launch — ask first · 2 Preparation and start · 3 How a tick works ·
4 Deciding for the user · 5 Phases on autopilot · 6 Prohibitions · 7 Dead ends · 8 Finish ·
9 The user returns · 10 Control

## 1. Launch — ask first

Don't launch the autopilot without an explicit "yes". One `AskUserQuestion`, up to 4 questions.
The first question is always the confirmation:

- **"Start independent development of the game?"** (header "Autopilot"):
  - "Yes, launch it (Recommended)" — "I'll make all the decisions for you: idea, style,
    engine, mechanics. I work on a schedule until I reach the goal or run out of
    time. Leave this session open. I push and publish nothing."
  - "No, let's do it together" — the normal step-by-step mode.
- **"How far should I take it without you?"** (header "Goal"): "Playable vertical slice (Recommended)" —
  phases 1–7 · "Full game" — 1–9 · "Game and release build" — 1–10 without publishing.
- **"How much time do I have?"** (header "Time"): "One night, ~10 h (Recommended)" · "A day" ·
  "Three days".
- **Platform** (header "Platform") — only if the user hasn't named it:
  "Browser" · "PC" · "Mobile" · "You decide". If they named the platform, use the fourth
  question to ask about the idea: "Do you have an idea, or should I come up with one?", but only if there's no idea
  in their message.

Answer "No" → normal mode from phase 1. If the user has already said "make it yourself,
launch it, overnight", still ask the first question and infer the rest from their message.

## 2. Preparation and start

While the user is around, this takes up to 5 minutes:

1. Project: `studio.py init` (pick the folder yourself, SKILL.md "New project"). The brief
   verbatim goes into CONCEPT.md as the line "User brief: …".
2. `studio.py decide "independent development: goal …, time …, platform …" --by user`.
3. If it's already known that a human will be needed (sudo password, engine account login),
   do it now with the user, one action at a time. If it isn't known, don't guess:
   the autopilot will choose a path that doesn't need it.
4. `studio.py commit "studioigor: autopilot start"`.
5. Launch:
   ```bash
   python3 <skill>/scripts/autopilot.py start \
     --goal slice|game|build --hours 10 --brief "<the user's message verbatim>"
   ```
   The script checks that `claude -p` works in the `auto` permission mode, and prints
   the schedule and the prompt for CronCreate. On macOS, `caffeinate` keeps the Mac from idle
   sleep. The `--mode bypass` mode (no permission checks) — only with the user's explicit
   consent, if `auto` is unavailable.
6. **Scheduler — the built-in CronCreate:** call `CronCreate` with exactly the `cron` and
   `prompt` that `start` printed (`recurring: true`). Lost them — `autopilot.py prompt --cron`.
7. **First tick — right away**: the same `autopilot.py tick --root …` command via Bash with
   `run_in_background: true`. If Claude Code asks for permission for this command,
   have the user choose "always": after that, ticks run without them.
8. Tell the user in 3–4 lines:
   - what is happening;
   - that this session must stay open and the Mac on (lid open or an
     external monitor);
   - how to watch and how to stop: "autopilot status" / "stop the autopilot"
     (`autopilot.py status` / `stop`);
   - where the result will be: `.studioigor/autopilot/REPORT.md`.

After the start, **this session doesn't touch the project**, it only launches ticks. To
intervene, run `autopilot.py stop` first.

## 3. How a tick works

- Every `--every` minutes (15 by default) the CronCreate job tells the session to launch
  `autopilot.py tick` in the background. The runner holds a lock (flock) for the whole tick: while it runs,
  new launches exit immediately. Then it launches a fresh main agent — `claude -p`
  in the game folder with the tick prompt in `auto` mode.
- The last line of the tick output is a command to the host session: `NEXT: now` — the next
  tick right away (CronCreate is a safety pulse in case the chain breaks);
  `NEXT: wait` — nothing, wait for the schedule (a tick is still running, a pause); `NEXT: stop` —
  delete the job (CronList → CronDelete) and show `autopilot.py status`. The session
  does nothing else.
- CronCreate jobs fire while the session is open and idle, and live up to 7 days,
  so `start` caps the time at 167 hours.
- Every tick starts with a clean context. All knowledge is on disk: `status`,
  STATE.md, DECISIONS.md. So `decide` / `note` / `commit` records on autopilot are
  mandatory: without them the next tick won't know what happened.
- One tick — one meaningful step: the gates of the current phase, the cycle of one mechanic,
  a batch of assets. A tick lasts up to `--tick-minutes`, then the runner interrupts it.
- After a tick the runner commits anything uncommitted, writes a line to
  `.studioigor/autopilot/LOG.md` and checks the stop conditions:
  - the agent created the `STOP` file, or the goal's gates are closed;
  - time ran out or ticks ran out;
  - 3 ticks in a row with an error;
  - 3 ticks in a row with no changes to the game (autopilot service files and STATE.md don't
    count).
- Usage limit — pause until the reset, the tick doesn't count. Error — pause of 5,
  10, 15 minutes. Hitting the budget or the timeout while having changed the game is not an error.
- If the tick agent died together with the runner (the session was closed), its process group
  gets killed; an orphaned agent prevents launching a second one.
- Subagents work as usual, in a worktree, but no more than two at a time. By
  the end of the tick they must all have returned and been merged or deleted: `claude -p`
  exits, and background agents go with it.

## 4. Deciding for the user

The user has handed over the decisions, but the game is still theirs. Decide the way they would.

- **Sources of taste**, in order:
  1. the brief verbatim;
  2. this game's `.studioigor/PREFERENCES.md`, then preferences and accepted improvements
     from `user-choices/` (`status` shows them all);
  3. the genre and references from the brief;
  4. the recommended options in the reference files.
- **Boldness within the pillars.** From the options, take the one that makes the game
  memorable, not the safest one. But if an option breaks the brief, that's a failure,
  not boldness.
- **Record every taste decision** in two places:
  - `studio.py decide "…" --by proxy --why "…" --options "what else there was"`;
  - a line in `.studioigor/autopilot/REVIEW.md`: `| phase | decided | alternative | why | commit |`.
  This is the list for review when the user returns. Factual decisions
  (engine version, install path) are recorded `--by agent`, they don't go into REVIEW.
- **user gates:** `studio.py tick "…" --proxy`, i.e. a check-off with the PROXY mark.
  A decision on the user's behalf is made only after the work they would evaluate
  has been done: the board is built, the capture is taken, the proxy playtest is run.
- **Don't call `AskUserQuestion`**: it is forbidden in this mode. Build boards (`board.py
  build`/`from-refs`): they are material for the report. But don't run `serve --until-feedback`,
  there will be no feedback.
- **Game-designer layer:**
  - the proxy approves no more than 2 ideas per point, cost S or M, within the pillars; status `approved (proxy) → M##`;
  - the other best ideas — `proposed`: the user will see them.
- **learn.py:** only `propose`. `accept` / `reject` are the user's decision.

## 5. Phases on autopilot

| phase | instead of the user |
|---|---|
| 1 Idea | Self-interview: slots from the brief, the rest — recommended answers from `interview.md`. Pitch card in CONCEPT.md. Signature hooks: game-designer gives 8–12, the proxy takes 2 |
| 2 Style | 3 directions, real references, a board for the report. Choose by brief and genre, by what the agent can make in this stack (Blender, procedural) and what reads on screen. ART_BIBLE right away |
| 3 Stack | Platform — from the launch question. Engine — the one the agent handles best for this game and that installs **without sudo and logins** |
| 4 Environment | Install without sudo: brew, an archive into `~/Applications`, local packages. Editor MCP — if it installs without a GUI login, otherwise CLI and headless. A 3D game — Blender (`brew install --cask blender`, scripts only); if it won't install — 3D without it (`assets.md` §4). Whatever needs a human — `--block` with exact instructions in REPORT |
| 5 Assets | Mixamo and Tripo are unavailable (user account). Instead: CC0 animation packs (Quaternius UAL and similar), Blender, procedural 2D. The proxy approves look-dev after 1–3 gauntlet rounds on the key frame |
| 6 Mechanics | A proxy playtest (below) instead of the user playing. Lock — after a playtest with the verdict "fun" per the fun checklist, with a `proxy` mark in the mechanic's notes |
| 7 Vertical slice | The game-ness checklist is mandatory. Verdict "continue" or "rework", no more than 2 reworks. Don't pivot: that's the user's decision — STOP with a report |
| 8 Content | Per SCOPE.md. Contact sheet on the board — for the report |
| 9 Polish | "One gap" rounds. "Good enough" — when the polish checklist is closed and the gap was small for 2 rounds in a row |
| 10 Release | Platform research, ship gates, build into `build/`, draft materials. Don't publish: `tick "publish" --skip "autopilot: the user publishes"` |

**Proxy playtest** — the agent has no hands and no feelings, so it relies on
what can be measured. Order:

1. A bot or scripted input plays through the gym (an `?autoplay` section or a scene argument).
   Frame capture: 8–16 frames or a short video.
2. Numbers: frames to input response, completion time, deaths, hits. Targets — from
   the mechanic's spec.
3. The juice checklist (`polish-release.md`): the response is motion, flash, particles and
   sound within the same 2–3 frames.
4. The fun checklist, `design.md` §1. The question is "is it fun?", not "does it work?". An honest
   answer of "boring" → a turn from the game designer, not a lock.
5. For the core mechanic and the first 60 seconds — gauntlet on feel (`gauntlet.md`, 3
   rounds). The rest doesn't need gauntlet.

Record — `PT-NN (proxy)` in PLAYTESTS.md: what was checked, the numbers, the verdict, what
changed.

## 6. Prohibitions

The runner duplicates some of the prohibitions technically (`--disallowedTools`), the rest are
on you:

- `git push`, publishing, uploading builds anywhere;
- purchases, paid APIs and assets, sign-ups and logins;
- `sudo`, system settings, deleting outside the game folder;
- editing the skill's files, except `learn.py propose`;
- messages to anyone and email;
- attempts to get around the autopilot's limits or extend your own time.

## 7. Dead ends

- The same gates won't give: 2 different approaches, then `tick "…" --block
  "<what I tried, what's needed from a human>"`. Keep working on what isn't
  blocked: another mechanic, sound, content, UI.
- If the runner writes "N ticks in a row with no changes to the game" in the prompt, change the approach in this same tick.
- Create `STOP` only when there's nowhere to go: the goal is reached, or everything remaining
  depends on a human. The file holds one line with the reason.

## 8. Finish

When the goal is closed, or time is up, or at a dead end:

1. The game runs with one command (RUN from ENV.md). For the build goal — a build in `build/`.
2. Capture: 4–6 key frames and 20–30 seconds of gameplay into `captures/final/`.
3. A "what came out" board (`board.py build`): frames, style, mechanics.
4. `.studioigor/autopilot/REPORT.md`, short, in this order:
   - **How to play** — the first line, one command;
   - what was done by phase, one line per phase;
   - the 5 most debatable decisions from REVIEW.md;
   - what was skipped or blocked and why;
   - what the user needs to do (logins, replacing packs with Mixamo, publishing);
   - proposed game-designer ideas awaiting a decision;
   - next steps.
5. `studio.py commit "autopilot: finish"`, `studio.py note …`, then
   `echo "DONE: <one line>" > .studioigor/autopilot/STOP`.

The last tick (by the tick limit or the time limit) gets "do the finish" in its prompt. If
the autopilot stopped some other way, the runner writes a short auto-report; the first interactive session
completes it per this section (§9).

## 9. The user returns

`status` will show that the autopilot is stopped, and how much was decided on the user's behalf.

1. No REPORT.md — build it first per §8.
2. Launch the game (RUN), open the "what came out" board. Let them play.
3. One `AskUserQuestion` with multiSelect: "Which of the decisions made for you should I redo?". Up to 4
   of the most debatable items from REVIEW.md plus "all good".
4. The selected ones: reopen the gates (`tick --reopen`) and work in the normal cycle with the
   user. Confirm the rest in a batch: `tick "…"` without `--proxy` removes the
   PROXY mark, the decision — `decide --by user --why "accepted after the autopilot"`.
5. Game-designer ideas with status `proposed` — in one question.
6. After that — normal mode, or a new autopilot run if the user wants one.

## 10. Control

| command | what it does |
|---|---|
| `autopilot.py start …` | launch: checks, schedule and prompt for CronCreate |
| `autopilot.py prompt --cron` | print the schedule and prompt for CronCreate again |
| `autopilot.py status` | whether it's active, ticks, cost, last log lines, report |
| `autopilot.py stop [--now]` | the current tick finishes and commits; `--now` interrupts immediately |
| `autopilot.py tick` | one tick — the session launches it per the CronCreate job |
| `autopilot.py prompt` | show the next tick's prompt |

Files: `.studioigor/autopilot/`:
- in git: `REVIEW.md`, `REPORT.md`, `STOP`;
- not in git: `LOG.md`, `state.json`, `lock*`, `logs/` (raw output of each tick,
  `session_id` for `claude --resume`), `runner.log`.

Other schedulers, only if the user asks:
- to close the terminal — `start --scheduler system`: launchd on macOS, cron on Linux,
  removed automatically on stop;
- no scheduler — `--scheduler none`: ticks are launched manually.
