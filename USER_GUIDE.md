# Poetry Phone — User Guide

This guide is for the team helping deploy and maintain the Poetry Phone. It covers how to manage audio files on the SD card, add phone numbers to the phonebook, and update the random poem collection.

## What You Need

- The microSD card from the DFPlayer module
- A computer with an SD card reader (or USB adapter)
- A text editor for editing `phonebook.json`
- Audio files in MP3 format (mono, 44.1kHz, 128kbps recommended)

## SD Card Overview

The SD card has three folders:

```
SD Card/
├── 01/    ← Sound effects (dial tone, DTMF, etc.) — DON'T TOUCH
├── 02/    ← Poems mapped to specific phone numbers
└── 03/    ← Random poems (played for unknown numbers)
```

The DFPlayer reads files by the **3-digit number** at the start of the filename. Everything after that is just a label for humans. For example, `001_dialtone.mp3` — the player sees "001", you see "dialtone".

---

## Adding a Poem to a Specific Phone Number

This is a two-step process: add the audio file to the SD card, then add the number to the phonebook.

### Step 1: Add the audio file to /02/

1. Look at what's already in the `/02/` folder and find the next available number
2. Name your file with a 3-digit prefix: `005_my_poem.mp3`
3. Copy it into `/02/`

Example — if `/02/` currently has:
```
001_8675309.mp3
002_5551212.mp3
003_5554321.mp3
004_1234567.mp3
```

Your new file would be `005_whatever_you_want.mp3`.

### Step 2: Add the number to phonebook.json

Open `phonebook.json` in any text editor. It looks like this:

```json
{
  "8675309": {"file": 1, "title": "Jenny, I got your number!"},
  "5551212": {"file": 2, "title": "Directory assistance"},
  "5554321": {"file": 3, "title": "Goodbye, friend!"},
  "1234567": {"file": 4, "title": "Hello, world!"}
}
```

Add a new line for your number. The `file` value must match the 3-digit prefix on the SD card (without leading zeros):

```json
{
  "8675309": {"file": 1, "title": "Jenny, I got your number!"},
  "5551212": {"file": 2, "title": "Directory assistance"},
  "5554321": {"file": 3, "title": "Goodbye, friend!"},
  "1234567": {"file": 4, "title": "Hello, world!"},
  "5550199": {"file": 5, "title": "My New Poem"}
}
```

Important rules:
- Phone numbers are always **7 digits** (no dashes, no area code)
- Numbers **cannot start with 0**
- The `file` number matches the 3-digit prefix on the SD card (001 = file 1, 005 = file 5)
- Don't forget the comma after the previous line when adding a new entry
- The last entry does NOT have a comma after it
- The `title` is just for your reference — it shows up in debug logs

### Step 3: Update the 411 directory listing

The 411 recording tells callers which numbers are available. After changing the phonebook, regenerate it:

```bash
# First time only: set up the virtual environment
python3 -m venv venv
source venv/bin/activate
pip install gTTS

# Every time after updating phonebook.json:
source venv/bin/activate
python tools/generate_411.py
```

Then copy the updated file (`sd_card/01/020_411.mp3`) to the `/01/` folder on the SD card.

### Step 4: Deploy the updated phonebook

Copy the updated `phonebook.json` to the Pico:

```bash
mpremote connect /dev/cu.usbmodem1101 cp phonebook.json :phonebook.json
```

Then reboot the Pico (unplug/replug) or run:

```bash
mpremote connect /dev/cu.usbmodem1101 reset
```

---

## Adding Random Poems (Unknown Numbers)

When someone dials a number that's NOT in the phonebook, the phone plays a random poem from the `/03/` folder. This is a great way to surprise people.

### Step 1: Add audio files to /03/

Name them with sequential 3-digit prefixes:

```
03/
├── 001_not_in_service.mp3
├── 002_wrong_number.mp3
├── 003_surprise_poem.mp3
├── 004_another_poem.mp3
└── 005_one_more.mp3
```

### Step 2: Update the count in config.py

Open `config.py` and find this line:

```python
RANDOM_COUNT = 1          # How many files in /03/ (update as you add more)
```

Change the number to match how many files are in `/03/`:

```python
RANDOM_COUNT = 5          # How many files in /03/ (update as you add more)
```

### Step 3: Deploy the updated config

```bash
mpremote connect /dev/cu.usbmodem1101 cp config.py :config.py
```

Then reboot the Pico.

---

