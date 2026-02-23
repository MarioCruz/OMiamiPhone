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
    count = 0
    last = None
    while True:
        hit = raw_scan()
        if hit is not None and hit == last:
            count += 1
            if count >= 5:
                return KEYMAP[hit[0]][hit[1]]
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


print("=== Phone Keypad ===")
print("Type a number, press # to submit, * to clear\n")

number = ""
while True:
    key = get_key()
    wait_release()

    if key == '#':
        if number:
            print(">>> You dialed: {}".format(number))
        number = ""
    elif key == '*':
        number = ""
        print("[cleared]")
    else:
        number += key
        print(number)
