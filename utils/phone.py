from machine import Pin
import utime
import json

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

# Load phonebook from file
try:
    with open("phonebook.json", "r") as f:
        PHONEBOOK = json.load(f)
    print("Loaded {} numbers from phonebook.".format(len(PHONEBOOK)))
except:
    PHONEBOOK = {}
    print("No phonebook.json found, using empty phonebook.")


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
                return KEYMAP[hit[0]][hit[1]]
        else:
            count = 1 if hit is not None else 0
            last = hit
        utime.sleep_ms(10)


def get_key_timeout(timeout_ms):
    """Try to get a key within timeout. Returns key or None."""
    deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
    count = 0
    last = None
    while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
        hit = raw_scan()
        if hit is not None and hit == last:
            count += 1
            if count >= 5:
                return KEYMAP[hit[0]][hit[1]]
        else:
            count = 1 if hit is not None else 0
            last = hit
        utime.sleep_ms(10)
    return None


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


# Special short-dial numbers (handled immediately)
SPECIAL = {
    "0":   "Operator. How may I direct your call?",
    "411": "Directory assistance. What city and listing?",
    "611": "Customer service. Please hold.",
    "711": "Relay service connected.",
    "811": "Call before you dig!",
    "911": "This is 911. What is your emergency?",
    "305": "Welcome to Miami!",
}


def lookup(number):
    """Look up a number in the phonebook."""
    if number in PHONEBOOK:
        print(">>> Calling {}...".format(format_number(number)))
        print('    "{}"'.format(PHONEBOOK[number]))
    else:
        print(">>> {} - Number not in service.".format(format_number(number)))
    print()


def check_special(number):
    """Check if number matches a special code. Returns True if handled."""
    if number in SPECIAL:
        print(">>> {}".format(SPECIAL[number]))
        print()
        return True
    return False


def format_number(n):
    """Format 7 digits as xxx-xxxx."""
    if len(n) == 7:
        return "{}-{}".format(n[:3], n[3:])
    return n


# --- Main loop ---
print("=== Pico Phone ===")
print("Dial 7 digits (xxx-xxxx) or 10 digits (xxx-xxx-xxxx).")
print("Special: 0=Operator, 411=Info, 911=Emergency")
print("Press * to clear. No # needed.\n")

number = ""
while True:
    # At 10 digits, immediately look up
    if len(number) == 10:
        local = number[3:]  # strip area code
        print("(stripped area code {})".format(number[:3]))
        lookup(local)
        number = ""
        continue

    # At 7 digits, wait 2 seconds for more input
    if len(number) == 7:
        key = get_key_timeout(2000)
        if key is None:
            lookup(number)
            number = ""
            continue
        else:
            wait_release()
            if key == '*':
                number = ""
                print("[cleared]")
            elif key != '#':
                number += key
                print(number)
            continue

    # Normal input
    key = get_key()
    wait_release()

    if key == '*':
        number = ""
        print("[cleared]")
    elif key == '#':
        pass  # ignore # during dialing
    else:
        # Block leading zero on regular numbers (0 alone is operator)
        if key == '0' and len(number) == 0:
            number = "0"
            print(number)
            # Wait 1 second — if no more digits, it's the operator
            next_key = get_key_timeout(1000)
            if next_key is None:
                check_special("0")
                number = ""
            else:
                wait_release()
                if next_key == '*':
                    number = ""
                    print("[cleared]")
                elif next_key != '#':
                    # 0 followed by digit — invalid, clear
                    print("Numbers can't start with 0.")
                    number = ""
            continue

        number += key
        print(number)

        # Check for 3-digit special codes (411, 911, etc.)
        if len(number) == 3 and number in SPECIAL:
            # Wait 1 second in case they're dialing a longer number
            next_key = get_key_timeout(1000)
            if next_key is None:
                check_special(number)
                number = ""
            else:
                wait_release()
                if next_key == '*':
                    number = ""
                    print("[cleared]")
                elif next_key != '#':
                    number += next_key
                    print(number)

