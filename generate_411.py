"""
Generate the 411 directory assistance audio from phonebook.json.

Reads all entries and creates an MP3 that reads out each phone number
and its title, like a real directory assistance operator.

Usage:
    pip install gTTS
    python generate_411.py

Creates:
    sd_card/01/020_411.mp3

Re-run this whenever you update phonebook.json.
"""

import json
import os


def format_phone_number(number):
    """Format 7 digits as spoken words: '8675309' -> '8-6-7-5-3-0-9'."""
    return ". ".join(list(number))


def build_script(phonebook):
    """Build the 411 directory assistance script from phonebook entries."""
    lines = [
        "Directory assistance.",
        "The following numbers are available.",
    ]

    for number, entry in sorted(phonebook.items()):
        # Format as "For Jenny, I got your number, dial 8. 6. 7. 5. 3. 0. 9."
        spoken_number = format_phone_number(number)
        lines.append(
            f'For "{entry["title"]}", dial {spoken_number}.'
        )

    lines.append("For all other numbers, dial any 7 digits for a surprise.")
    lines.append("Thank you for calling.")

    return " ".join(lines)


def generate_with_gtts(text, output_path):
    """Generate MP3 using Google Text-to-Speech."""
    from gtts import gTTS
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_path)
    return True


def main():
    # Load phonebook
    with open("phonebook.json", "r") as f:
        phonebook = json.load(f)

    script = build_script(phonebook)

    print("=== 411 Directory Assistance Script ===\n")
    print(script)
    print()

    # Generate audio
    output_dir = "sd_card/01"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/020_411.mp3"

    try:
        generate_with_gtts(script, output_path)
        print(f"Generated: {output_path}")
    except ImportError:
        print("gTTS not installed. Install with: pip install gTTS")
        print("Or record the script above manually as sd_card/01/020_411.mp3")


if __name__ == "__main__":
    main()
