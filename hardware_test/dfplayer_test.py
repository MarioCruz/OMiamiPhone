"""
DFPlayer Mini hardware test — run on the Pico.

Tests:
  1. Initialize DFPlayer on UART1 (GP8 TX, GP9 RX)
  2. Set volume
  3. Play a test file from /01/001.mp3 (dial tone)
  4. Wait, then stop

Wiring:
  GP8 --[1K resistor]--> DFPlayer RX
  GP9 <----------------- DFPlayer TX
  VBUS (5V) -----------> DFPlayer VCC
  GND ------------------> DFPlayer GND
  SPK1/SPK2 ------------> Phone earpiece

Usage:
  mpremote connect /dev/cu.usbmodem1101 cp dfplayer.py :dfplayer.py
  mpremote connect /dev/cu.usbmodem1101 run hardware_test/dfplayer_test.py
"""

from machine import Pin
import utime

# Import the DFPlayer library (must be copied to Pico first)
try:
    from dfplayer import DFPlayer
except ImportError:
    print("ERROR: dfplayer.py not found on Pico!")
    print("Copy it first: mpremote cp dfplayer.py :dfplayer.py")
    raise SystemExit

print("=== DFPlayer Mini Test ===\n")

# Initialize DFPlayer on UART1
print("Initializing DFPlayer on UART1 (TX=GP8, RX=GP9)...")
df = DFPlayer(uart_id=1, tx_pin_id=8, rx_pin_id=9)
utime.sleep_ms(1000)  # DFPlayer needs ~500ms to boot
print("  OK\n")

# Set volume (0-30, start low for earpiece)
VOLUME = 15
print("Setting volume to {}...".format(VOLUME))
df.volume(VOLUME)
utime.sleep_ms(200)
print("  OK\n")

# Play dial tone (folder 01, file 001)
print("Playing /01/001.mp3 (dial tone)...")
df.play(1, 1)
print("  Playing! You should hear the dial tone in the earpiece.")
print("  Waiting 5 seconds...\n")
utime.sleep_ms(5000)

# Stop playback
print("Stopping playback...")
df.stop()
utime.sleep_ms(200)
print("  OK\n")

# Test a DTMF tone
print("Playing /01/006.mp3 (DTMF key 1)...")
df.play(1, 6)
utime.sleep_ms(500)
df.stop()
utime.sleep_ms(200)
print("  OK\n")

# Volume sweep test
print("Volume sweep (10, 15, 20, 25) with dial tone...")
for v in [10, 15, 20, 25]:
    print("  Volume: {}".format(v))
    df.volume(v)
    utime.sleep_ms(100)
    df.play(1, 1)
    utime.sleep_ms(2000)
    df.stop()
    utime.sleep_ms(300)

print("\n=== Test Complete ===")
print("Pick the volume level that sounded best for the earpiece.")
print("Update VOLUME in config.py to match.")
