# Team — how the lead works with subagents

Read before any parallelization and before the first subagent in a project. Covers:
how the lead hands work to the studio's roles, runs a worktree from commit to cleanup, verifies the
result on disk and doesn't burn tokens. The short version is in SKILL.md, "Subagents and git".

## Contents
1 When to parallelize · 2 What not to hand off · 3 Roles and how to call them · 4 Once per
project · 5 Worktree step by step · 6 What a worktree lacks · 7 Research without a worktree ·
8 A fresh-eyes reviewer · 9 Return contract · 10 Verification on disk · 11 Prompt
template · 12 Cost · 13 The skill learns

## 1. When to parallelize and when not

By default the lead works alone and sequentially. A subagent is justified if at least
one of three holds:
- **real parallelism**: 2–3 independent tasks with non-overlapping files,
  each can be verified separately (gyms of independent mechanics, a batch of props in Blender,
  independent levels, reference sets for different style directions);
- **clean context**: a large research or review task that doesn't need your reasoning;
- **long mechanical work** (download and label references, convert a batch of
  assets) while you guide the user.

Don't parallelize:
- dependent tasks (mechanic B builds on A's code): A first, merge, then B;
- tasks with shared files (`project.godot`, `package.json`, `ProjectSettings/`, the main
  scene, the player controller, the shared HUD). Prepare the shared points — input, autoload, folders, data schema —
  yourself BEFORE launching, give the agent its own folder;
- feel tuning: the lead runs the "played → said → adjusted" loop;
- small stuff of 10–15 minutes: launching an agent costs more (§12).

No more than 3 agents at once: each costs tens of thousands of tokens, and you merge and the
user tries things one at a time anyway.

## 2. What never to hand off

- **Talking to the user** (subagents have no `AskUserQuestion`): questions,
  playtests, boards, showing results.
- **Decisions and state:** `studio.py decide / tick / note`, the `locked` status, STATE.md,
  DECISIONS.md, PIPELINE.md. The agent proposes, you decide. **Merge and rollback** — also you.
- **The engine editor via MCP (and a live Blender MCP, if the user has one).** There is one
  instance: two agents in one editor or Blender scene silently corrupt it. Subagents are
  headless: `Blender -b -P`, the engine CLI. Roles from `.claude/agents/` don't get MCP (they have an explicit `tools`), but
  `general-purpose` inherits all MCP servers — forbid them in the prompt.
- **Push, publishing, logins, payment** — never without the user.

## 3. The studio's roles and how to call them

`studio.py init` puts the roles into `<game>/.claude/agents/`. A role defines the mission, what to read,
what it may touch and the return contract. Everything else comes from your prompt.

| role | for what | worktree | writes |
|---|---|---|---|
| game-designer | spec, balance, economy, mechanic research, holism review | if it edits files | tuning data, `research/mech-*.md` |
| art-director | reviewing frames against ART_BIBLE, finding references | no, read-only | only `refs/<set>/` |
| tech-artist | headless Blender, GLB, previews, materials, shaders, VFX | yes | assets and their sources |
| gameplay-programmer | mechanic gym, systems code, tuning panel | yes | code, scenes, data |
| level-designer | levels, tracks, arenas, placement, pacing | yes | level scenes and data |
| sound-designer | SFX, music, ambience, hooking up audio | yes | audio and sound hooks |
| narrative-designer | dialogue, texts, cutscene scripts | yes | dialogue data, cutscenes |
| qa-tester | TEST/BUILD/CAPTURE, acceptance criteria, bugs | no, read-only | nothing |

**How to call.**
- **A new session started in the game root:** `subagent_type: "<role>"`. Editing
  roles already have `isolation: worktree` in their frontmatter; pass it explicitly anyway.
- **The session in which you just ran `init`:** the `.claude/agents/` folder didn't exist
  at startup, and Claude Code doesn't see it until a restart. Use `subagent_type: "general-purpose"`,
  paste the text of `.claude/agents/<role>.md` without the frontmatter at the start of the prompt, pass
  `isolation: "worktree"` explicitly, forbid MCP and its own subagents.
- Adapt the project copies of the roles to the game (path to godot, folders); not the skill's templates.

## 4. Once per project (before the first worktree)

1. **Check that `.claude/worktrees/` is in .gitignore** (`studio.py init` adds it
   itself; older projects lack it). Claude Code puts subagent worktrees there, inside the
   repository. Without this line `studio.py commit` (`git add -A`) will add a
   live worktree as a nested repository (gitlink), and the history gets cluttered:
   `grep -qxF '.claude/worktrees/' .gitignore || echo '.claude/worktrees/' >> .gitignore`
2. **Worktree base.** By default (`worktree.baseRef: "fresh"`) a worktree is cut from
   `origin/HEAD`, and without a remote — from the local HEAD. We don't push, so with a remote the
   agent gets a stale `origin/main` without your commits. If `git remote` is not empty —
   `.claude/settings.json`: `{"worktree": {"baseRef": "head"}}`. The safety net in any
   case is the line "Base: <sha>" in the prompt (§11).
3. **`.worktreeinclude`** in the game root (.gitignore syntax): ignored files that
   Claude Code copies into every new worktree. Small stuff goes here: `.env`, local
   configs, downloaded packs. Big caches (`.godot/`, `Library/`, `node_modules/`) don't go
   here: they get rebuilt (§6).
4. `studio.py commit "studioigor: worktree setup"`.

## 5. Worktree step by step

1. **Prepare and commit.** Make the shared points yourself, then `studio.py commit "…"`.
   A worktree is cut from the committed state: the agent won't see anything uncommitted.
   Note down `git rev-parse --short HEAD` — that is the base.
2. **Launch.** Independent tasks — in one message, up to 3 Agent calls. Each has
   `isolation: "worktree"` and a prompt from the §11 template. While the agents work, guide the
   user or do your own task in other files.
3. **The agent** prepares its worktree (§6), does the task, looks at a frame itself, commits in
   its branch and returns the contract (§9) with the branch and the path.
4. **Check the branch before merging** (`main` is your working branch, `studioigor` in someone else's game):
   ```bash
   git worktree list
   git log --oneline main..<branch>          # are there commits?
   git diff --stat main...<branch>           # only allowed files?
   git diff main...<branch> -- <file>        # read the important parts
   git -C <worktree-path> status --short     # nothing left uncommitted?
   ```
   Files outside the allowed set, extra tests and docs (rule 1 in SKILL.md), edits to shared
   files — send back to the agent (§10) or revert in its branch. The agent's frames are in
   `<worktree-path>/.studioigor/captures/` and don't go into git: look at them now,
   they will be gone after the worktree is removed.
5. **Merge one at a time:** `git merge --no-ff <branch> -m "merge <branch>: <what>"`. With
   `--no-ff` each task gets its own node in the history: easy to find and revert. A conflict
   means the files were split badly: resolve a small one yourself, for a large one — `git merge --abort` and
   relaunch the task from the new HEAD.
6. **After every merge the game must run.** Godot: first
   `<godot> --headless --path . --import` (new assets). Then CAPTURE from ENV.md and
   look at the frame (Read PNG); if logic was touched — also TEST (or just `studio.py verify`).
   Broken — `git reset --hard ORIG_HEAD` (everything is committed and not pushed, so this is
   safe), fix, merge again. Only then the next branch.
7. **Clean up:** `git worktree remove <worktree-path>` (`--force` if non-ignored files remain
   inside; "locked" — the agent is still working or hung: `git worktree unlock`),
   then `git branch -d <branch>` (`-d` refuses an unmerged branch — that is the safety net).
   Claude Code's auto-cleanup doesn't touch worktrees with unpushed commits, and we don't push:
   without you they pile up. `status` reminds you about leftover ones.
8. Then as usual: the user plays (RUN), `decide` / `tick` / `note`. Don't push.

## 6. What a worktree lacks

A worktree is a checkout of tracked files only. Everything in .gitignore and everything
uncommitted is missing from it. The agent's first step:

| what's missing | what happens | what to do in the worktree |
|---|---|---|
| Godot `.godot/` (import cache) | textures and models don't load, scenes fail | `<godot> --headless --path . --import` (path to godot — from ENV.md) |
| `node_modules/` | vite and playwright don't start | `npm ci` (or `npm install`) |
| Unity `Library/` | the first batchmode import takes minutes or tens of minutes | budget the time; parallel work in Unity — only when it pays off |
| packs in ignored folders | "file not found" | `.worktreeinclude` (§4) or `cp -R <main-checkout>/<folder> <folder>` |
| LFS files (`gitignore --lfs` sets up LFS locally) | text pointers instead of .glb/.png | `git lfs pull` |
| images in `refs/`, `captures/` | no references | read via the absolute path of the main checkout: reading is allowed, writing is blocked |

Don't symlink ignored folders: `node_modules/` with a slash only matches a directory, and
`git add -A` will commit the symlink. Copy or rebuild.

## 7. Research and references — without a worktree

An agent that only reads and searches works in the main checkout, without a worktree:
- **research** (`general-purpose` or game-designer) writes only
  `.studioigor/research/<topic>.md` (60–80 lines: date, sources, findings, what it changes);
  you commit it, after checking;
- **references** (art-director): each set gets its own `.studioigor/refs/<set>/` via
  `refs.py`, so style directions can be handed to 2–3 agents in parallel. You build and
  show the board (`board.py`).

Don't give one file to two agents. Whatever one WebSearch finds, search for yourself.

## 8. A fresh-eyes reviewer

The author sees what they intended, not what they made. For important artifacts, call a reviewer
with a clean context, read-only:
- **art-director** — a look-dev frame, a hero asset, a key frame, a content contact sheet
  against ART_BIBLE and the references;
- **qa-tester** — a gym before the user's playtest, the vertical slice, a release candidate: acceptance
  criteria and bugs;
- **game-designer** — the design holism check at the end of phase 6.

One review per milestone, not for every little thing. Brief rules:
- give the artifact (paths to frames, how to run it) and the bar (ART_BIBLE, paths to references,
  acceptance criteria); don't give your reasoning or "here's what I intended";
- wording: "your task is to find problems, not to approve";
- answer: first line `OK | FIXES | NOT ASSESSED`, then up to 5 findings as an observable
  difference ("in frame X — Y, the art bible says Z"), each marked "verified" (frame, run,
  file:line) or "unverified". Couldn't run or look — `NOT ASSESSED`, not `OK`.

You decide what to fix. A review doesn't replace the user's playtest. A blind A/B against the
bar is the gauntlet (`gauntlet.md`), not a reviewer.

## 9. Return contract

Every subagent returns only this, no essays and no retelling of what it read:

```text
SUMMARY: done | partial | BLOCKED
BRANCH: <branch> in <worktree path> | no worktree
FILES: <changed and created paths>
DONE:
- <up to 5 items: what the game now has>
HOW TO SEE: <RUN command or scene, what to press; frame paths>
VERIFIED: <what you actually ran: command → exit code or frame> | NOT VERIFIED: <why>
BLOCKED: <what's in the way and which decision is needed from the user> | none
```

Paste this block into every prompt. The roles in `.claude/agents/` already have it.

## 10. Verification on disk

A smooth answer doesn't prove the work was done. The proof is a commit, a file, a frame.
It has happened that an agent spent 26 calls, wrote nothing and returned confident text.
Before believing it: `git log main..<branch>` is not empty, `git diff --stat` matches
FILES; "works" — you run CAPTURE yourself after the merge and look at the frame; "tests
are green" — you run TEST yourself; reviewer findings marked "unverified" — verify before editing.

Contract not fulfilled — don't launch a new agent. Continue the same one via `SendMessage`
(ID — in the Agent result) and name what's missing: "there is no commit in the branch — commit and
return the contract". It already has the context, so this is cheaper.

## 11. Prompt template

```text
Role: <role> — follow .claude/agents/<role>.md
      (for general-purpose: paste the role text here without the frontmatter)
Game: "<name>", engine <engine>. Main checkout: <absolute path>.
Base: <sha>. First thing, `git log -1 --format=%h` must print <sha>; if not, and you
haven't changed anything yet — `git reset --hard <sha>`.
Goal: <one sentence — what will appear in the game>.
Context: <3–8 lines of summary: mechanic, parameters, style, what already exists>.
Acceptance criteria:
- <observable: "in scene X pressing Y makes Z happen", "the CAPTURE frame shows …">
May touch: <folders and files>. May not: project.godot / package.json / main
scene / .studioigor/*.md / <other shared files>.
Commands from .studioigor/ENV.md: RUN: … | CAPTURE: … | TEST: … | scene directly: …
Worktree preparation: <godot --headless --path . --import | npm ci | git lfs pull | none>.
Rules:
- The game comes first: make what can be seen and played. A test — only for logic that
  breaks silently. Don't write documentation.
- Don't ask the user. Decide small things yourself and note them in the answer; taste, money,
  accounts — into BLOCKED.
- Don't push. Commit only in your branch: git add -A && git commit -m "<role>: <what>".
- No MCP (mcp__blender-mcp__*, the engine editor) and no subagents of your own. Blender —
  only /Applications/Blender.app/Contents/MacOS/Blender -b -P <script>.
- Before "done", run CAPTURE and look at the frame (Read PNG).
Return strictly per the contract:
<the block from §9>
```

For research and review, remove the lines about the base, preparation and committing, and add "write only to
<path>" or "change nothing".

## 12. Cost

- **Launching is expensive.** An agent re-reads CLAUDE.md, the role and the task files: 20–40k
  tokens before the first useful action. A single feature pass by a big team of agents
  reaches 200–400k, and in practice the heaviest process produces the worst game.
- **A summary, not a list of documents.** An agent given a path will re-read the whole file.
  Give a path only to what is needed in full (ART_BIBLE for an art review).
- **No hierarchy.** Agents don't launch their own agents; there are no directors or panels. One
  critic per milestone, not a fleet.
- **Model.** Mechanical work (download references, convert a batch) can be given
  `model: "sonnet"` in the Agent call. Code and creative work — on the lead's model (roles inherit it).
- **Autonomous mode** (running in a loop without the user) doesn't change the rules: the same ≤3 agents, merge one at a time with
  CAPTURE, no questions, decisions — `--by agent`.

## 13. The skill learns

A parallel pass produced a repeatable recipe (worktree preparation for this engine
worked on the first try; a file split under which the merges went through without conflicts) —
write a proposal: `python3 <skill>/scripts/learn.py propose
--title "…" --phase <N> --kind process --what "…" --when "…" --why "…" --source
"<game>, <date>"`. Whether to save it is asked by the lead at the end of the phase (SKILL.md, "The skill learns").
