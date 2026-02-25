# Poetry Phone — Hardware & Software Spec

## Context

The existing PhoneHack project proved that a 3x4 membrane keypad works with a Pico running MicroPython (`phone.py`). The next step is turning it into a **Poetry Phone**: pick up a real handset, hear a dial tone, dial a number with touch tones, hear ringing, then listen to an audio poem through the earpiece. Each phone number maps to a different poem.

---

## 1. Recommended Audio Module: DFPlayer Mini

| Factor | DFPlayer Mini | I2S DAC + SD Reader |
|--------|---------------|---------------------|
| Wiring | 4 wires (VCC, GND, TX, RX) + speaker | 7+ wires + separate SD (SPI) + external amp |
| SD card | Built-in slot | Separate breakout needed |
| Amplifier | Built-in 3W mono (drives 8-ohm directly) | Need external amp (PAM8403) |
| Formats | MP3, WAV, WMA natively | WAV only (no MP3 decode on Pico) |
| CPU load | Zero — DFPlayer handles all decoding | Heavy — Pico must stream continuously |
| Cost | ~$2-4 | ~$7+ (DAC + SD + amp) |

**Decision: DFPlayer Mini.** Built-in SD slot, built-in amp that drives the phone earpiece directly, UART control, zero CPU load so the Pico stays free for keypad scanning and hook detection.

---

## 2. GPIO Allocation

### Currently Used (Keypad — from phone.py)

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| GP0 | Keypad Column 0 | Output | Keys: 1, 4, 7, * |
| GP1 | Keypad Column 1 | Output | Keys: 2, 5, 8, 0 |
| GP2 | Keypad Column 2 | Output | Keys: 3, 6, 9, # |
| GP3 | Keypad Row 3 | Input (pull-up) | Keys: *, 0, # — noisy, needs aggressive debounce |
| GP4 | Keypad Row 2 | Input (pull-up) | Keys: 7, 8, 9 |
| GP5 | Keypad Row 1 | Input (pull-up) | Keys: 4, 5, 6 |
| GP6 | Keypad Row 0 | Input (pull-up) | Keys: 1, 2, 3 |

### New Assignments (Poetry Phone)

| GPIO | New Use | Direction | Notes |
|------|---------|-----------|-------|
| GP20 | **DFPlayer UART1 TX** | Output | Via 1K resistor to DFPlayer RX |
| GP21 | **DFPlayer UART1 RX** | Input | Direct from DFPlayer TX |
| GP22 | **Hook switch** | Input (pull-up) | HIGH = off-hook, LOW = on-hook |

**Note:** UART1 TX/RX are constrained to specific pins on the RP2040. GP20/GP21 are the UART1 pair in the GP20+ range. GP23-25 are internal (SMPS, VBUS sense, onboard LED).

### Available (GP7–GP19, GP26–GP28)

All remaining GPIOs are free for future expansion (LEDs, rotary dial, coin slot, etc.).

---

## 3. Wiring

```
Pico                              DFPlayer Mini
====                              =============
GP20 (TX) ---[1K resistor]-----> RX
GP21 (RX) <--------------------- TX
VBUS (5V) ----------------------> VCC
GND -----------------------------> GND
                                  SPK1 ----> Phone earpiece (+)
                                  SPK2 ----> Phone earpiece (-)

Hook Switch (in phone cradle)
=============================
GP22 ---+---- Hook Switch ---- GND
        |
   (internal pull-up)

Handset DOWN (on-hook): switch closed, GP22 = LOW
Handset UP (off-hook):  switch open,   GP22 = HIGH
```

---

## 4. SD Card File Organization

DFPlayer reads the **3-digit prefix** of each filename and ignores the rest.
Use descriptive suffixes so your team can manage files without a lookup table.
Case doesn't matter (FAT32 is case-insensitive). We use **lowercase with underscores**.

