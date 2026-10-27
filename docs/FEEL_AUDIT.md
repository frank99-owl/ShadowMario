# Feel audit — October 2026

What was measured before changing how Shadow Mario plays, what changed, and
what still needs people rather than code to answer. Every number here comes
from the simulation (`tools/make_replays.py`, `tests/test_replays.py`) or from
running the builds; nothing is estimated unless marked.

## 1. The build visitors play

The portfolio links to `frank-owl.itch.io/shadowmario`. Its HTML5 upload was
pushed by the last successful `Deploy to itch.io` run, on commit `4e6ee61`
(2026-04-22). No game code changed between that commit and `main`, so the
live game matches `main`'s gameplay.

Found while rebuilding it:

| Finding | Effect | Fixed by |
| --- | --- | --- |
| The bundle was packaged from the repo root, so it shipped a developer's `save.json` (all four levels unlocked, 346 coins, five achievements) plus the READMEs and Makefile. | Every visitor started with someone else's progress; level unlocking never happened for a new player. | `tools/build_web.sh` stages only `main.py`, `shadow_mario/` and `res/`. |
| The same pygbag pin (0.9.3) now fetches a newer browser runtime. Rebuilt from `main`, the game crashed at import (`module 'pygame' has no attribute 'event'`), then exited before its first frame. | The next deploy from `main` would have replaced a working game with a blank page. | `main.py` imports pygame at top level and does not `sys.exit` in the browser; `audio.py` defers annotations. |
| The itch page needs a click before the game boots. | A visitor sees an empty grey frame until they click. | Not fixed; an itch embed setting, worth checking on the game's edit page. |
| Nothing checked the web build. | The two breakages above were invisible. | CI `web` job: build, boot in headless Chromium (`tools/web_smoke.py`), keep the bundle as an artifact. Verified to fail on the broken entrypoint. |

Deploying is a manual workflow (`deploy-itch.yml`, `workflow_dispatch`), and it
refuses to push a bundle that does not boot.

## 2. Frame-rate dependence

Every rule is written per tick: 5 px per tick of scrolling, -20 px per tick
jump speed, timers that subtract `1/60`. The loop ran one tick per rendered
frame, so a browser holding 30 fps played the game at half speed, and nothing
in the code could tell.

Now `FixedStepClock` releases exactly 60 ticks per real second whatever the
frame rate (tested at 24, 30, 60, 75, 144 and 240 fps). Input is sampled once
per frame and held for the ticks that frame covers. The reference runs reach
the flag with the same tick count, score, health and hit count at 30, 60 and
144 fps, both in `tests/test_replays.py` and through the real `GameScene`.

All simulation randomness (enemy patrol direction, platform direction, boss
fire decisions) now comes from a per-level seed, so a recorded input replays
to the same result.

## 3. Jump measurements

Player sprite: 64 × 64 px. Scroll speed: 5 px/tick (300 px/s).

| Hold UP for | Levels 1–3 rise | Airtime | Level 4 rise | Airtime |
| --- | --- | --- | --- | --- |
| 1 tick (tap) | 75 px (1.2 bodies) | 0.38 s | 48 px (0.75) | 0.35 s |
| 6 ticks | 160 px (2.5) | 0.57 s | 118 px (1.85) | 0.57 s |
| 12+ ticks | 210 px (3.3) | 0.67 s | 235 px (3.7) | 0.95 s |

Before this change, levels 1–3 had one jump: 210 px whether UP was tapped or
held. There was no jump buffer, so pressing UP a few ticks before landing did
nothing, and no coyote time, so a press one tick after leaving an edge did
nothing either. Level 4 already had all three.

For scale only, not re-measured here: Celeste's publicly released
`Player.cs` uses a 0.1 s jump grace (coyote) window and a variable jump held
for up to 0.2 s. Its full jump is roughly 2.5 body heights. Super Mario Bros.
is commonly cited at about 4 to 5 body heights for small Mario.

## 4. Flying platforms: the 1-pixel window

