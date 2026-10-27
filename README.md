# Shadow Mario (Python + Pygame)

Shadow Mario is a 2D platform game built with Python and Pygame.  
The project includes four playable levels, a scene-based UI flow, audio/save systems, and effect modules (particles, shake, transitions).

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
- Scene-based architecture: menu, loading, gameplay, pause, settings, game-over
- Runtime configuration (`res/runtime_config.json`) for colors/UI/hitbox scaling
- Save system for unlock state, highscores, best times, and audio settings

## Gameplay Rules

- Level 1: tutorial-style single-player stage
- Level 2: single-layer moving-platform stage
- Level 3: dual-layer platform stage with boss combat
- Level 4: two-player race with score-based winner resolution
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
│   ├── scenes/                # Scene implementations
│   └── entities/              # Game entities
├── tests/
└── .github/workflows/ci.yml
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
- Corrupted local save:
  - Remove `save.json` and restart to regenerate defaults.

## Documentation

- Chinese version: [README_CN.md](README_CN.md)

## License

MIT. See [LICENSE](LICENSE).