```
SD Card/
├── /01/                           ← Sound effects
│   ├── 001_dialtone.mp3
│   ├── 002_ringback.mp3
│   ├── 003_busy.mp3
│   ├── 004_hangup.mp3
│   ├── 005_dtmf_0.mp3
│   ├── 006_dtmf_1.mp3
│   ├── 007_dtmf_2.mp3
│   ├── 008_dtmf_3.mp3
│   ├── 009_dtmf_4.mp3
│   ├── 010_dtmf_5.mp3
│   ├── 011_dtmf_6.mp3
│   ├── 012_dtmf_7.mp3
│   ├── 013_dtmf_8.mp3
│   ├── 014_dtmf_9.mp3
│   ├── 015_dtmf_star.mp3
│   ├── 016_dtmf_hash.mp3
│   ├── 017_operator.mp3           ← Record your own
│   ├── 018_not_in_service.mp3     ← Record your own
│   ├── 019_311.mp3                ← City services
│   ├── 020_411.mp3                ← Directory assistance
│   └── 021_305_omiami.mp3         ← O Miami!
│
└── /02/                           ← Poems
    ├── 001_8675309.mp3
    ├── 002_5551212.mp3
    ├── 003_5554321.mp3
    ├── 004_1234567.mp3
    ├── 005_0000000.mp3
    └── ...
```

**Naming rule:** `{3-digit number}_{description}.mp3` — DFPlayer uses the number, humans read the description.

**macOS users:** Run `dot_clean /Volumes/<SDCard>` after copying — macOS creates hidden `._` files that confuse the DFPlayer.

---

## 5. Updated phonebook.json Format

```json
{
    "8675309": {"file": 1, "title": "Song of Jenny"},
    "5551212": {"file": 2, "title": "Directory Blues"},
    "5554321": {"file": 3, "title": "Countdown Verse"},
    "1234567": {"file": 4, "title": "Hello World Haiku"}
}
```

The `file` value maps to the file number in folder `/02/` on the SD card.

---

## 6. Sound Effects Needed

| Sound | Frequencies | Duration | File |
|-------|------------|----------|------|
| Dial tone | 350Hz + 440Hz | ~30s | 01/001 |
| Ringback | 440Hz + 480Hz, 2s on / 4s off | ~12s | 01/002 |
| Busy signal | 480Hz + 620Hz, 0.5s on / 0.5s off | ~8s | 01/003 |
| Hangup click | Short clunk | ~0.3s | 01/004 |
| DTMF 0 | 941Hz + 1336Hz | ~150ms | 01/005 |
| DTMF 1 | 697Hz + 1209Hz | ~150ms | 01/006 |
| DTMF 2 | 697Hz + 1336Hz | ~150ms | 01/007 |
| DTMF 3 | 697Hz + 1477Hz | ~150ms | 01/008 |
| DTMF 4 | 770Hz + 1209Hz | ~150ms | 01/009 |
| DTMF 5 | 770Hz + 1336Hz | ~150ms | 01/010 |
| DTMF 6 | 770Hz + 1477Hz | ~150ms | 01/011 |
| DTMF 7 | 852Hz + 1209Hz | ~150ms | 01/012 |
| DTMF 8 | 852Hz + 1336Hz | ~150ms | 01/013 |
| DTMF 9 | 852Hz + 1477Hz | ~150ms | 01/014 |
| DTMF * | 941Hz + 1209Hz | ~150ms | 01/015 |
| DTMF # | 941Hz + 1477Hz | ~150ms | 01/016 |
| Operator | Voice recording | ~3s | 01/017 |
| Not in service | Voice recording | ~4s | 01/018 |

These can be generated with Python (numpy/scipy) or downloaded as standard telephone signals.

---

## 7. Software State Machine

```
IDLE ──(off-hook)──> OFF_HOOK ──(keypress)──> DIALING ──(number complete)──> CONNECTING
  ^                                                                             |
  |                                                                    found? ──┤
  |                                                                   /         \
  |                                                              PLAYING      BUSY
  |                                                                |            |
  └──────────────────────(hangup from any state)───────────────────┘────────────┘
```

### States

- **IDLE** — Handset on cradle. Poll hook switch every 50ms. DFPlayer silent.
- **OFF_HOOK** — Play dial tone. Scan keypad for first digit. 30s timeout to busy signal.
- **DIALING** — Stop dial tone on first key. Play DTMF tone per keypress. Accumulate digits. Same timeout logic as current `phone.py`:
  - 7 digits → wait 2 seconds for more input, then submit
  - 10 digits → submit immediately (strip area code)
  - Special codes (0, 411, 911, etc.) → 1 second wait
  - `*` clears input
- **CONNECTING** — Number submitted. If found: play ringback ~5s, then transition to PLAYING. If not found: play busy signal or "not in service" recording.
- **PLAYING** — Play poem audio from `/02/`. Monitor hook switch. When poem ends, return to OFF_HOOK so user can dial again.
- **HANGUP** — On-hook detected in any state. Stop playback immediately. Return to IDLE.

### Key Design Point