## Removing a Poem

1. Delete the file from `/02/` on the SD card (or just leave it — unused files don't hurt)
2. Remove the line from `phonebook.json`
3. Regenerate the 411 listing (`python tools/generate_411.py`) and copy to SD card
4. Deploy the updated phonebook

Don't renumber the remaining files. Gaps are fine — the DFPlayer doesn't care.

---

## Replacing a Poem

Just overwrite the file on the SD card with a new one using the same 3-digit prefix. No need to change `phonebook.json` if the number stays the same.

---

## Audio File Tips

- Format: MP3, mono, 44.1kHz, 128kbps works great
- Keep poems under 5 minutes — people won't stand there longer
- Normalize audio levels so poems aren't wildly different volumes
- Test on the actual phone earpiece — it sounds different than headphones
- Free tools: Audacity (record + export), FFmpeg (convert)

---

## macOS Warning

After copying files to the SD card on a Mac, always run this before ejecting:

```bash
dot_clean /Volumes/YOUR_SD_CARD_NAME
```

macOS creates hidden `._` files that confuse the DFPlayer. This command removes them.

---

## Special Dialing Codes

These short codes work without dialing a full 7-digit number:

| Code | What happens |
|------|-------------|
| `0` | Operator message |
| `305` | O Miami! |
| `311` | City services |
| `411` | Directory assistance (lists all available numbers) |
| `611` | Service message |
| `711` | Service message |
| `811` | Service message |
| `911` | Service message |

Callers can also dial 10 digits (with any area code) — the phone strips the first 3 digits and looks up the remaining 7.

---

## Folder 01 — Don't Touch

The `/01/` folder contains sound effects (dial tone, DTMF tones, busy signal, etc.). These are generated by the build scripts and shouldn't need to change. If something sounds wrong, re-generate them:

```bash
source venv/bin/activate
pip install numpy scipy    # first time only
python tools/generate_tones.py
```

Then copy the `/01/` folder back to the SD card.

---

## Quick Reference

| Task | What to do |
|------|-----------|
| Add a poem to a number | Put MP3 in `/02/`, add line to `phonebook.json`, regenerate 411, deploy |
| Add a random poem | Put MP3 in `/03/`, update `RANDOM_COUNT` in `config.py`, deploy |
| Remove a poem | Delete line from `phonebook.json`, regenerate 411, deploy |
| Replace a poem | Overwrite the MP3 on SD card (keep same filename prefix) |
| Update 411 listing | Run `python tools/generate_411.py`, copy `sd_card/01/020_411.mp3` to SD card |
| Change volume | Edit `VOLUME` in `config.py` (0-30), deploy |
| Test without hardware | Set `HOOK_ENABLED = False` and `AUDIO_ENABLED = False` in `config.py` |

## Deploy Cheat Sheet

Close Thonny first (it locks the serial port).

```bash
# Push phonebook
mpremote connect /dev/cu.usbmodem1101 cp phonebook.json :phonebook.json

# Push config
mpremote connect /dev/cu.usbmodem1101 cp config.py :config.py

# Push main program
mpremote connect /dev/cu.usbmodem1101 cp poetry_phone.py :main.py

# Reboot
mpremote connect /dev/cu.usbmodem1101 reset
```

If the port is busy, unplug and replug the Pico's USB cable.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No sound | Check `AUDIO_ENABLED = True` in config.py. Check SD card is inserted. Check volume isn't 0. Check DFPlayer has 5V power (VBUS, not 3V3). |
| Wrong poem plays | Check that the `file` number in phonebook.json matches the 3-digit prefix on the SD card |
| Poems cut off early | Check that DFPlayer BUSY pin is wired to GP16. Check `BUSY_PIN_ENABLED = True` in config.py. |
| Bottom row keys (*, 0, #) act weird | This is normal — they need extra debounce. The code handles it. If it's really bad, check the keypad wiring. |
| "mpremote: failed to access" | Close Thonny or any other serial monitor. If still stuck, unplug/replug the Pico. |
| DFPlayer not responding | Check wiring: GP20 TX→RX (via 1K resistor), GP21 RX←TX, GP16←BUSY. Make sure it's getting 5V from VBUS, not 3.3V. |
| Poems sound too quiet/loud | Adjust `VOLUME` in config.py (0-30). 20 is a good starting point. |
| SD card not reading | Must be FAT32, ≤32GB. On Mac, run `dot_clean` after copying files. |
