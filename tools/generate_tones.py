"""
Generate all telephone sound effects for the Poetry Phone.
Outputs MP3 files organized for the DFPlayer Mini SD card.

File naming: DFPlayer reads the 3-digit prefix, ignores the rest.
So 001_dialtone.mp3 plays as file 1. The suffix is for humans.

Usage:
    pip install numpy scipy
    python generate_tones.py

Creates:
    sd_card/01/001_dialtone.mp3
    sd_card/01/002_ringback.mp3
    sd_card/01/003_busy.mp3
    sd_card/01/004_hangup.mp3
    sd_card/01/005_dtmf_0.mp3
    ...
    sd_card/01/016_dtmf_hash.mp3
    sd_card/01/017_operator.mp3
    sd_card/01/018_not_in_service.mp3
"""

import os
import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100
OUTPUT_DIR = "sd_card/01"

# DTMF frequency table (row_freq, col_freq)
DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477),
}

# File number and name assignments (must match config.py)
DTMF_FILE_MAP = {
    '0': (5, 'dtmf_0'),     '1': (6, 'dtmf_1'),
    '2': (7, 'dtmf_2'),     '3': (8, 'dtmf_3'),
    '4': (9, 'dtmf_4'),     '5': (10, 'dtmf_5'),
    '6': (11, 'dtmf_6'),    '7': (12, 'dtmf_7'),
    '8': (13, 'dtmf_8'),    '9': (14, 'dtmf_9'),
    '*': (15, 'dtmf_star'),  '#': (16, 'dtmf_hash'),
}


def make_tone(freqs, duration_s, amplitude=0.5):
    """Generate a dual-tone signal from a list of frequencies."""
    t = np.linspace(0, duration_s, int(SAMPLE_RATE * duration_s), endpoint=False)
    signal = np.zeros_like(t)
    for f in freqs:
        signal += np.sin(2 * np.pi * f * t)
    signal = signal / len(freqs) * amplitude
    return signal


def apply_envelope(signal, attack_ms=5, release_ms=5):
    """Apply a short fade-in/fade-out to avoid clicks."""
    attack_samples = int(SAMPLE_RATE * attack_ms / 1000)
    release_samples = int(SAMPLE_RATE * release_ms / 1000)
    if attack_samples > 0:
        signal[:attack_samples] *= np.linspace(0, 1, attack_samples)
    if release_samples > 0:
        signal[-release_samples:] *= np.linspace(1, 0, release_samples)
    return signal


def save_wav(filename, signal):
    """Save signal as 16-bit mono WAV."""
    signal = np.clip(signal, -1.0, 1.0)
    data = (signal * 32767).astype(np.int16)
    wavfile.write(filename, SAMPLE_RATE, data)


def save_mp3(filepath, signal):
    """Save as WAV, then convert to MP3 using ffmpeg/lame if available."""
    wav_path = filepath.replace(".mp3", ".wav")
    save_wav(wav_path, signal)

    ret = os.system(f'ffmpeg -y -i "{wav_path}" -ar 44100 -ac 1 -b:a 128k "{filepath}" -loglevel quiet 2>/dev/null')
    if ret == 0:
        os.remove(wav_path)
        return True

    ret = os.system(f'lame --quiet -m m -b 128 "{wav_path}" "{filepath}" 2>/dev/null')
    if ret == 0:
        os.remove(wav_path)
        return True

    print(f"  (kept as WAV — install ffmpeg or lame for MP3)")
    os.rename(wav_path, filepath.replace(".mp3", ".wav"))
    return False


def generate_dial_tone():
    """US dial tone: 350Hz + 440Hz, continuous."""
    name = "001_dialtone"
    print(f"{name}")
    signal = make_tone([350, 440], duration_s=30.0, amplitude=0.4)
    signal = apply_envelope(signal, attack_ms=10, release_ms=10)
    save_mp3(f"{OUTPUT_DIR}/{name}.mp3", signal)


def generate_ringback():
    """US ringback: 440Hz + 480Hz, 2s on / 4s off, ~2 rings."""
    name = "002_ringback"
    print(f"{name}")
    segments = []
    for _ in range(2):
        ring = make_tone([440, 480], duration_s=2.0, amplitude=0.4)
        ring = apply_envelope(ring, attack_ms=10, release_ms=10)
        silence = np.zeros(int(SAMPLE_RATE * 4.0))
        segments.extend([ring, silence])
    signal = np.concatenate(segments)
    save_mp3(f"{OUTPUT_DIR}/{name}.mp3", signal)


def generate_busy_signal():
    """US busy signal: 480Hz + 620Hz, 0.5s on / 0.5s off."""
    name = "003_busy"
    print(f"{name}")
    segments = []
    for _ in range(8):
        tone = make_tone([480, 620], duration_s=0.5, amplitude=0.4)
        tone = apply_envelope(tone, attack_ms=5, release_ms=5)
        silence = np.zeros(int(SAMPLE_RATE * 0.5))
        segments.extend([tone, silence])
    signal = np.concatenate(segments)
    save_mp3(f"{OUTPUT_DIR}/{name}.mp3", signal)


def generate_hangup_click():
    """Short click/clunk sound."""
    name = "004_hangup"
    print(f"{name}")
    duration_s = 0.05
    t = np.linspace(0, duration_s, int(SAMPLE_RATE * duration_s), endpoint=False)
    signal = np.sin(2 * np.pi * 120 * t) * 0.6
    signal += np.random.uniform(-0.3, 0.3, len(t))
    decay = np.exp(-t * 80)
    signal *= decay
    padding = np.zeros(int(SAMPLE_RATE * 0.2))
    signal = np.concatenate([signal, padding])
    signal = apply_envelope(signal, attack_ms=1, release_ms=1)
    save_mp3(f"{OUTPUT_DIR}/{name}.mp3", signal)


def generate_dtmf_tones():
    """Generate all 12 DTMF tones."""
    for key, (file_num, file_name) in sorted(DTMF_FILE_MAP.items(), key=lambda x: x[1][0]):
        freqs = DTMF_FREQS[key]
        name = f"{file_num:03d}_{file_name}"
        print(f"{name}  ({freqs[0]}Hz + {freqs[1]}Hz)")
        signal = make_tone(list(freqs), duration_s=0.15, amplitude=0.5)
        signal = apply_envelope(signal, attack_ms=3, release_ms=3)
        min_samples = int(SAMPLE_RATE * 0.25)
        if len(signal) < min_samples:
            padding = np.zeros(min_samples - len(signal))
            signal = np.concatenate([signal, padding])
        save_mp3(f"{OUTPUT_DIR}/{name}.mp3", signal)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("sd_card/02", exist_ok=True)

    print(f"Generating sound effects in {OUTPUT_DIR}/\n")

    generate_dial_tone()
    generate_ringback()
    generate_busy_signal()
    generate_hangup_click()
    generate_dtmf_tones()

    print(f"\nDone! {len(os.listdir(OUTPUT_DIR))} files generated.")
    print(f"""
Next steps:
  1. Add poem MP3s to sd_card/02/ using this naming:
       001_8675309.mp3
       002_5551212.mp3
       003_5554321.mp3
       ...
     The 3-digit prefix must match the "file" number in phonebook.json.
     The phone number suffix is for you — DFPlayer ignores it.

  2. Add special code recordings to sd_card/01/:
       017_operator.mp3
       018_not_in_service.mp3
       019_311.mp3
       020_411.mp3
       021_305_omiami.mp3

  3. Copy both folders to your microSD card

  4. On macOS, run: dot_clean /Volumes/<SDCard>
""")


if __name__ == "__main__":
    main()
