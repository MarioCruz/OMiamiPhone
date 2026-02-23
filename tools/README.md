# Tools — Desktop Scripts

Everything in this folder runs on your Mac/PC, **not** on the Pico. These are generators, discovery tools, and earlier iterations of the keypad code from the initial build.

## Audio Generators

| Script | What it does |
|--------|-------------|
| `generate_tones.py` | Generates all telephone sound effects (dial tone, ringback, busy signal, hangup click, DTMF tones) as MP3 files in `sd_card/01/`. Requires `numpy` and `scipy`. |
| `generate_411.py` | Reads `phonebook.json` and generates a 411 directory assistance recording using Google Text-to-Speech. Lists every available phone number and its title. Re-run whenever you update the phonebook. Requires `gTTS`. |

### Usage

```bash
python3 -m venv venv
source venv/bin/activate
pip install numpy scipy gTTS
python tools/generate_tones.py
python tools/generate_411.py
```

## Keypad Discovery Tools

These were used during the initial build to figure out how the 3x4 membrane keypad was wired. They run on the Pico via `mpremote run` but are kept here for reference since they're not part of the deployed phone.

| Script | What it does |
|--------|-------------|
| `keypad_probe.py` | Brute-force pin discovery. Tries every pair of GP0-GP7 while you hold a key down. This is how we figured out which pins were columns and which were rows. |
| `keypad_scan.py` | Basic scanner using the confirmed wiring (cols: GP0-2, rows: GP6-3). Prints key presses to the console. First working scan after probe results. |
| `keypad_mapper.py` | Experimental scanner that tried alternative row/column splits (rows on GP0-3, cols on GP4-7). Didn't work — kept here as a record of what we tried. |
| `keypad_test.py` | Simple test harness for validating the `raw_scan()` function in isolation. Used for debugging the bottom row noise on GP3. |

## Earlier Phone Iterations

These are previous versions of the phone code, before `poetry_phone.py` became the main app.

| Script | What it does |
|--------|-------------|
| `keypad_dialer.py` | Added dialing on top of keypad scanning. Had a hardcoded phonebook (`"123"` -> `"Hello!"`). First proof that multi-digit input worked. |
| `keypad_phone.py` | Upgraded to loading `phonebook.json` from the filesystem. Added graceful handling for missing phonebook. |
| `phone.py` | Final pre-DFPlayer version. Full debounce logic, JSON phonebook, 7/10 digit dialing, special codes. This code's keypad scanning was carried forward unchanged into `poetry_phone.py`. |

## What's NOT here

- **Pico code** — `poetry_phone.py`, `config.py`, `dfplayer.py`, `phonebook.json` live in the project root
- **Hardware tests** — `hardware_test/` has scripts that test DFPlayer and hook switch wiring on the actual Pico
- **Unit tests** — `test/` has 144 pytest tests that run on desktop with mocked MicroPython
