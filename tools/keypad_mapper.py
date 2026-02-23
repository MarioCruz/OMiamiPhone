from machine import Pin
import utime

# 3x4 phone keypad: 8 wires on GP0..GP7
# We don't know the exact row/col split, so let's try different combos.
# Most common: rows on first 4, cols on last 4 (one col unused)
# But could also be rows on last 4, cols on first 4.

# Let's try: 4 rows on GP0-3, 4 cols on GP4-7
rows = [Pin(gp, Pin.IN, Pin.PULL_UP) for gp in [0, 1, 2, 3]]
cols = [Pin(gp, Pin.OUT) for gp in [4, 5, 6, 7]]

for c in cols:
    c.value(1)


def scan():
    for ci, c in enumerate(cols):
        c.value(0)
        utime.sleep_us(200)
        for ri, r in enumerate(rows):
            if r.value() == 0:
                c.value(1)
                return (ri, ci)
        c.value(1)
    return None


def wait_release():
    while True:
        pressed = False
        for ci, c in enumerate(cols):
            c.value(0)
            utime.sleep_us(200)
            for ri, r in enumerate(rows):
                if r.value() == 0:
                    pressed = True
            c.value(1)
        if not pressed:
            return
        utime.sleep_ms(20)


keymap = {}
print("=== Phone Keypad Mapper ===")
print("Press a key on the keypad, then type what it is (0-9, *, #).")
print("Type 'done' when finished.\n")

while True:
    print(">> Press a key on the keypad...")
    hit = None
    while hit is None:
        hit = scan()
        utime.sleep_ms(20)

    print("   Detected position:", hit)
    wait_release()

    label = input("   What key is that? > ").strip()
    if label.lower() == "done":
        break

    keymap[hit] = label
    print("   Mapped {} -> '{}'\n".format(hit, label))

print("\n=== Your Keymap ===")
max_r = max(k[0] for k in keymap) + 1 if keymap else 0
max_c = max(k[1] for k in keymap) + 1 if keymap else 0
result = "KEYMAP = [\n"
for r in range(max_r):
    row = [keymap.get((r, c), '?') for c in range(max_c)]
    line = "    {},".format(row)
    print(line)
    result += line + "\n"
result += "]\n"
print("]")

with open("keymap.py", "w") as f:
    f.write(result)
print("\nSaved to keymap.py on the Pico!")
