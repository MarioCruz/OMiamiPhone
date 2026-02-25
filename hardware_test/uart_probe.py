"""
UART probe — tries multiple pin combos to find the DFPlayer.

Tries GP20/GP21 normal, then swapped, then GP8/GP9 (old pins)
in case the wiring is on the original pins.

Usage:
  mpremote connect /dev/cu.usbmodem1101 run hardware_test/uart_probe.py
"""

from machine import UART, Pin
import utime

def try_uart(uart_id, tx_pin, rx_pin, label):
    print("  Testing {} (UART{}, TX=GP{}, RX=GP{})...".format(label, uart_id, tx_pin, rx_pin))
    try:
        uart = UART(uart_id, baudrate=9600, tx=Pin(tx_pin), rx=Pin(rx_pin))
    except ValueError as e:
        print("    Skip — invalid pin combo: {}".format(e))
        return False
    utime.sleep_ms(200)

    # Flush any stale data
    uart.read()

    # Send "get status" command
    cmd = bytearray([0x7E, 0xFF, 0x06, 0x42, 0x00, 0x00, 0x00, 0xFE, 0xB9, 0xEF])
    uart.write(cmd)
    utime.sleep_ms(500)

    resp = uart.read()
    if resp:
        print("    RESPONSE: {}".format(resp.hex()))
        return True
    else:
        print("    No response")
        return False

print("=" * 40)
print("UART Probe for DFPlayer")
print("=" * 40)

# Check if DFPlayer LED is on (power test via a pin read isn't possible,
# but we can tell the user)
print("\nFirst: Is the DFPlayer LED lit up?")
print("If not, it has no power.\n")

found = False

# Try 1: Normal GP20/GP21 (UART1)
print("[1/3] GP20 TX -> DFPlayer RX, GP21 RX <- DFPlayer TX (UART1)")
if try_uart(1, 20, 21, "normal"):
    found = True
    print("    >> FOUND on GP20/GP21 (correct!)")

# Try 2: Old pins GP8/GP9 (UART1)
if not found:
    print("\n[2/3] GP8 TX, GP9 RX (old pin assignment, UART1)")
    if try_uart(1, 8, 9, "old pins UART1"):
        found = True
        print("    >> FOUND on GP8/GP9!")
        print("    >> Move wires to GP20/GP21, or change config.py back")

# Try 3: GP4/GP5 (UART1 alt)
if not found:
    print("\n[3/3] GP4 TX, GP5 RX (UART1 alternate)")
    if try_uart(1, 4, 5, "alt UART1"):
        found = True
        print("    >> FOUND on GP4/GP5!")

if not found:
    print("\n>> NO RESPONSE on any pin combination!")
    print("")
    print("This means either:")
    print("  1. DFPlayer has no power (check VCC -> VBUS 5V, GND -> GND)")
    print("  2. TX/RX wires aren't connected to ANY of these pins")
    print("  3. The 1K resistor is missing or broken")
    print("  4. The DFPlayer module is dead")
    print("  5. SD card is not inserted (some clones won't respond without it)")
    print("")
    print("Try: remove the 1K resistor temporarily and connect TX direct")

print("\n" + "=" * 40)
