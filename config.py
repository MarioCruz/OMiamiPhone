# =============================================================================
# Poetry Phone — Configuration
#
# Edit this file to change hardware pins, volume, timing, and features.
# Deploy to Pico: mpremote cp config.py :config.py
# =============================================================================

# --- Hardware Flags ---
HOOK_ENABLED = True       # False = skip hook switch (always acts off-hook)
AUDIO_ENABLED = True      # False = skip DFPlayer (prints debug instead)

# --- Hook Switch ---
HOOK_PIN = 22             # GPIO pin for hook switch
HOOK_ACTIVE_HIGH = False  # True = HIGH means off-hook (NC switch with pull-up)
                          # False = LOW means off-hook (NO switch)

# --- DFPlayer Mini ---
DFPLAYER_UART = 1         # UART channel (1 = UART1)
DFPLAYER_TX = 20          # GPIO pin for Pico TX -> DFPlayer RX (via 1K resistor)
DFPLAYER_RX = 21          # GPIO pin for Pico RX <- DFPlayer TX
DFPLAYER_BUSY = 17        # GPIO pin for DFPlayer BUSY (LOW = playing, HIGH = idle)
VOLUME = 20               # 0-30, tune for your earpiece

# --- Keypad ---
# Old phone (7-wire, 3x4):
# COL_PINS = [0, 1, 2]      # GPIO pins for columns (output)
# ROW_PINS = [6, 5, 7, 3]   # GPIO pins for rows (input, pull-up)

# New phone (8-wire, 3x4):
COL_PINS = [6, 5, 7]      # GPIO pins for columns (output)
ROW_PINS = [4, 2, 1, 0]   # GPIO pins for rows (input, pull-up)
KEYMAP = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#'],
]

# --- SD Card Folders ---
SFX_FOLDER = 1            # Folder 01 on SD card = sound effects
POEM_FOLDER = 2           # Folder 02 on SD card = poems (mapped by number)
RANDOM_FOLDER = 3         # Folder 03 on SD card = random poems (unknown numbers)
RANDOM_COUNT = 28         # How many files in /03/ (update as you add more)

# --- Sound Effect File Numbers (in /01/) ---
SFX_DIALTONE       = 1
SFX_RINGBACK       = 2
SFX_BUSY           = 3
SFX_HANGUP         = 4
SFX_OPERATOR       = 17
SFX_NOT_IN_SERVICE = 18
SFX_311            = 19   # 311 — City services
SFX_411            = 20   # 411 — Directory assistance
SFX_305            = 21   # 305 — O Miami!
SFX_911            = 22   # 911 — Emergency redirect
SFX_211            = 23   # 211 — Community services
SFX_511            = 24   # 511 — Traffic/road conditions
SFX_711            = 25   # 711 — Telecommunications relay
SFX_811            = 26   # 811 — Call before you dig
SFX_611            = 27   # 611 — Customer service

DTMF_FILE = {
    '0': 5,  '1': 6,  '2': 7,  '3': 8,
    '4': 9,  '5': 10, '6': 11, '7': 12,
    '8': 13, '9': 14, '*': 15, '#': 16,
}

# --- Timing (milliseconds) ---
DIALTONE_TIMEOUT = 30000   # How long dial tone plays before giving up
SEVEN_DIGIT_WAIT = 2000    # Wait after 7 digits for more input
SPECIAL_CODE_WAIT = 1000   # Wait after special code (0, 411, etc.)
RING_DURATION = 5000       # How long ringback plays before poem starts
BUSY_DURATION = 4000       # How long busy signal plays

# --- Special Codes ---
# Map short-dial codes to SFX file numbers in /01/
# Replace values with dedicated audio file numbers as you record them
SPECIAL_CODES = {
    "0":   SFX_OPERATOR,
    "311": SFX_311,            # City services
    "411": SFX_411,            # Directory assistance
    "211": SFX_211,            # Community services
    "511": SFX_511,            # Traffic/road conditions
    "611": SFX_611,            # Customer service
    "711": SFX_711,            # Telecommunications relay
    "811": SFX_811,            # Call before you dig
    "911": SFX_911,            # Emergency redirect
    "305": SFX_305,            # O Miami!
}
