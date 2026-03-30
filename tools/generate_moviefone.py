"""
Generate the 777-3456 "Moviefone" Easter egg audio.

777-FILM was Moviefone — call for showtimes.
This version gives you poetry showtimes instead.

Uses ElevenLabs TTS (Sarah voice).

Usage:
    ELEVENLABS_API_KEY=xxx python tools/generate_moviefone.py

Creates:
    sd_card/02/005_moviefone.mp3
"""

import os
import requests


ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not ELEVENLABS_API_KEY:
    raise SystemExit("Set ELEVENLABS_API_KEY environment variable")
VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah
URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

SCRIPT = (
    "Hello, and welcome to Moviefone! "
    "If you know the name of the movie you'd like to see, press 1 now. "
    "...Just kidding. "
    "You've reached the Banana Poem Phone. We don't do movies here. We do poems. "
    "But since you've already called — "
    "Now showing: P. Scott Cunningham in... A Poet Stuck in Chicago. "
    "A documentary. One poet. One city. Zero flights home. "
    "He came for a fresh start. He stayed because the house needed work. "
    "The winters stayed because they always do. "
    "Critics are calling it... Remarkably cold. Aggressively cold. Why is he still there? "
    "Showtimes are: always. Because unlike movies, poems never stop playing. "
    "They're showing right now. In your head. See? "
    "If you'd like to hear an actual poem instead of a fake movie listing, "
    "hang up and dial any seven-digit number. "
    "Why are you still listening to this? "
    "Go hear a poem. "
    "Thank you for calling Poemafone — a service of O, Miami. "
    "No refunds. No concessions. Unlimited poems."
)


def main():
    print("=== 777-3456 Moviefone Script ===\n")
    print(SCRIPT)
    print()

    output_dir = "sd_card/02"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/005_moviefone.mp3"

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
