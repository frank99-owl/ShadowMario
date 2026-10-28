# Playtest kit

A five-person, first-play test that tells you whether a change made the game
better, measured the same way before and after.

## Setup (once per round)

- Use the build you want to judge: the web bundle (`tools/build_web.sh`, then
  serve `build/web`) or the desktop game (`python3 main.py`).
- Desktop runs write telemetry to `telemetry/events.jsonl`. Note the time
  each player starts, so sessions can be told apart in the report.
- Give each player a fresh save: `SHADOW_MARIO_DATA_DIR="$(mktemp -d)" python3 main.py` on desktop, a new private window in the browser.
- Record the screen and the player's voice if they agree. Ask first.

## Script

Read this aloud and then say nothing else:

> "This is a small game I made. Please play it as you would if you'd found it
> on its own. Say whatever you're thinking as you go. I can't help you while
> you play — that's the point. Stop whenever you'd stop on your own."

While they play, do not explain controls, warn them, or react. Mark the record
sheet. When they stop (or after 5 minutes):

1. "What was that game about?"
2. "What was frustrating, if anything?"
3. "Was there a moment where it felt good?"
4. "Would you play another level?" (Only then: offer it, and record whether
   they take it.)

During the test, press **F9** at the end of a run to save its input to
`replays/`. `python tools/replay.py replays/<file>` plays it back in a
window, so you can rewatch exactly what they did.

## Record sheet (one row per player)

| # | Date | Build (commit) | Found how to move without help? (s) | First hit (s) | Cleared level 1 first try? | Retries | Took the offer of another level? | Quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

## After the round

```bash
python tools/playtest_report.py
```

It writes `telemetry/report/summary.md` (attempts, wins, quits, first-try
clears, median seconds to first hit and to clear, per level) and one
`heatmap_level<N>.png` per level: orange marks are hits, red marks are
deaths, grey marks are where someone quit or restarted.

Compare rounds on the same three numbers: **first-try clear rate for
level 1, seconds to first hit, share who accept another level.** A change
is an improvement only if those move, whatever the build looks like.
