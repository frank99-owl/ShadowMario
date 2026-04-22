# Shadow Mario

A 2D platform game built with Python + Pygame.  
Current build includes 4 levels, a scene-based UI flow, save/audio systems, and enhanced visual effects.

## Current Scope

- Levels 1/2/3 keep the classic GitHub movement/platform feel
- Level 2 is single-layer platform focused
- Level 3 is dual-layer platform + boss battle
- Level 4 is a two-player race mode (P1 vs P2)
- Enhanced effects are enabled: landing dust, hit particles, coin FX, boss death FX, screen shake

## Requirements

- Python 3.10+
- Pygame 2.5.0+

## Install & Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Or:

```bash
./run.sh
```

## Controls

### Menu / Global

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate menu |
| `Enter` / `Space` | Confirm |
| `1` / `2` / `3` / `4` | Quick start level from menu |
| `ESC` | Pause / Back / Quit (depends on scene) |
| `F12` | Screenshot to `screenshots/` |

### Levels 1-3 (Single Player)

| Key | Action |
|-----|--------|
| `←` / `→` | Move |
| `↑` | Jump |
| `S` | Shoot fireball (when boss is in activation range) |

### Level 4 (Two-Player Race)

| Player | Keys |
|--------|------|
| P1 | `W` / `A` / `D` |
| P2 | `↑` / `←` / `→` |

Race rules:

- Both players start with 100 HP, each enemy hit deals 25 damage
- Reaching the end flag ends the round; winner is decided by score
- If one player falls behind and leaves the visible frame, the other player wins immediately

## Systems

- Scene flow: menu, level select, loading, gameplay, pause, game over, settings
- Audio manager: BGM/SFX volume and mute control
- Save manager: level unlocks, high scores, best times, total coins
- Runtime config: `res/runtime_config.json` for UI/colors/hitbox scaling

## Project Layout

```
ShadowMarioPython/
├── main.py                    # Primary entry point (recommended)
├── run.sh                     # Convenience launcher
├── requirements.txt
├── res/
│   ├── app.properties
│   ├── message_en.properties
│   ├── level1.csv
│   ├── level2.csv
│   ├── level3.csv
│   ├── level4.csv
│   ├── runtime_config.json
│   ├── sounds/
│   └── images/fonts
├── shadow_mario/
│   ├── config.py
│   ├── level.py
│   ├── audio.py
│   ├── particles.py
│   ├── save.py
│   ├── runtime_config.py
│   ├── scenes/
│   └── entities/
├── save.json                  # generated at runtime
└── screenshots/               # F12 output
```

## Pre-upload Checklist

```bash
python3 -m py_compile main.py
python3 main.py
```

Manual checks:

- Menu can enter levels 1-4
- Platform behavior in L2/L3 feels correct
- L4 two-player race logic works as expected
- Audio and visual effects are present

## License

MIT (see `LICENSE`)
