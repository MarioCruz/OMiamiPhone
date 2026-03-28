from machine import Pin
import utime
import json
import random
import gc
import config

# =============================================================================
# Poetry Phone — State machine with DFPlayer Mini audio
# All settings live in config.py
# =============================================================================

# --- Keypad setup ---
rows = [Pin(gp, Pin.IN, Pin.PULL_UP) for gp in config.ROW_PINS]
cols = [Pin(gp, Pin.OUT) for gp in config.COL_PINS]

for c in cols:
    c.value(1)

# --- Heartbeat LED (onboard, GP25) ---
led = Pin(25, Pin.OUT)

# --- Hook switch ---
hook_pin = Pin(config.HOOK_PIN, Pin.IN, Pin.PULL_UP)

# --- DFPlayer BUSY pin (LOW = playing, HIGH = idle) ---
busy_pin = Pin(config.DFPLAYER_BUSY, Pin.IN, Pin.PULL_UP)

# --- DFPlayer Mini (optional — runs without it for testing) ---
HAS_AUDIO = False
df = None
if config.AUDIO_ENABLED:
    try:
        from dfplayer import DFPlayer
        df = DFPlayer(uart_id=config.DFPLAYER_UART,
                      tx_pin_id=config.DFPLAYER_TX,
                      rx_pin_id=config.DFPLAYER_RX)
        utime.sleep_ms(1000)
        df.volume(config.VOLUME)
        utime.sleep_ms(200)
        HAS_AUDIO = True
        print("DFPlayer OK (volume {})".format(config.VOLUME))
    except Exception as e:
        print("DFPlayer not found — running without audio ({})".format(e))
else:
    print("Audio disabled in config.py")

# --- Load phonebook ---
try:
    with open("phonebook.json", "r") as f:
        PHONEBOOK = json.load(f)
    print("Loaded {} poems from phonebook.".format(len(PHONEBOOK)))
except:
    PHONEBOOK = {}
    print("No phonebook.json found, using empty phonebook.")


# =============================================================================
# Keypad scanning — unchanged from phone.py
# =============================================================================

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
        if check_hangup():
            return None
        hit = raw_scan()
        if hit is not None and hit == last:
            count += 1
            if count >= 5:
                return config.KEYMAP[hit[0]][hit[1]]
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
        if wdt:
            wdt.feed()
        if check_hangup():
            return None
        hit = raw_scan()
        if hit is not None and hit == last:
            count += 1
            if count >= 5:
                return config.KEYMAP[hit[0]][hit[1]]
        else:
            count = 1 if hit is not None else 0
            last = hit
        utime.sleep_ms(10)
    return None


def wait_release():
    """Wait for key release. Returns True if key was stuck (2s timeout)."""
    clean = 0
    deadline = utime.ticks_add(utime.ticks_ms(), 2000)
    while clean < 5:
        if wdt:
            wdt.feed()
        if check_hangup():
            return False
        if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
            return True  # stuck key
        hit = raw_scan()
        if hit is None:
            clean += 1
        else:
            clean = 0
        utime.sleep_ms(5)
    utime.sleep_ms(30)
    return False


# =============================================================================
# Hook switch
# =============================================================================

def is_off_hook():
    """Debounced check — True if handset is lifted."""
    if not config.HOOK_ENABLED:
        return True
    for _ in range(5):
        val = hook_pin.value()
        if (val == 1) != config.HOOK_ACTIVE_HIGH:
            return False
        utime.sleep_ms(10)
    return True


def check_hangup():
    """Debounced check — True only if 3 consecutive reads say on-hook."""
    if not config.HOOK_ENABLED:
        return False
    for _ in range(3):
        val = hook_pin.value()
        if not ((val == 1) != config.HOOK_ACTIVE_HIGH):
            return False
        utime.sleep_ms(5)
    return True


# =============================================================================
# Audio helpers
# =============================================================================

