# Shadow Mario

A 2D platformer game built with Python + Pygame. Control the character through three levels, collect coins, dodge enemies, defeat the boss, and reach the end flag.

## Requirements

- Python 3.11+
- Pygame 2.5.0+

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

## Controls

| Key | Action |
|-----|--------|
| `←` / `→` | Move left / right |
| `↑` | Jump |
| `S` | Shoot fireball (Level 3 boss fight only) |
| `1` / `2` / `3` | Select level |
| `ESC` | Quit game |
| `Space` | Return to main menu |

## Game Mechanics

- **Three Levels**: tutorial level → flying platform challenge → boss fight
- **Power-ups**: Invincibility (immune to damage) and Double Score (2x coin value), lasting ~8 seconds
- **Boss Fight**: The boss shoots fireballs when the player is more than 500 pixels away; fight back with your own fireballs
- **Win/Lose**: Lose when health reaches zero or you fall off-screen; win by defeating the boss and touching the end flag

## Project Structure

```
ShadowMarioPython/
├── res/                    # Game assets
│   ├── app.properties      # Game parameters
│   ├── level1.csv          # Level 1 data
│   ├── level2.csv          # Level 2 data
│   ├── level3.csv          # Level 3 data
│   ├── *.png               # Sprites
│   └── FSO8BITR.TTF        # Pixel font
├── shadow_mario/
│   ├── main.py             # Game entry, state machine
│   ├── config.py           # Config loader
│   ├── level.py            # Level manager
│   ├── io_utils.py         # CSV/properties reader
│   └── entities/           # Game entities
│       ├── player.py       # Player character
│       ├── platform.py     # Normal platform
│       ├── flying_platform.py  # Flying platform
│       ├── enemy.py        # Normal enemy
│       ├── enemy_boss.py   # Boss
│       ├── coin.py         # Coin
│       ├── power_up.py     # Power-up base
│       ├── invincible_power.py  # Invincibility
│       ├── double_score_power.py # Double score
│       ├── fireball.py     # Fireball
│       └── end_flag.py     # End flag
├── requirements.txt
├── run.sh
├── README.md               # Chinese version
└── README_EN.md            # This file
```
