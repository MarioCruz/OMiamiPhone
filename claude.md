# Poetry Phone — Project Notes

## Project Overview

Art installation phone: dial a number, hear a poem. Built on Raspberry Pi Pico + DFPlayer Mini + salvaged phone handset. For O Miami poetry festival.

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

## Pico Filesystem

Only 4 files deployed: `config.py`, `dfplayer.py`, `main.py` (from poetry_phone.py), `phonebook.json`

## Keypad Wiring

- Columns (outputs): GP0, GP1, GP2
- Rows (inputs, pull-up): GP6 (top), GP5, GP4, GP3 (bottom)
- Bottom row (GP3: *, 0, #) is noisy — needs aggressive debounce
- Debounce: 5 stable reads to accept, 10 clean reads + 100ms to release

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

## DFPlayer Notes

- Library: redoxcode/micropython-dfplayer (single file `dfplayer.py`)
- `is_playing()` returns file number (not bool) — check `== 0` or `== -1`
- UART1: TX on GP8 (via 1K resistor), RX on GP9
- Built-in amp drives 8-ohm phone earpiece directly
- SD card must be FAT32, ≤32GB
- File naming: DFPlayer reads 3-digit prefix, ignores the rest (e.g., `001_dialtone.mp3`)
- On macOS, run `dot_clean` after copying to SD card

## File Organization

- `poetry_phone.py` — Main app (deployed as `:main.py`)
- `config.py` — All tunables (pins, timing, volume, special codes)
- `dfplayer.py` — DFPlayer library dependency
- `phonebook.json` — Phone number → poem file mappings
- `generate_tones.py` — Desktop script to generate sound effects
- `SPEC.md` — Full hardware/software specification
- `tests/` — Hardware validation scripts (dfplayer_test.py, hook_test.py)
- `utils/` — Keypad discovery tools from initial build (phone.py, keypad_*.py)

## Reference Code

Found old CircuitPython code for same keypad on Feather RP2040:
- Used `keypad.KeyMatrix` with column_pins and row_pins
- Had DTMF tones and dial-a-song functionality
- Good reference for the full phone build
