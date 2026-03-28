# Poetry Phone — Project Notes

## Project Overview

Art installation phone for O Miami poetry festival. Dial a number on a real phone keypad, hear ringing, then listen to a poem through the earpiece. Built on Raspberry Pi Pico + DFPlayer Mini + salvaged phone handset. Created by Mario The Maker.

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

- Keypad columns (outputs): GP6, GP5, GP7
- Keypad rows (inputs, pull-up): GP4 (top), GP2, GP1, GP0 (bottom)
- Hook switch: GP22 (NO switch, pull-up, LOW = on-hook, HIGH = off-hook)
- DFPlayer TX: GP20 (via 1K resistor to DFPlayer RX)
- DFPlayer RX: GP21 (direct from DFPlayer TX)
- DFPlayer BUSY: GP17 (LOW = playing, HIGH = idle)

## Deploy Commands

Deploy all 4 files to Pico:
```bash
mpremote connect /dev/cu.usbmodem1101 cp config.py :config.py + cp phonebook.json :phonebook.json + cp poetry_phone.py :main.py + cp dfplayer.py :dfplayer.py
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
| `phonebook.json` | `:phonebook.json` | Phone number → poem mappings (3 entries) |
| `tools/` | No | Desktop scripts (generators, keypad discovery, etc.) |
| `SPEC.md` | No | Full hardware/software specification |
| `SHOPPING.md` | No | Shopping list (extracted from SPEC.md) |
| `USER_GUIDE.md` | No | How to add/remove poems and manage the SD card |
| `test/` | No | 145 pytest tests with MicroPython mock framework |
| `hardware_test/` | No | Hardware validation scripts (dfplayer_test, hook_test, busy_test, uart_probe, etc.) |
| `OmiamiPoems/` | No | Source O'Miami poem MP3s (29 poems + index.html) |
| `sd_card/` | SD card | Full SD card image — tracked in git as backup |

## SD Card Layout

The `sd_card/` directory is the complete image of what goes on the DFPlayer's microSD card. It is tracked in git so the full phone can be recreated if the SD card is lost.

| Folder | Files | Purpose |
|--------|-------|---------|
| `/01/` | 27 | Sound effects (dial tone, DTMF, ringback, busy, operator, special codes) |
| `/02/` | 5 | Mapped poems (phonebook entries with specific numbers) |
| `/03/` | 28 | Random poems (played for any unrecognized number) |

To update the SD card:
```bash
cp sd_card/01/*.mp3 /Volumes/<SDCARD>/01/
cp sd_card/02/*.mp3 /Volumes/<SDCARD>/02/
cp sd_card/03/*.mp3 /Volumes/<SDCARD>/03/
dot_clean /Volumes/<SDCARD>
```

## Phonebook (Easter Eggs)

Numbers mapped to specific audio in `phonebook.json`:

| Number | Also via | Audio | File |
|--------|----------|-------|------|
| 867-5309 | 305-867-5309 | Jenny Munaweera poem | `/02/001` |
| 555-2368 | — | "Who are you going to call? A poet?" (Ghostbusters) | `/02/002` |
| 555-1212 | 305-555-1212 | Ericka poem (classic directory assistance) | `/02/003` |
| 324-8811 | 305-324-8811 | "Poetry Time" (Miami's old time-of-day number) | `/02/004` |
| 777-3456 | 305-777-3456 | "Poemafone" (Moviefone parody, P. Scott Cunningham) | `/02/005` |

All other 7-digit (or 10-digit with area code) numbers play a random poem from `/03/`.

## Special Codes (3-digit)

Dialing these short codes plays a dedicated SFX from `/01/`:

| Code | SFX# | Description |
|------|------|-------------|
| 0 | 17 | Operator — "This is the Banana Poem Phone..." |
| 211 | 23 | Community services — poetic Miami message |
| 311 | 19 | City services |
| 411 | 20 | Directory assistance — explains the phone, lists Easter eggs |
| 511 | 24 | Traffic — "Every road in Miami leads to the ocean..." |
| 611 | 27 | Customer service — "All representatives are busy reading poetry..." |
| 711 | 25 | Telecom relay — "Every voice deserves to be heard..." |
| 811 | 26 | Utility locator — "Call before you dig... beneath every poem, a tangle of feelings" |
| 911 | 22 | Emergency redirect — "This is not a real phone, dial 911 on a real phone" |
| 305 | 21 | O'Miami — Miami area code shoutout, credits Mario The Maker |

## Audio Generation

- **SFX voice messages** (operator, special codes): Generated with ElevenLabs TTS, Sarah voice, `eleven_multilingual_v2` model
- **Poem audio** (`OmiamiPoems/`): Generated with ElevenLabs TTS, multiple voices (Sarah, Chris, Jessica, Liam) matched by poem type and poet gender
- **Dial/DTMF tones**: Generated with `tools/generate_tones.py` (pure synthesis)
- **411 directory**: Regenerate with `tools/generate_411.py` (requires `ELEVENLABS_API_KEY` env var)
- API key is NOT stored in the repo — set `ELEVENLABS_API_KEY` env var when regenerating

## Test Suite

Run tests: `pytest test/ -v`

169 tests across 7 test files. Mock framework in `test/mock_micropython.py` uses AST parser to avoid MicroPython imports. Tests cover state machine logic, hook switch, dialing edge cases, audio sequencing, config/SD card consistency, off-hook timeout, and crash recovery.

## Keypad Wiring

- Columns (outputs): GP6, GP5, GP7
- Rows (inputs, pull-up): GP4 (top), GP2, GP1, GP0 (bottom)
- Bottom row (GP0: *, 0, #) may be noisy — needs aggressive debounce
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

- Keypad: wired and working (GP0-GP2, GP4-GP7)
- DFPlayer: wired and working (UART1 on GP20/GP21, BUSY on GP17, 5V from VBUS)
- Hook switch: wired and working (GP22, normally-open, LOW = off-hook)
- SD card: loaded — /01/ SFX (27 files), /02/ mapped poems (5 files), /03/ random poems (28 files)

## GPIO Gotchas

- **GP4/GP5 vs UART1 default pins (THE BIG BUG)**: `machine.UART(1, 9600)` without explicit `tx`/`rx` params momentarily claims GP4 and GP5 — the UART1 default pins on RP2040 — even if you call `.init()` with different pins afterward. GP4 is keypad row 0 and GP5 is keypad column 1. This caused the keypad to intermittently fail on boot: sometimes keys worked, sometimes they didn't, and manually stopping/starting the script often "fixed" it because the pins re-initialized in a different order. **Fix**: Always pass `tx=pin, rx=pin` directly in the `machine.UART()` constructor so the default pins are never touched. The dfplayer.py library was patched to do this.
- **GP4 vs UART1 alternate function**: GP4 is an alternate UART1 TX pin on RP2040. Even after fixing the constructor, GP4 can still misbehave if UART1 is initialized without explicit pins. This is why keypad row 2 was originally on GP4 and had to stay there carefully.
- **GP16 vs UART0**: GP16 had issues as BUSY pin input. Moved to GP17.
- **Non-contiguous pins**: Keypad rows use GP4, GP2, GP1, GP0 (not GP0-GP3) due to the GP4/UART1 conflict.

## Keypad Discovery (Historical)

Used `keypad_probe_8wire.py` to brute-force every pin pair on the new phone. Results:

| Key | Pin A | Pin B |
|-----|-------|-------|
| 1   | GP4   | GP6   |
| 2   | GP4   | GP5   |
| 3   | GP4   | GP7   |
| 4   | GP2   | GP6   |
| 5   | GP2   | GP5   |
| 6   | GP2   | GP7   |
| 7   | GP1   | GP6   |
| 8   | GP1   | GP5   |
| 9   | GP1   | GP7   |
| *   | GP0   | GP6   |
| 0   | GP0   | GP5   |
| #   | GP0   | GP7   |

## What Didn't Work

- 7-pin config (GP0-GP6) — lost the bottom row entirely
- Simple debounce (single clean read) — bottom row keys fired multiple times
- `mpremote run` with timeout — leaves serial port locked, need unplug/replug
- `is_playing()` on DFPlayer clone — always returns `-1`, use BUSY pin instead
- GP4 for keypad row when UART1 active — alternate function conflict on RP2040
- GP16 for BUSY pin — unreliable, moved to GP17
