# Poetry Phone — Project Notes

## Project Overview

Art installation phone for O Miami poetry festival. Dial a number on a real phone keypad, hear ringing, then listen to a poem through the earpiece. Built on Raspberry Pi Pico + DFPlayer Mini + salvaged phone handset.

## Repo

- GitHub: https://github.com/MarioCruz/OMiamiPhone
- Initial commit: Mario only (no co-author)
- All subsequent commits: Mario + Claude co-author

## Pico Connection

- `mpremote` v1.27.0 installed via Homebrew
- Pico at `/dev/cu.usbmodem1101`, device ID `e660c062136d6e27`
- Close Thonny before using mpremote (port conflict)
- `mpremote run` holds the serial port — unplug/replug Pico to release

## GPIO Wiring

- Keypad columns (outputs): GP0, GP1, GP2
- Keypad rows (inputs, pull-up): GP6 (top), GP5, GP7, GP3 (bottom)
- Hook switch: GP22 (NO switch, pull-up, LOW = on-hook, HIGH = off-hook)
- DFPlayer TX: GP20 (via 1K resistor to DFPlayer RX)
- DFPlayer RX: GP21 (direct from DFPlayer TX)
- DFPlayer BUSY: GP17 (LOW = playing, HIGH = idle)

## Deploy Commands

```bash
mpremote connect /dev/cu.usbmodem1101 cp config.py :config.py
mpremote connect /dev/cu.usbmodem1101 cp dfplayer.py :dfplayer.py
mpremote connect /dev/cu.usbmodem1101 cp phonebook.json :phonebook.json
mpremote connect /dev/cu.usbmodem1101 cp poetry_phone.py :main.py
```

To run without rebooting:
```bash
mpremote connect /dev/cu.usbmodem1101 run poetry_phone.py
```

## Pico Filesystem

Only 4 files deployed: `config.py`, `dfplayer.py`, `main.py` (from poetry_phone.py), `phonebook.json`

## File Organization

| File | Deployed | Purpose |
|------|----------|---------|
| `poetry_phone.py` | `:main.py` | Main state machine |
| `config.py` | `:config.py` | All settings (pins, timing, volume, special codes) |
| `dfplayer.py` | `:dfplayer.py` | DFPlayer Mini library (redoxcode) |
| `phonebook.json` | `:phonebook.json` | Phone number → poem mappings (4 entries) |
| `tools/` | No | Desktop scripts (generators, keypad discovery, etc.) |
| `SPEC.md` | No | Full hardware/software specification |
| `SHOPPING.md` | No | Shopping list (extracted from SPEC.md) |
| `USER_GUIDE.md` | No | How to add/remove poems and manage the SD card |
| `test/` | No | 145 pytest tests with MicroPython mock framework |
| `hardware_test/` | No | Hardware validation scripts (dfplayer_test, hook_test, busy_test, uart_probe, etc.) |
| `Poems/` | No | Original poem MP3 source files (copied to sd_card/03/ with DFPlayer naming) |

## Test Suite

Run tests: `pytest test/ -v`

145 tests across 5 test files. Mock framework in `test/mock_micropython.py` uses AST parser to avoid MicroPython imports.

## Keypad Wiring

- Columns (outputs): GP0, GP1, GP2
- Rows (inputs, pull-up): GP6 (top), GP5, GP7, GP3 (bottom)
- Bottom row (GP3: *, 0, #) is noisy — needs aggressive debounce
- Debounce: 5 stable reads to accept, 5 clean reads + 30ms to release

## DFPlayer Notes

- Library: redoxcode/micropython-dfplayer (single file `dfplayer.py`)
- `is_playing()` is BROKEN on this clone — always returns `-1`. Do NOT use it.
- **BUSY pin** (GP17) is the reliable way to detect end-of-track: LOW = playing, HIGH = idle
- All audio playback (poems, special codes, ringback) now waits for completion instead of fixed timeouts
- UART1: TX on GP20 (via 1K resistor), RX on GP21
- BUSY pin on GP17 (input with pull-up)
- Built-in amp drives 8-ohm phone earpiece directly
- DFPlayer needs 5V (VBUS) — 3V3 won't work
- SD card must be FAT32, ≤32GB
- File naming: DFPlayer reads 3-digit prefix, ignores the rest (e.g., `001_dialtone.mp3`)
- On macOS, run `dot_clean /Volumes/<SDCard>` after copying to SD card

## Hardware Status

- Keypad: wired and working (GP0-GP3, GP5-GP7)
- DFPlayer: wired and working (UART1 on GP20/GP21, BUSY on GP17, 5V from VBUS)
- Hook switch: wired and working (GP22, normally-open, LOW = off-hook)
- SD card: loaded — /01/ SFX (22 files), /02/ empty (mapped poems), /03/ random poems (5 files)

## Keypad Discovery (Historical)

Used `keypad_probe.py` to brute-force every pin pair. Results:

| Key | Pin A | Pin B |
|-----|-------|-------|
| 0   | GP1   | GP3   |
| 1   | GP0   | GP6   |
| 2   | GP1   | GP6   |
| 3   | GP2   | GP6   |
| 4   | GP0   | GP5   |
| 7   | GP0   | GP7   |
| *   | GP0   | GP3   |

## What Didn't Work

- 7-pin config (GP0–GP6) — lost the bottom row entirely
- Simple debounce (single clean read) — bottom row keys fired multiple times
- `mpremote run` with timeout — leaves serial port locked, need unplug/replug
