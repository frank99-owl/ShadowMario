# Shadow Mario (Python + Pygame)

Shadow Mario is a 2D platform game built with Python and Pygame.  
The project includes four playable levels, a scene-based UI flow, audio/save systems, and effect modules (particles, shake, transitions).

## Features

- Four levels with different gameplay pacing
- Level 2/3 platform behavior aligned with classic project logic
- Level 4 two-player race mode (P1 vs P2)
- Scene-based architecture: menu, loading, gameplay, pause, settings, game-over
- Runtime configuration (`res/runtime_config.json`) for colors/UI/hitbox scaling
- Save system for unlock state, highscores, best times, and audio settings

## Gameplay Rules

- Level 1: tutorial-style single-player stage
- Level 2: dual-layer moving-platform stage
- Level 3: single-layer platform stage with boss combat
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

## Auto Deploy to itch.io

This repository includes `.github/workflows/deploy-itch.yml` for automatic itch.io uploads.

1. Add GitHub repository secret `BUTLER_API_KEY` (from your itch.io account API keys page).
2. Optional: set repository variables:
   - `ITCH_GAME` (default: `frank-owl/shadowmario`)
   - `ITCH_SOURCE_CHANNEL` (default: `source`)
   - `ITCH_WEB_CHANNEL` (default: `web`)
3. Push to `main` (or run the workflow manually from Actions).

The workflow uploads two packages on each deployment:

- Source package (`git archive`):

```bash
butler push dist/shadowmario-source.zip frank-owl/shadowmario:source
```

- Web package (`pygbag`, for browser play updates):

```bash
butler push build/web.zip frank-owl/shadowmario:web
```

## Troubleshooting

- Pygame display init errors:
  - Ensure a valid desktop/SDL environment is available.
- No sound:
  - Check OS mixer/device settings and `Settings` scene mute/volume values.
- Corrupted local save:
  - Remove `save.json` and restart to regenerate defaults.

## Documentation

- Chinese version: [README_CN.md](README_CN.md)
- Compatibility alias: [README_EN.md](README_EN.md)

## License

MIT. See [LICENSE](LICENSE).
