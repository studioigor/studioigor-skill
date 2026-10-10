# The game-designer layer — invent on your own, decide together

Read when a trigger below fires or the user asks to "come up with something".
Here: when the layer switches on, how to invent mechanics and signature hooks, how to select
ideas and how to show them to the user. There is one rule: **the agent invents, the user
decides**. No idea gets into the game without their "yes".

Contents: 1 Why · 2 When it switches on · 3 Techniques · 4 From 10 ideas to 3 · 5 Idea
card · 6 Showing the user · 7 Recording and the path into the game · 8 Tact · 9 Anti-patterns

## 1. Why

The pipeline executes a plan well, but a game is not remembered for execution. It is
remembered for its hook: a mechanic the neighbors do not have, a synergy of two systems, a
moment people tell each other about. The interview captures what the user wants. The
game-designer layer adds what the user would not have come up with themselves, but will say
"yes, exactly" to. The craft (fun, pillars, loops, progression) is in `design.md`. Here —
how to create something new.

## 2. When it switches on

| where | what you invent | how many to show |
|---|---|---|
| phase 1, after the pitch is approved | 3–4 **signature hooks**: how the game differs from the reference | up to 4, multiSelect |
| phase 6, before the spec of a core or signature mechanic | 2–3 **designs** of the mechanic, one of them bold | 2–3, single-select with preview |
| phase 6, the playtest answered "okay" or "boring" | 2–3 **twists** that add choice, risk or feedback | 2–3 |
| phase 7, after the vertical slice | **synergies** of locked mechanics and 1–2 new mechanics that deepen the loop | up to 4 |
| phase 8, before a content batch | the **signature moment** of each unit (set piece, level gimmick) | as a batch, on one board |
| phase 9 | **moments of delight**: surprises, secrets, easter eggs, rare events | up to 4 |
| on request | what was asked for | up to 4 |

Outside these points do not generate ideas in advance. The user needs time to play, not
only to choose.

## 3. Techniques

For each pass take 3–4 techniques, not all of them at once.

- **Verb first.** Write down the player's main verb ("drift", "hide"). Ask: what if the verb
  gets a second meaning? Drifting charges nitro; taking cover reloads the weapon.
- **"Like X, but also Y".** Cross the reference with something from a distant genre: racing ×
  rhythm game (nitro on the beat of the music), shooter × puzzle (bullets ricochet by the laws
  of billiards).
- **Inverting a convention.** Take a genre rule and flip it: in a horror game the monster is
  afraid of the player's light; in racing the one falling behind gets the best line.
- **Constraint as a hook.** Take away something familiar: no brakes, one bullet, a game with
  no UI. A good constraint gives birth to a style.
- **Risk and reward.** Every safe action gets a risky twin with a bigger reward: threading
  past traffic within inches, a parry instead of a block.
- **Synergy matrix.** A "mechanic × mechanic" table. A cell is what happens when they meet.
  Two strong cells are already a hook.
- **The theme dictates a rule.** The setting provides a mechanic: a subway game — the train
  as a timer and as cover; a game about dreams — the laws of physics change when the hero
  falls asleep.
- **One rule on top.** Add one rule that changes decisions to a verb that already works: a
  jump leaves a trail platform for 2 seconds.
- **Emergence.** Let systems interact without a script: fire + wind, noise + enemy AI,
  physics + explosions. Players will invent the rest.
- **Player expression.** Where the player can show themselves: playstyle, build, paint job,
  a replay of the best run.
- **Backwards from the aesthetic (MDA).** Pick what the player should feel ("panic under
  control") and derive the mechanic that produces that feeling.
- **A moment to retell.** Come up with what the player will tell a friend ("and then the
  train went right through the wall"). Then — a mechanic that makes such a moment possible
  without a script.

## 4. From 10 ideas to 3

1. **Diverge.** Generate 8–12 raw ideas. A fresh look helps: hand the generation to the
   game-designer role as a subagent without a worktree (`team.md`). It reads CONCEPT,
   DESIGN, STORY and PLAYTESTS and returns cards. It does not change the project.
2. **Converge.** Pick 3–4 through the filters:
   - does not violate the anti-pillars and serves at least one pillar;
   - the fun hypothesis fits in one phrase;
   - can be checked in a gym within one mechanic cycle;
   - the cost S / M / L (agent hours, new assets) matches the scale in CONCEPT;
   - does not duplicate something rejected earlier (the "Game designer ideas" table in
     DESIGN.md).
3. Among those that pass, keep ones of different types: not four variations of one.

## 5. Idea card

Five to seven lines, no more:

```
Nitro on the beat
Nitro fires stronger if pressed on the beat of the track.
Why it's fun: rhythm turns the race into a performance, mastery is visible and audible.
Check: gym — a loop track with a metronome, 3 laps with the beat and without.
Cost: M (audio sync, beat indicator). Risk: gets in the way of those who can't hear rhythm.
Pillar: "Speed on the edge".
```

## 6. Showing the user

- **Several ideas to choose from, multiple allowed** — `AskUserQuestion` with `multiSelect`,
  up to 4 options. The label is the name (1–5 words). The description is one phrase plus "why
  it's fun". Full cards if needed — on a board (`board.py build`, options without
  images).
- **One of the designs of a mechanic** — single-select with `preview`: a card
  or an ASCII diagram in the preview, the recommended option first.
- There is always a "none of them" exit (via Other) and "you decide" where the question is
  about taste.
- Context goes inside the question: "Hooks for 'Night Drift': what goes into the game?".

## 7. Recording and the path into the game

- Every idea shown is a row in the `## Game designer ideas` table in DESIGN.md with
  status `proposed`, after the answer — `approved → M07`, `rejected` (with the reason in
  one phrase) or `deferred`.
- An approved idea becomes a row in the mechanics table with status `idea`. The tier
  (`mvp` or `full`) is decided by the user: `full` by default, so that a new idea does not
  bloat the vertical slice.
- Then the usual mechanic cycle (`mechanics.md`): research → spec → gym → playtest.
  An idea that did not become fun in the gym goes to `cut`, like any other.
- `studio.py decide "hooks: …" --by user --why "…"`. `status` shows how many
  ideas are waiting for a decision.

## 8. Tact

- One pass per trigger. No more than 4 ideas at a time, no more than one such question
  in a row.
- Do not implement unapproved ideas, not even "a quick try": that is the user's decision.
- In autonomous mode ideas are only recorded with status `proposed`. You show
  them when the user returns. On autopilot (`autopilot.md`) the proxy approves no
  more than 2 ideas of cost S/M per point (`approved (proxy)`), the rest wait for the user.
- An idea the user especially loved is a signal that the technique worked.
  Record it: `learn.py propose --kind technique --phase <N> --title "…" --what "technique X
  gave hook Y" --when … --why "the user picked it right away" …`.

## 9. Anti-patterns

| what | why it's bad | how to do it |
|---|---|---|
| "let's add crafting / leveling / an open world" | a genre feature, not an idea | the idea changes the player's decisions in the 30-second loop |
| 12 ideas to the user | choosing turns into work | 3–4 after the filter |
| an idea for its own sake | complicates, doesn't add fun | a fun hypothesis in one phrase and a check in the gym |
| an idea against an anti-pillar | breaks coherence | the §4 filter |
| implement first, ask later | the decision is taken away from the user | "yes" first |
| vague: "make it more interesting" | can't be checked | the §5 card |
