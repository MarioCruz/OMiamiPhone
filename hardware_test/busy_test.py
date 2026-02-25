"""Test DFPlayer BUSY pin on GP16. Plays a track and monitors BUSY."""
from machine import Pin, UART
import utime
import sys
sys.path.append("/")
from dfplayer import DFPlayer

busy = Pin(16, Pin.IN, Pin.PULL_UP)

print("=== BUSY Pin Test (GP16) ===\n")
print("BUSY pin before playback: {} ({})".format(
    busy.value(), "IDLE" if busy.value() == 1 else "PLAYING"))

df = DFPlayer(uart_id=1, tx_pin_id=20, rx_pin_id=21)
utime.sleep_ms(1000)
df.volume(20)
utime.sleep_ms(200)

print("\nPlaying /01/001 (dial tone)...")
df.play(1, 1)

print("Monitoring BUSY pin every 500ms for 15 seconds:\n")
print("Time(s)  BUSY  Status")
print("-------  ----  ------")

for i in range(30):
    utime.sleep_ms(500)
    val = busy.value()
    status = "IDLE" if val == 1 else "PLAYING"
    t = (i + 1) * 0.5
    print("{:5.1f}    {}     {}".format(t, val, status))

df.stop()
utime.sleep_ms(200)
print("\nAfter stop: BUSY = {} ({})".format(
    busy.value(), "IDLE" if busy.value() == 1 else "PLAYING"))
print("\nDone.")
