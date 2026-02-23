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
| `generate_tones.py` | No | Desktop script to generate sound effects |
| `SPEC.md` | No | Full hardware/software specification |
| `SHOPPING.md` | No | Shopping list (extracted from SPEC.md) |
| `test/` | No | 143 pytest tests with MicroPython mock framework |
| `hardware_test/` | No | Hardware validation scripts (dfplayer_test.py, hook_test.py) |
| `utils/` | No | Keypad discovery tools from initial build |

## Test Suite

Run tests: `pytest test/ -v`

143 tests across 5 test files. Mock framework in `test/mock_micropython.py` uses AST parser to avoid MicroPython imports.

## Keypad Wiring

- Columns (outputs): GP0, GP1, GP2
- Rows (inputs, pull-up): GP6 (top), GP5, GP4, GP3 (bottom)
- Bottom row (GP3: *, 0, #) is noisy — needs aggressive debounce
- Debounce: 5 stable reads to accept, 10 clean reads + 100ms to release

## DFPlayer Notes

- Library: redoxcode/micropython-dfplayer (single file `dfplayer.py`)
- `is_playing()` returns file number (not bool) — check `== 0` for stopped, `-1` for error
- UART1: TX on GP8 (via 1K resistor), RX on GP9
- Built-in amp drives 8-ohm phone earpiece directly
- SD card must be FAT32, ≤32GB
- File naming: DFPlayer reads 3-digit prefix, ignores the rest (e.g., `001_dialtone.mp3`)
- On macOS, run `dot_clean /Volumes/<SDCard>` after copying to SD card

## Hardware Status

- Keypad: wired and working (GP0-GP6)
- DFPlayer: code ready, not yet physically wired
- Hook switch: code ready, not yet physically wired
- SD card: file structure defined, generate with `python generate_tones.py`

## Keypad Discovery (Historical)

Used `keypad_probe.py` to brute-force every pin pair. Results:

| Key | Pin A | Pin B |
|-----|-------|-------|
| 0   | GP1   | GP3   |
| 1   | GP0   | GP6   |
| 2   | GP1   | GP6   |
| 3   | GP2   | GP6   |
| 4   | GP0   | GP5   |
| 7   | GP0   | GP4   |
| *   | GP0   | GP3   |

## What Didn't Work

- 7-pin config (GP0–GP6) — lost the bottom row entirely
- Simple debounce (single clean read) — bottom row keys fired multiple times
- `mpremote run` with timeout — leaves serial port locked, need unplug/replug
