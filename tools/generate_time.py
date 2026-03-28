"""
Generate the 324-8811 "Poetry Time" Easter egg audio.

324-8811 was Miami's old time-of-day phone number.
This version gives you "poetry time" instead.

Uses ElevenLabs TTS (Sarah voice).

Usage:
    pip install requests
    ELEVENLABS_API_KEY=xxx python tools/generate_time.py

Creates:
    sd_card/02/004_poetry_time.mp3
"""

import os
import requests


ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not ELEVENLABS_API_KEY:
    raise SystemExit("Set ELEVENLABS_API_KEY environment variable")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

SCRIPT = (
    "At the tone, the time will be... "
    "poetry o'clock. "
    "It is always poetry o'clock. "
    "The minutes are made of metaphor. "
    "The hours are held together by rhythm. "
    "And somewhere in Miami, a banana phone is ringing. "
    "If you are hearing this, you are exactly on time. "
    "You are never early, never late, for a poem. "
    "This has been a public service announcement from the Banana Poem Phone and O'Miami. "
    "Please set your watches to wonder."
)


def main():
    print("=== 324-8811 Poetry Time Script ===\n")
    print(SCRIPT)
    print()

    output_dir = "sd_card/02"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/004_poetry_time.mp3"

    print(f"Generating {output_path} via ElevenLabs (Sarah)...")
    resp = requests.post(
        URL,
        headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
        json={
            "text": SCRIPT,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.4},
        },
    )
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"Generated: {output_path} ({len(resp.content)} bytes)")
    else:
        print(f"Error {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    main()
