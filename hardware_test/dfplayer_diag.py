"""
DFPlayer Mini diagnostic — run on the Pico.

Checks UART communication, SD card detection, and audio output step by step.
Prints detailed results so you can identify what's wrong.

Wiring:
  GP20 --[1K resistor]--> DFPlayer RX
  GP21 <------------------ DFPlayer TX
  VBUS (5V) -----------> DFPlayer VCC
  GND ------------------> DFPlayer GND
  SPK1/SPK2 ------------> Phone earpiece (or small speaker)

Usage:
  mpremote connect /dev/cu.usbmodem1101 run hardware_test/dfplayer_diag.py
"""

from machine import UART, Pin
import utime

print("=" * 40)
print("DFPlayer Mini Diagnostic")
print("=" * 40)

# --- Step 1: Raw UART test ---
print("\n[1/5] Testing UART connection on GP20 TX, GP21 RX...")
uart = UART(1, baudrate=9600, tx=Pin(20), rx=Pin(21))
utime.sleep_ms(500)

# Send a "get status" query (DFPlayer command 0x42)
# Format: 0x7E 0xFF 0x06 CMD 0x00 PAR1 PAR2 CHECKSUM_HI CHECKSUM_LO 0xEF
# CMD 0x42 = get current status
cmd = bytearray([0x7E, 0xFF, 0x06, 0x42, 0x00, 0x00, 0x00, 0xFE, 0xB9, 0xEF])
uart.write(cmd)
utime.sleep_ms(500)

response = uart.read()
if response:
    print("  UART response: {}".format(response.hex()))
    print("  >> DFPlayer is responding on UART!")
else:
    print("  No UART response!")
    print("  >> Check wiring:")
    print("     - GP20 (Pico TX) -> DFPlayer RX (via 1K resistor)")
    print("     - GP21 (Pico RX) -> DFPlayer TX (direct)")
    print("     - VCC -> VBUS (5V), not 3.3V")
    print("     - GND -> GND")
    print("     - Is the DFPlayer powered? LED should blink on power-up.")

# --- Step 2: Try the library ---
print("\n[2/5] Loading DFPlayer library...")
try:
    from dfplayer import DFPlayer
    print("  Library loaded OK")
except ImportError:
    print("  ERROR: dfplayer.py not on Pico!")
    print("  Run: mpremote cp dfplayer.py :dfplayer.py")
    raise SystemExit

print("\n[3/5] Initializing DFPlayer...")
# Re-init with clean UART through library
df = DFPlayer(uart_id=1, tx_pin_id=20, rx_pin_id=21)
utime.sleep_ms(1000)  # DFPlayer needs time to boot
print("  Init complete")

# --- Step 3: Set volume and check ---
print("\n[4/5] Setting volume to 25 (out of 30)...")
df.volume(25)
utime.sleep_ms(200)
print("  Volume set")

# --- Step 4: Try playing ---
print("\n[5/5] Playing test sounds...")

# Try folder 01, file 001 (dial tone)
print("\n  Playing /01/001 (dial tone) for 3 seconds...")
df.play(1, 1)
utime.sleep_ms(200)

# Check if playing
status = df.is_playing()
print("  is_playing() = {} (0=stopped, >0=file#, -1=error)".format(status))

if status == 0:
    print("  >> Not playing! Possible causes:")
    print("     - SD card not inserted or not FAT32")
    print("     - No file at /01/001_*.mp3")
    print("     - Speaker not connected to SPK1/SPK2")
elif status == -1:
    print("  >> Error from DFPlayer!")
    print("     - Check SD card format (must be FAT32, <=32GB)")
    print("     - Run dot_clean if copied from Mac")
else:
    print("  >> Playing file #{}!".format(status))

print("  Waiting 3 seconds (you should hear the dial tone)...")
utime.sleep_ms(3000)
df.stop()
utime.sleep_ms(200)

# Try a DTMF tone (shorter, louder)
print("\n  Playing /01/006 (DTMF key 1) for 1 second...")
df.play(1, 6)
utime.sleep_ms(1000)
df.stop()
utime.sleep_ms(200)

# Try folder 03 random poem
print("\n  Playing /03/001 (first random poem) for 3 seconds...")
df.play(3, 1)
utime.sleep_ms(200)
status = df.is_playing()
print("  is_playing() = {}".format(status))
utime.sleep_ms(3000)
df.stop()

# --- Summary ---
print("\n" + "=" * 40)
print("Diagnostic complete.")
print("")
print("If you heard nothing at all:")
print("  - Check speaker wiring (SPK1/SPK2)")
print("  - Try a different speaker or earbuds")
print("  - Check volume (we set it to 25)")
print("")
print("If UART responded but no audio:")
print("  - SD card may not be inserted")
print("  - SD card may need FAT32 format")
print("  - Files may be missing from /01/")
print("  - On Mac, run: dot_clean /Volumes/TEST")
print("")
print("If nothing responded:")
print("  - Check all 4 wires (TX, RX, VCC, GND)")
print("  - DFPlayer needs 5V (VBUS), not 3.3V")
print("  - Try swapping TX/RX wires")
print("=" * 40)