The existing `raw_scan()`, `get_key()`, `get_key_timeout()`, and `wait_release()` functions stay **completely unchanged**. They are proven and handle the noisy bottom row (GP3).

---

## 8. Code Constants

```python
# Sound effect folder and file mappings
SFX_FOLDER    = 1
POEM_FOLDER   = 2

SFX_DIALTONE       = 1
SFX_RINGBACK       = 2
SFX_BUSY           = 3
SFX_HANGUP         = 4
SFX_OPERATOR       = 17
SFX_NOT_IN_SERVICE = 18

DTMF_FILE = {
    '0': 5,  '1': 6,  '2': 7,  '3': 8,
    '4': 9,  '5': 10, '6': 11, '7': 12,
    '8': 13, '9': 14, '*': 15, '#': 16,
}
```

---

## 9. Shopping List

See [SHOPPING.md](SHOPPING.md) for the full shopping list with links, search terms, and sourcing tips.

---

## 10. MicroPython Library

**[redoxcode/micropython-dfplayer](https://github.com/redoxcode/micropython-dfplayer)** — tested on Pico, simple API, single file install:

```bash
mpremote connect /dev/cu.usbmodem1101 cp dfplayer.py :dfplayer.py
```

Key API:
```python
from dfplayer import DFPlayer

df = DFPlayer(uart_id=1, tx_pin_id=20, rx_pin_id=21)
df.volume(20)                    # 0-30
df.play(folder=1, file=1)       # Play /01/001.mp3
df.stop()                        # Stop playback
df.is_playing()                  # Returns True/False
```

No other external libraries needed — `machine.Pin`, `machine.UART`, `utime`, and `json` are all built into MicroPython.

---

## 11. Files to Deploy

```
Pico filesystem:
  :main.py          ← New poetry phone state machine (refactored from phone.py)
  :dfplayer.py      ← DFPlayer library (single file)
  :phonebook.json   ← Updated with file number mappings

SD card (in DFPlayer module):
  /01/*.mp3         ← Sound effects (18 files)
  /02/*.mp3         ← Poem audio files
```

Deploy commands:
```bash
mpremote connect /dev/cu.usbmodem1101 cp dfplayer.py :dfplayer.py
mpremote connect /dev/cu.usbmodem1101 cp phonebook.json :phonebook.json
mpremote connect /dev/cu.usbmodem1101 cp phone.py :main.py
```

---

## 12. Implementation Phases

### Phase 1: Hardware Validation
1. Wire DFPlayer to Pico (GP20 TX, GP21 RX, VBUS 5V, GND)
2. Connect phone earpiece to SPK1/SPK2
3. Load a test MP3 onto SD card as `/01/001.mp3`
4. Write a minimal test script to verify sound in earpiece
5. Tune volume for comfortable earpiece listening

### Phase 2: Hook Switch
1. Wire hook switch to GP22 + GND
2. Test NC/NO behavior with multimeter
3. Write test script printing on-hook/off-hook state changes
4. Verify debounce (no false triggers)

### Phase 3: Sound Effects
1. Generate DTMF tones, dial tone, ringback, busy signal (Python + numpy or download)
2. Organize on SD card per folder structure
3. Test each sound effect via UART commands

### Phase 4: Software Integration
1. Refactor `phone.py` into state machine
2. Keep all existing keypad scanning functions unchanged
3. Add hook switch polling + DFPlayer integration at each state transition
4. Test each state transition on hardware

### Phase 5: Content
1. Record or source poetry audio files
2. Convert to MP3 (mono, 44.1kHz, 128kbps)
3. Number sequentially in `/02/`
4. Update `phonebook.json` with number-to-file mappings

### Phase 6: Polish
1. Tune volume levels (dial tone vs DTMF vs poems)
2. Tune timing (ring duration, delays between states)
3. Test edge cases: hangup mid-poem, rapid key presses, bottom row noise

---

## 13. Known Risks

| Risk | Mitigation |
|------|------------|
| DFPlayer command latency (~100-200ms) | Acceptable for phone sim; real phones had slight delay too |
| Bottom row noise (GP3: *, 0, #) | Existing aggressive debounce handles this — no changes needed |
| Hook switch bounce | 100ms debounce on on-hook detection |
| macOS hidden files on SD card | Run `dot_clean` after copying files |
| DFPlayer clone chip variations | redoxcode library handles common variants; test early |
| Rapid key presses skipping DTMF | Add 50ms delay between stop/play; non-critical if a tone is skipped |
