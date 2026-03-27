from machine import Pin
import utime

# Try every combination of GP0-GP7 to find which pins connect
GPIOS = [0, 1, 2, 3, 4, 5, 6, 7,8 ,9,10, 16]

print("=== Keypad Probe ===")
print("Press and HOLD a key, then hit Enter here...")
input()

print("Scanning all pin pairs...")
for out_gp in GPIOS:
    out_pin = Pin(out_gp, Pin.OUT)
    out_pin.value(0)  # drive low
    utime.sleep_us(500)
    for in_gp in GPIOS:
        if in_gp == out_gp:
            continue
        in_pin = Pin(in_gp, Pin.IN, Pin.PULL_UP)
        utime.sleep_us(200)
        if in_pin.value() == 0:
            print("  GP{} (out) -> GP{} (in) = CONNECTED".format(out_gp, in_gp))
    out_pin.value(1)
    # reset all to input
    Pin(out_gp, Pin.IN)

print("\nDone! Press more keys and run again to map them all.")



