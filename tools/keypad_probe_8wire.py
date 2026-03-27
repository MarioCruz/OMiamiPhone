from machine import Pin
import utime

# 8-wire keypad probe for the new phone
# Wires connected to: GP1-GP10 and GP16
GPIOS = [0,1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16]

print("=== 8-Wire Keypad Probe ===")
print("Pins to scan:", GPIOS)
print()
print("Hold one key at a time. Scanning every 2 seconds.")
print("Press Ctrl-C to stop.")
print()

results = []
seen = set()

while True:
    for out_gp in GPIOS:
        out_pin = Pin(out_gp, Pin.OUT)
        out_pin.value(0)
        utime.sleep_us(500)
        for in_gp in GPIOS:
            if in_gp == out_gp:
                continue
            in_pin = Pin(in_gp, Pin.IN, Pin.PULL_UP)
            utime.sleep_us(200)
            if in_pin.value() == 0:
                # Only report the lower-numbered pin as "out" to avoid duplicates
                pair = (min(out_gp, in_gp), max(out_gp, in_gp))
                if pair not in seen:
                    seen.add(pair)
                    line = "GP{} <-> GP{}".format(pair[0], pair[1])
                    print("  FOUND: " + line)
                    results.append(line)
        out_pin.value(1)
        Pin(out_gp, Pin.IN)

    utime.sleep_ms(500)

    # Save after each scan cycle
    with open("keypad_map.txt", "w") as f:
        f.write("=== 8-Wire Keypad Probe Results ===\n")
        f.write("Total unique pairs found: {}\n\n".format(len(results)))
        for i, line in enumerate(results):
            f.write("Key {}: {}\n".format(i + 1, line))