The spec lands the player on a flying platform only if, at the end of a tick,
the player's centre is between 49 and 50 px above the platform's centre. The
player falls more than 1 px per tick, so landing depended on where the arc
happened to stop each tick. Simulated from a standing jump, **37 of 300
possible platform heights could be landed on at all**. The shipped levels sit
on heights that work (555 and 355), so this was invisible, but any change to
the jump arc would have made players fall through platforms they touched.

The test now covers the whole path the player moved through during the tick
(one-way: rising through a platform from below still passes through).
`test_falling_onto_a_flying_platform_lands_at_any_height` covers heights the
old rule missed.

## 5. What changed in feel, and why

| Change | Grounded in |
| --- | --- |
| Levels 1–3: 6-tick jump buffer and 6-tick coyote time; releasing UP while rising caps the rise (tap = 75 px hop, hold = full 210 px). The spec arc itself (-20, +1) is kept, in whole pixels. | §3: no forgiveness existed in the levels visitors play first. |
| Swept flying-platform landing. | §4. |
| Hit-stop: the simulation holds 5 ticks when the player is hurt, 4 when the boss is hit, 10 when the boss dies. | Impacts had sound and particles but no pause, so a hit and a non-event read the same. |
| Squash and stretch on the player sprite (stretch on take-off, squash on landing scaled by fall speed, a brief red flash when hurt). Drawing only, the hitbox is unchanged. | The sprite was rigid; landings were signalled only by a screen shake. |
| Screen shake no longer fires on every landing, only after long falls. | A shake on every landing makes the camera noise and drowns out the shakes that mean something. |
| The red "you were hurt" screen flash fires only when the player is hurt. It used to fire on any shake above 4, which included the player's own hits on the boss. | Feedback bug: hitting the boss looked like being hit. |
| The end flag counts once the player is level with or past its pole, not only on touching its centre. | Found playing the live itch.io build: crossing the pole mid-jump never touched the flag's 10 px radius (centred mid-pole), so the flag scrolled away and the level never ended. |
| Level 1 teaches in the level: "HOLD RIGHT TO RUN" until the player moves, "UP TO JUMP - HOLD IT TO JUMP HIGHER" until they have jumped twice, "ENEMIES HURT - JUMP OVER THEM" after the first hit. | Level 1 had no in-level instructions at all; controls appeared only in the pause menu. |

Deliberately not changed, because they are design decisions rather than feel
defects, and the playtests in `PLAYTEST.md` should decide them:

- **There is no stomp.** Touching an enemy always hurts, as the spec says.
  Many visitors will expect a "Mario" game to let them stomp.
- **Level 1 cannot really be lost.** An enemy takes 5% health; a run that
  never jumps finishes with 20% left.
- **Lives are dead code in levels 1–3.** `Player.respawn()` and the pause
  screen's "LIVES" line exist, but nothing calls them outside level 4.
- **Level layouts.** Moving coins or enemies without death data would be
  guessing. `tools/playtest_report.py` produces that data.
- The boss fires only when the player is **at least** 500 px away. That is
  what the spec says (`Project_2.pdf`, p. 9), even though it reads backwards.

## 6. Name and assets

**Name.** "Mario" is a Nintendo trademark, and the itch.io page and the
portfolio use it as the title of a public game. The name comes from the
University of Melbourne assignment (SWEN20003, 2024 S1), but that context
does not travel with the itch page. Renaming is Frank's call; candidates that
keep the "Shadow" identity: *Shadow Runner*, *Shadowdash*, *Shade Sprint*.

**Course policy.** `Project_2.pdf` says the implementation must be the
student's own work and covers submission and academic integrity. It says
nothing either way about publishing afterwards. The subject's current
policy on public solution repositories was not checked; worth confirming
with the subject page, since this repo is a complete solution to a recurring
assignment.

**Assets.** See [ASSETS.md](ASSETS.md). Several images and every sound have
no recorded source or license.

## 7. How to tell if it worked

None of the above proves the game is more fun. What would:

1. Five first-time players on the web build, before and after, using
   [PLAYTEST.md](PLAYTEST.md): level 1 cleared without help, seconds to first
   hit, whether they replay.
2. `tools/playtest_report.py` on the telemetry those sessions write: the
   same numbers, plus a heatmap of where they were hurt.
3. itch.io analytics: browser plays per page view, before and after a deploy.
