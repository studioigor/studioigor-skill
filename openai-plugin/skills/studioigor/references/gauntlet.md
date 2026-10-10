# Gauntlet — targeted refinement of what matters most

Read when a trigger from SKILL.md fires ("Gauntlet — targeted"): the user is not
impressed, or this is a critical part with a clear gap to the bar. Here: how to run
3–6 mini-rounds right in the session and when to offer long autonomous refinement.

## Why, and why not always

The usual "build → show → fix" cycle gets stuck at "fine": the agent grades itself
softly, and the user can't always put into words what's wrong.
Gauntlet breaks this with three things:

- a bar you can open and compare against;
- a blind comparison, where the verdict is written before you know which side is whose;
- one biggest gap per round.

The cost is tokens and time. So the technique is applied to the few things the
impression of the game rests on, not to everything.

## Critical parts and their lenses

For each target, pick 3–4 lenses up front, one per round, in rotation.

| target | bar (what to open) | lenses |
|---|---|---|
| core mechanic feel | gameplay frames of the reference (`refs.py youtube … --frames`) of the same length and interval | response: frames to the first reaction · weight and inertia · the response "chord" (motion + flash + particles + sound within the same 2–3 frames) · readability: is it clear from the frames what the player did and what happened |
| look-dev and key frame | 1–3 references from the style board, same angle and framing | value structure (squint, forget color) · light and material · signature techniques from ART_BIBLE on screen and at full strength · layer density (light, post, particles, background, camera) |
| hero asset or main character | a reference render or concept at the same angle | silhouette at 128 px · proportions and form · material under the scene's light · match to the art bible |
| the first 60 seconds and the main menu | a recording or frames of the reference game's menu | hierarchy: the next action is the most visible · path to gameplay (how many steps) · UI response (animation, sound) · style |
| capsule or trailer for release | capsules and trailers of strong games in the genre | readability as a thumbnail · hook within 3 seconds · match to the game's style |

Feel is poorly checked from frames alone. For it, rounds also rely on
numbers (frames to response, the juice checklist from `polish-release.md`), and the final
judge is the user, who plays it themselves.

## A mini-round in the session

Preparation, once per target:

```
.studioigor/gauntlet/<target>/
  BAR.md        what the bar is, its path, lenses, capture command — frozen
  ref/          bar files
  rounds/NN/    rounds: ab/{A,B,key.json}, verdict.md, outcome.json
  LEDGER.md     round log — written by reveal.py
```

The capture command is frozen: same angle, framing, scenario and seed. Otherwise
an improvement can't be told apart from reframing.

A round:

1. **Capture** the current version with the command from BAR.md → `rounds/NN/artifact.png`.
2. **Blind pair:**
   ```bash
   python3 <skill>/scripts/ab.py \
     --round .studioigor/gauntlet/<target>/rounds/NN \
     --ref .studioigor/gauntlet/<target>/ref/<file> \
     --cand .studioigor/gauntlet/<target>/rounds/NN/artifact.png
   ```
   Don't open `key.json` and don't look at file sizes (`ls -l`) — that's a hint.
3. **Critique through one lens.** Read only the lens, ART_BIBLE.md and the two images. Don't
   reread the code or your own reasoning: "that's what I intended" is exactly the thought an
   independent critic doesn't have. By default the bar wins. Call our side the
   winner only if you can point to exactly how it wins under this lens.
4. **Verdict** in `rounds/NN/verdict.md`, up to 10 lines:
   ```markdown
   # Round NN — <target> — lens: <lens>
   WINNER: A
   GAP: <the single biggest gap as an observable difference: "the bar has X, we have Y">
   FIX: <the concrete change in this round>
   ```
5. **Reveal** (the script won't open the key without WINNER and GAP):
   ```bash
   python3 <skill>/scripts/reveal.py .studioigor/gauntlet/<target>/rounds/NN
   ```
6. **One change** per FIX, nothing more. Everything else you noticed — a line in BACKLOG.md.
7. `studio.py commit "gauntlet <target> NN: <gap>"`.

If "our" side won at the reveal, reread the lens line. You built that
side and could have recognized it. If your reason doesn't survive the rereading, count it
as a win for the bar.

## When to stop

- 3–6 rounds have passed. Show the user "before → after" on the board (`board.py`,
  two options: round 00 and the latest).
- Our side has won under every lens at least once. Show the user.
- Two rounds with no visible difference: the gap is phrased as a feeling, not as an
  observable difference. Rephrase it or switch the lens.

The user decides either way. If they're satisfied, the target is closed: record
`decide … --by user`. If not — the next step.

## Escalation: long autonomous refinement

If the user is still not impressed after the mini-rounds, offer them via
`AskUserQuestion` a long refinement with the same procedure without their involvement: "Refine <target>
autonomously — N rounds while you're busy (for example, overnight)?". Only with their consent.
Then the same rounds from this file run with the same bar and the frozen capture command:
2–3 rounds per run, state on disk (`LEDGER.md`), each round a commit. In
autonomous mode, ask nothing (SKILL.md, "Autonomous mode"). When the user
returns, show "before → after" on the board and let them play.

## What not to do

- Don't run gauntlet on every mechanic and every asset. A playtest is
  enough for those.
- Don't compare the incomparable: a stylized game against a stylized bar,
  a mobile frame against a mobile frame. AAA realism against low-poly always wins
  and teaches nothing.
- Don't fix several things per round: afterwards you can't tell what worked.
- Don't change the capture between rounds.
