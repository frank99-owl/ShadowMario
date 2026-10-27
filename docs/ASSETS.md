# Asset sources

Every file under `res/` the game loads, where it came from, and whether its
license allows public redistribution (itch.io, GitHub). "Unknown" means no
source is recorded anywhere in this repository or in `res/credit.txt`. Each
unknown should be confirmed or replaced before the next public release.

The image set and `credit.txt` match the `res/` folder of the Java version of
the University of Melbourne SWEN20003 project (2024 S1, Project 2), so the
images were most likely provided with the assignment.

| File | Source | License | Status |
| --- | --- | --- | --- |
| `platform.png` | Modified from artwork by Luis Zuno (@ansimuz), per `credit.txt` | ansimuz assets are typically CC0 or free for commercial use. The specific pack is not named. | Check: name the pack |
| `enemy.png` | Bonsaiheldin, per `credit.txt` | Not recorded | Check |
| `endflag.png` | UEG Productions, per `credit.txt` | Not recorded | Check |
| `FSO8BITR.TTF` | "8 bit revival" by Jeff George, per `credit.txt` | Not recorded | Check |
| `player_left.png`, `player_right.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `coin.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `background.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `enemy_boss.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `fireball.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `flying_platform.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `double_score.png`, `invincible_power.png` | Unknown (course-provided) | Unknown | **Unknown** |
| `sounds/*.wav` (11 files) | Unknown. Added in `fa3214d` (2026-04-22) with no note. All mono 44.1 kHz with round durations (0.10 s, 0.25 s, 30.0 s, ...), which suggests they were synthesised by a script. | Unknown | **Unknown**: if generated, record the generator |

If any course-provided image cannot be cleared for redistribution, replacing
it with a CC0 equivalent (for example from Kenney's asset packs) is cheaper
than confirming its provenance.
