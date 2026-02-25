"""Monitor is_playing() values during playback to debug cutoff issues."""
from machine import Pin, UART
import utime
import sys
sys.path.append("/")
from dfplayer import DFPlayer

print("=== is_playing() Monitor ===\n")

df = DFPlayer(uart_id=1, tx_pin_id=20, rx_pin_id=21)
utime.sleep_ms(1000)
df.volume(20)
utime.sleep_ms(200)

# Play 411 directory (folder 01, file 20)
print("Playing /01/020 (411 directory)...")
df.play(1, 20)

print("Monitoring is_playing() every 500ms for 30 seconds:\n")
print("Time(s)  is_playing()")
print("-------  ------------")

for i in range(60):
    utime.sleep_ms(500)
    try:
        val = df.is_playing()
    except Exception as e:
        val = "ERR: {}".format(e)
    t = (i + 1) * 0.5
    print("{:5.1f}    {}".format(t, val))

    # Stop after 30 seconds
    if t >= 30:
        break

df.stop()
print("\nDone.")
