from machine import Pin
import utime
import config

rows = [Pin(gp, Pin.IN, Pin.PULL_UP) for gp in config.ROW_PINS]
cols = [Pin(gp, Pin.OUT) for gp in config.COL_PINS]

for c in cols:
    c.value(1)


def raw_scan():
    for ci, c in enumerate(cols):
        c.value(0)
        utime.sleep_us(200)
        for ri, r in enumerate(rows):
            if r.value() == 0:
                c.value(1)
                return (ri, ci)
        c.value(1)
    return None


def get_key():
    """Return a key only if stable for 5 consecutive reads."""
    count = 0
    last = None
    while True:
        hit = raw_scan()
        if hit is not None and hit == last:
            count += 1
            if count >= 5:
                return config.KEYMAP[hit[0]][hit[1]], hit
        else:
            count = 1 if hit is not None else 0
            last = hit
        utime.sleep_ms(10)


def wait_release():
    clean = 0
    while clean < 10:
        hit = raw_scan()
        if hit is None:
            clean += 1
        else:
            clean = 0
        utime.sleep_ms(10)
    utime.sleep_ms(100)


print("=== Keypad Test (from config.py) ===")
print("COL_PINS:", config.COL_PINS)
print("ROW_PINS:", config.ROW_PINS)
print("Press any key to see what it maps to.\n")

while True:
    key, pos = get_key()
    row_gp = config.ROW_PINS[pos[0]]
    col_gp = config.COL_PINS[pos[1]]
    print("Key: {}  |  row={} (GP{})  col={} (GP{})".format(key, pos[0], row_gp, pos[1], col_gp))
    wait_release()
