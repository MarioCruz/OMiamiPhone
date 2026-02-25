"""
Hook switch test — run on the Pico.

Detects when the phone handset is lifted (off-hook) or replaced (on-hook).
Use this to verify your hook switch wiring and determine NC vs NO behavior.

Wiring:
  GP22 ----+---- Hook Switch ---- GND
          |
     (internal pull-up enabled)

Expected (normally-closed switch with pull-up):
  Handset DOWN (on-hook):  switch closed -> GP22 = LOW  (0)
  Handset UP   (off-hook): switch open   -> GP22 = HIGH (1)

If your switch is normally-open, the values will be inverted.
The script will tell you which type you have.

Usage:
  mpremote connect /dev/cu.usbmodem1101 run hardware_test/hook_test.py
"""

from machine import Pin
import utime

HOOK_PIN = 22

hook = Pin(HOOK_PIN, Pin.IN, Pin.PULL_UP)

print("=== Hook Switch Test ===")
print("GP{} with internal pull-up\n".format(HOOK_PIN))

# Read initial state
initial = hook.value()
print("Current reading: GP{} = {}".format(HOOK_PIN, initial))
if initial == 0:
    print("  -> Switch is CLOSED (shorted to GND)")
    print("  -> If handset is DOWN, this is a Normally-Closed (NC) switch")
    print("  -> Set HOOK_ACTIVE_HIGH = True in config.py")
else:
    print("  -> Switch is OPEN (pulled HIGH)")
    print("  -> If handset is DOWN, this is a Normally-Open (NO) switch")
    print("  -> Set HOOK_ACTIVE_HIGH = False in config.py")

print("\nLift and replace the handset to test. Ctrl+C to stop.\n")

last_state = initial
debounce_count = 0
DEBOUNCE_THRESHOLD = 5  # 5 reads at 10ms = 50ms debounce

while True:
    val = hook.value()

    if val != last_state:
        debounce_count += 1
        if debounce_count >= DEBOUNCE_THRESHOLD:
            last_state = val
            debounce_count = 0
            if val == 1:
                print("[{}ms] GP{} = HIGH (switch OPEN)".format(
                    utime.ticks_ms(), HOOK_PIN))
            else:
                print("[{}ms] GP{} = LOW  (switch CLOSED)".format(
                    utime.ticks_ms(), HOOK_PIN))
    else:
        debounce_count = 0

    utime.sleep_ms(10)
