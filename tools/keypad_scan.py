from machine import Pin
import utime

# 3x4 phone keypad wiring:
#        GP0  GP1  GP2
# GP6:    1    2    3
# GP5:    4    5    6
# GP4:    7    8    9
# GP3:    *    0    #

rows = [Pin(gp, Pin.IN, Pin.PULL_UP) for gp in [6, 5, 4, 3]]
cols = [Pin(gp, Pin.OUT) for gp in [0, 1, 2]]

KEYMAP = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#'],
]

for c in cols:
    c.value(1)


def scan():
    for ci, c in enumerate(cols):
        c.value(0)
        utime.sleep_us(200)
        for ri, r in enumerate(rows):
            if r.value() == 0:
                c.value(1)
                return KEYMAP[ri][ci]
        c.value(1)
    return None


last = None
while True:
    key = scan()
    if key:
        if key != last:
            print("Key:", key)
            last = key
    else:
        last = None
    utime.sleep_ms(50)