# SFX name lookup for debug printing
_SFX_NAMES = {1: "DIALTONE", 2: "RINGBACK", 3: "BUSY", 4: "HANGUP",
              17: "OPERATOR", 18: "NOT_IN_SERVICE",
              19: "311_CITY_SERVICES", 20: "411_DIRECTORY", 21: "305_O_MIAMI",
              22: "911_EMERGENCY", 23: "211_COMMUNITY", 24: "511_TRAFFIC",
              25: "711_RELAY", 26: "811_DIG", 27: "611_CUSTOMER_SERVICE"}


def play_sfx(file_num):
    """Play a sound effect from /01/."""
    if HAS_AUDIO:
        df.play(config.SFX_FOLDER, file_num)
        utime.sleep_ms(50)
    else:
        name = _SFX_NAMES.get(file_num, "SFX:{}".format(file_num))
        print("  ~~ [{}]".format(name))


def play_poem(file_num):
    """Play a poem from /02/."""
    if HAS_AUDIO:
        df.play(config.POEM_FOLDER, file_num)
        utime.sleep_ms(50)
    else:
        print("  ~~ [POEM:{}]".format(file_num))


def play_random_poem():
    """Play a random poem from /03/."""
    file_num = random.randint(1, config.RANDOM_COUNT)
    if HAS_AUDIO:
        df.play(config.RANDOM_FOLDER, file_num)
        utime.sleep_ms(50)
    else:
        print("  ~~ [RANDOM:{}]".format(file_num))


def stop_audio():
    """Stop whatever is playing."""
    if HAS_AUDIO:
        df.stop()
        utime.sleep_ms(50)


def play_dtmf(key):
    """Play the DTMF tone for a key."""
    if key in config.DTMF_FILE:
        if HAS_AUDIO:
            play_sfx(config.DTMF_FILE[key])
        else:
            print("  ~~ [DTMF:{}]".format(key))


def wait_with_hangup_check(ms):
    """Wait for a duration, but return True immediately if hangup detected."""
    deadline = utime.ticks_add(utime.ticks_ms(), ms)
    while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
        if wdt:
            wdt.feed()
        if check_hangup():
            return True
        utime.sleep_ms(20)
    return False


def format_number(n):
    """Format 7 digits as xxx-xxxx."""
    if len(n) == 7:
        return "{}-{}".format(n[:3], n[3:])
    return n


def start_dialtone():
    """Play dial tone and reset the timeout timer."""
    global dialtone_start
    dialtone_start = utime.ticks_ms()
    play_sfx(config.SFX_DIALTONE)


# =============================================================================
# State machine
# =============================================================================

STATE_IDLE       = 0
STATE_OFF_HOOK   = 1
STATE_DIALING    = 2
STATE_CONNECTING = 3
STATE_PLAYING    = 4

state = STATE_IDLE
number = ""
dialtone_start = 0
play_start = 0
off_hook_start = 0

random.seed(utime.ticks_us())

# --- Watchdog timer (reboots Pico if main loop hangs) ---
wdt = None
if config.WATCHDOG_ENABLED:
    try:
        from machine import WDT
        wdt = WDT(timeout=config.WATCHDOG_TIMEOUT)
        print("Watchdog enabled ({}ms)".format(config.WATCHDOG_TIMEOUT))
    except Exception as e:
        print("Watchdog not available: {}".format(e))

# --- Boot chime ---
print("=== Poetry Phone ===")
if HAS_AUDIO:
    df.play(config.SFX_FOLDER, config.SFX_DIALTONE)
    utime.sleep_ms(500)
    df.stop()
    utime.sleep_ms(100)
    print("Boot chime OK")
print("Waiting for handset lift...\n")

