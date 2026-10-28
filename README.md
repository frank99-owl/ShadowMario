# Shadow Mario (Python + Pygame)

Shadow Mario is a 2D platform game built with Python and Pygame.  
The project includes four playable levels, a scene-based UI flow, audio/save systems, and effect modules (particles, shake, transitions).

**Play it in the browser: [frank-owl.itch.io/shadowmario](https://frank-owl.itch.io/shadowmario)**

## Screenshots

| Menu | Level 1 |
| --- | --- |
| ![Main menu](docs/screenshots/menu.png) | ![Level 1 gameplay](docs/screenshots/level1.png) |

| Level 3 — boss stage | Level 4 — two-player race |
| --- | --- |
| ![Level 3 dual-layer boss stage](docs/screenshots/level3-boss.png) | ![Level 4 two-player race](docs/screenshots/level4-race.png) |

## Features

- Four levels with different gameplay pacing
- Level 2/3 platform behavior aligned with classic project logic
- Level 4 two-player race mode (P1 vs P2)
- Forgiving jump in levels 1-3: jump buffer, coyote time, and a variable height (tap for a hop, hold for the full jump)
- Impact feedback: hit-stop, squash and stretch, hurt flash
- Level 1 teaches the controls in-level, with hints that react to what the player does
- Runs at a fixed 60 ticks per second at any frame rate; every attempt can be saved and replayed exactly
- Scene-based architecture: menu, loading, gameplay, pause, settings, game-over
- Runtime configuration (`res/runtime_config.json`) for colors/UI/hitbox scaling
- Save system for unlock state, highscores, best times, coins, achievements, and audio settings, kept in the user's data folder on desktop and in `localStorage` in the browser

## Gameplay Rules

- Level 1: tutorial-style single-player stage
- Level 2: single-layer moving-platform stage
- Level 3: dual-layer platform stage with boss combat
- Level 4: two-player race with score-based winner resolution
- End flag: reached once the player is level with or past its pole, in the air or on the ground (level 3 also needs the boss defeated)
- End-flag rule: no entities are spawned to the right of the end flag in stage data

## Requirements

- Python 3.10+
- pip
- A desktop environment (or SDL-compatible runtime for Pygame)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Alternative launcher:

```bash
./run.sh
```

## Controls

### Global / Menu

- `Up` / `Down`: navigate menu
- `Enter` / `Space`: confirm
- `1` / `2` / `3` / `4`: quick start level from menu
- `Esc`: back/pause/quit depending on current scene
- `F12`: save screenshot to `screenshots/`
- `F9` (in a level): save this attempt's input to `replays/` (see Playtesting)

### Levels 1-3 (Single Player)

- `Left` / `Right`: move
- `Up`: jump
- `S`: shoot when boss is inside activation range; projectile direction follows player facing (`left`/`right`)

### Level 4 (Two Players)

- `P1`: `W` / `A` / `D`
- `P2`: `Up` / `Left` / `Right`

## Project Structure

```text
ShadowMarioPython/
├── main.py                    # Primary entrypoint (script)
├── run.sh                     # Convenience launcher
├── requirements.txt
├── requirements-dev.txt       # Dev tooling (ruff, pytest)
├── Makefile                   # Unified local checks
├── res/                       # Assets and runtime data
│   ├── app.properties
│   ├── message_en.properties
│   ├── level1.csv ... level4.csv
│   ├── runtime_config.json
│   └── sounds/
├── shadow_mario/
│   ├── app.py                 # Canonical runtime loop
│   ├── app_context.py         # Shared injected services
│   ├── scene_payloads.py      # Typed transition payloads
│   ├── level.py               # Gameplay façade
│   ├── level_components.py    # Level collaborators
│   ├── storage.py             # Where saves live: user data folder or localStorage
│   ├── simulation.py          # Fixed-timestep clock, input recording and replay
│   ├── input.py               # Recordable per-tick key state
│   ├── telemetry.py           # Local playtest event log
│   ├── scenes/                # Scene implementations
│   └── entities/              # Game entities
├── tools/
│   ├── build_web.sh           # Browser (pygbag) bundle from a clean copy
│   ├── web_smoke.py           # Boot the bundle and the itch.io zip in headless Chromium
│   ├── make_replays.py        # Regenerate tests/replays/
│   ├── replay.py              # Watch a saved attempt
│   └── playtest_report.py     # Telemetry summary and per-level heatmaps
├── docs/                      # FEEL_AUDIT, PLAYTEST, ASSETS, screenshots
├── tests/                     # incl. tests/replays/ reference runs
└── .github/workflows/
    ├── ci.yml                 # Checks on 3.10/3.12, web build + browser boot
    └── deploy-itch.yml        # Manual deploy to itch.io
```

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run all checks:

```bash
make check
```

Individual commands:

```bash
make lint
make test
make typecheck
```

### Simulation, replays and frame rate

The level runs at a fixed 60 ticks per second whatever the display frame rate
(`shadow_mario/simulation.py`), and every random choice comes from a per-level
seed, so a recorded input sequence always replays to the same result.
`tests/replays/level1-4.json` are reference runs that CI plays back at 30, 60
and 144 fps. If you change how a level plays on purpose, regenerate them and
say why in the commit:

```bash
python tools/make_replays.py
```

### Web build

```bash
pip install pygbag==0.9.3 playwright && python -m playwright install chromium-headless-shell
tools/build_web.sh          # build/web/ and build/web.zip, from a clean copy of the game
python tools/web_smoke.py   # boots build/web and the itch.io zip in headless Chromium
```

CI runs both on every push and keeps `web.zip` as an artifact. Publishing to
itch.io is the manual `Deploy web build to itch.io` workflow.

### Playtesting

Desktop runs log hits, deaths and level outcomes locally to
`telemetry/events.jsonl` (nothing is sent anywhere; `SHADOW_MARIO_TELEMETRY=0`
turns it off). After a session:

```bash
python tools/playtest_report.py             # summary + per-level heatmaps in telemetry/report/
python tools/replay.py replays/<file>.json  # rewatch an attempt saved with F9
```

The test script and record sheet are in [docs/PLAYTEST.md](docs/PLAYTEST.md);
[docs/FEEL_AUDIT.md](docs/FEEL_AUDIT.md) records what was measured and changed,
and [docs/ASSETS.md](docs/ASSETS.md) where each asset came from.

## Troubleshooting

- Pygame display init errors:
  - Ensure a valid desktop/SDL environment is available.
- No sound:
  - Check OS mixer/device settings and `Settings` scene mute/volume values.
- Where is my save?
  - macOS `~/Library/Application Support/ShadowMario/save.json`, Windows `%APPDATA%\ShadowMario\save.json`, Linux `~/.local/share/shadow-mario/save.json`; set `SHADOW_MARIO_DATA_DIR` to use another folder. In the browser it is in `localStorage` (key `shadowmario/save.json`).
  - A `save.json` from before October 2026 (in the project folder) is copied there on first run and left in place.
- Corrupted save:
  - The game moves an unreadable save aside as `save.json.corrupt` and starts fresh; nothing is overwritten. Delete the save to reset.

## Documentation

- Chinese version: [README_CN.md](README_CN.md)

## License

MIT. See [LICENSE](LICENSE).
