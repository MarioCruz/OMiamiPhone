"""
Generate the 411 directory assistance audio.

Uses ElevenLabs TTS (Sarah voice) to create the 411 greeting that
explains the Banana Poem Phone and hints at Easter eggs.

Usage:
    pip install requests
    python generate_411.py

Creates:
    sd_card/01/020_411.mp3

Re-run this whenever you update the Easter egg list.
"""

import os
import requests


ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not ELEVENLABS_API_KEY:
    raise SystemExit("Set ELEVENLABS_API_KEY environment variable")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

SCRIPT = (
    "4-1-1. Directory assistance. "
    "The Banana Poem Phone was created by Mario The Maker for O, Miami! "
    "Simply dial any 7-digit number, or 10-digit with area code, to hear a randomly selected poem. "
    "You never know what you'll get! "
    "Pro tip: try dialing some famous numbers for fun Easter eggs hidden throughout the experience. "
    "8-6-7-5-3-0-9... Jenny, by Tommy Tutone. "
    "5-5-5-2-3-6-8... Ghostbusters. "
    "3-1-1... non-emergency city services. "
    "6-1-1... carrier customer service. "
    "The more you dial, the more surprises you may find! "
    "Enjoy exploring the Banana Phone, and happy dialing!"
)


def main():
    print("=== 411 Directory Assistance Script ===\n")
    print(SCRIPT)
    print()

    output_dir = "sd_card/01"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/020_411.mp3"

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