while True:

    if wdt:
        wdt.feed()
    led.value(1 - led.value())
    gc.collect()

    try:

        # ----- IDLE: handset on cradle, waiting -----
        if state == STATE_IDLE:
            if is_off_hook():
                print("[off-hook]")
                state = STATE_OFF_HOOK
                number = ""
                off_hook_start = utime.ticks_ms()
                start_dialtone()
            else:
                utime.sleep_ms(50)

        # ----- OFF_HOOK: playing dial tone, waiting for first key -----
        elif state == STATE_OFF_HOOK:
            if check_hangup():
                stop_audio()
                print("[on-hook]")
                state = STATE_IDLE
                continue

            # Hard off-hook timeout (kid walked away with handset dangling)
            if utime.ticks_diff(utime.ticks_ms(), off_hook_start) > config.OFF_HOOK_TIMEOUT:
                print("[off-hook timeout]")
                stop_audio()
                state = STATE_IDLE
                continue

            if utime.ticks_diff(utime.ticks_ms(), dialtone_start) > config.DIALTONE_TIMEOUT:
                stop_audio()
                print("[dial tone timeout]")
                play_sfx(config.SFX_BUSY)
                wait_with_hangup_check(config.BUSY_DURATION)
                stop_audio()
                state = STATE_IDLE
                continue

            key = get_key_timeout(200)
            if key is not None:
                if key == '#':
                    pass  # ignore # during dial tone
                elif key == '*':
                    pass  # already have dial tone, nothing to clear
                else:
                    stop_audio()
                    utime.sleep_ms(30)
                    play_dtmf(key)
                    if wait_release():
                        print("[stuck key]")
                        number = ""
                        start_dialtone()
                        continue
                    number += key
                    print(number)
                    state = STATE_DIALING

        # ----- DIALING: accumulating digits with DTMF tones -----
        elif state == STATE_DIALING:
            if check_hangup():
                stop_audio()
                print("[on-hook]")
                state = STATE_IDLE
                number = ""
                continue

            # Hard off-hook timeout
            if utime.ticks_diff(utime.ticks_ms(), off_hook_start) > config.OFF_HOOK_TIMEOUT:
                print("[off-hook timeout]")
                stop_audio()
                number = ""
                state = STATE_IDLE
                continue

            # --- 10 digits: submit immediately ---
            if len(number) == 10:
                local = number[3:]
                print("(stripped area code {})".format(number[:3]))
                number = local
                state = STATE_CONNECTING
                continue

            # --- 7 digits: wait 2 seconds for more input ---
            if len(number) == 7:
                key = get_key_timeout(config.SEVEN_DIGIT_WAIT)
                if check_hangup():
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                if key is None:
                    state = STATE_CONNECTING
                    continue
                else:
                    play_dtmf(key)
                    if wait_release():
                        print("[stuck key]")
                        number = ""
                        start_dialtone()
                        state = STATE_OFF_HOOK
                        continue
                    if key == '*':
                        number = ""
                        print("[cleared]")
                        start_dialtone()
                        state = STATE_OFF_HOOK
                    elif key != '#':
                        number += key
                        print(number)
                    continue

            # --- Leading zero: operator ---
            if len(number) == 1 and number == "0":
                next_key = get_key_timeout(config.SPECIAL_CODE_WAIT)
                if check_hangup():
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                if next_key is None:
                    # Operator
                    stop_audio()
                    play_sfx(config.SPECIAL_CODES["0"])
                    play_start = utime.ticks_ms()
                    state = STATE_PLAYING
                else:
                    play_dtmf(next_key)
                    if wait_release():
                        print("[stuck key]")
                        number = ""
                        start_dialtone()
                        state = STATE_OFF_HOOK
                        continue
                    if next_key == '*':
                        number = ""
                        print("[cleared]")
                        start_dialtone()
                        state = STATE_OFF_HOOK
                    elif next_key != '#':
                        print("Numbers can't start with 0.")
                        number = ""
                        play_sfx(config.SFX_BUSY)
                        wait_with_hangup_check(3000)
                        stop_audio()
                        start_dialtone()
                        state = STATE_OFF_HOOK
                continue

            # --- Subsequent digits ---
            key = get_key_timeout(config.DIALING_TIMEOUT)
            if key is None:
                if check_hangup():
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                print("[dial timeout]")
                play_sfx(config.SFX_BUSY)
                wait_with_hangup_check(config.BUSY_DURATION)
                stop_audio()
                number = ""
                start_dialtone()
                state = STATE_OFF_HOOK
                continue
            play_dtmf(key)
            if wait_release():
                print("[stuck key]")
                number = ""
                start_dialtone()
                state = STATE_OFF_HOOK
                continue

            if key == '*':
                number = ""
                print("[cleared]")
                start_dialtone()
                state = STATE_OFF_HOOK
                continue
            elif key == '#':
                continue

            number += key
            print(number)

            # --- Reject overlong input ---
            if len(number) > 10:
                print("[too many digits]")
                play_sfx(config.SFX_BUSY)
                wait_with_hangup_check(config.BUSY_DURATION)
                stop_audio()
                number = ""
                start_dialtone()
                state = STATE_OFF_HOOK
                continue

            # --- 3-digit special codes ---
            if len(number) == 3 and number in config.SPECIAL_CODES:
                next_key = get_key_timeout(config.SPECIAL_CODE_WAIT)
                if check_hangup():
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                if next_key is None:
                    stop_audio()
                    play_sfx(config.SPECIAL_CODES[number])
                    play_start = utime.ticks_ms()
                    state = STATE_PLAYING
                else:
                    play_dtmf(next_key)
                    if wait_release():
                        print("[stuck key]")
                        number = ""
                        start_dialtone()
                        state = STATE_OFF_HOOK
                        continue
                    if next_key == '*':
                        number = ""
                        print("[cleared]")
                        start_dialtone()
                        state = STATE_OFF_HOOK
                    elif next_key != '#':
                        number += next_key
                        print(number)

        # ----- CONNECTING: ring or busy -----
        elif state == STATE_CONNECTING:
            if check_hangup():
                stop_audio()
                print("[on-hook]")
                state = STATE_IDLE
                number = ""
                continue

            if number in PHONEBOOK:
                print(">>> Calling {}...".format(format_number(number)))
                play_sfx(config.SFX_RINGBACK)
                hung_up = wait_with_hangup_check(config.RING_DURATION)
                if hung_up:
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                stop_audio()
                utime.sleep_ms(200)
                # Play the poem
                poem_file = PHONEBOOK[number]["file"]
                print('    Playing: "{}"'.format(PHONEBOOK[number]["title"]))
                play_poem(poem_file)
                play_start = utime.ticks_ms()
                state = STATE_PLAYING
            else:
                print(">>> {} - Random poem.".format(format_number(number)))
                play_sfx(config.SFX_RINGBACK)
                hung_up = wait_with_hangup_check(config.RING_DURATION)
                if hung_up:
                    stop_audio()
                    state = STATE_IDLE
                    number = ""
                    continue
                stop_audio()
                utime.sleep_ms(200)
                play_random_poem()
                play_start = utime.ticks_ms()
                state = STATE_PLAYING

        # ----- PLAYING: poem/sfx is playing -----
        elif state == STATE_PLAYING:
            if check_hangup():
                stop_audio()
                print("[on-hook]")
                state = STATE_IDLE
                number = ""
                continue

            # Safety timeout (5 minutes)
            if utime.ticks_diff(utime.ticks_ms(), play_start) > 300000:
                print("[play timeout]")
                stop_audio()
                number = ""
                start_dialtone()
                state = STATE_OFF_HOOK
                continue

            # Check BUSY pin: HIGH = idle (playback finished)
            # Skip first 2s to let DFPlayer start
            if utime.ticks_diff(utime.ticks_ms(), play_start) > 2000:
                if busy_pin.value() == 1:
                    print("[playback finished]")
                    play_sfx(config.SFX_HANGUP)
                    utime.sleep_ms(500)
                    stop_audio()
                    number = ""
                    start_dialtone()
                    state = STATE_OFF_HOOK
                    continue

            # Any key press interrupts playback and returns to dial tone
            key = get_key_timeout(200)
            if key is not None:
                if wait_release():
                    print("[stuck key]")
                print("[interrupted by keypress]")
                stop_audio()
                utime.sleep_ms(200)
                number = ""
                start_dialtone()
                state = STATE_OFF_HOOK

    except Exception as e:
        print("!!! ERROR: {}".format(e))
        try:
            stop_audio()
        except:
            pass
        state = STATE_IDLE
        number = ""
        utime.sleep_ms(1000)
