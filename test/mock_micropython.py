"""
Mock MicroPython modules for desktop testing.

Simulates machine.Pin, machine.UART, utime, and the DFPlayer
so we can test poetry_phone logic without hardware.
"""

import time as _time


# =============================================================================
# utime mock
# =============================================================================

class MockUtime:
    """Mock utime with controllable clock for deterministic tests."""

    def __init__(self):
        self._ticks = 0

    def ticks_ms(self):
        return self._ticks

    def ticks_add(self, ticks, delta):
        return ticks + delta

    def ticks_diff(self, end, start):
        return end - start

    def sleep_ms(self, ms):
        self._ticks += ms

    def sleep_us(self, us):
        self._ticks += us // 1000

    def advance(self, ms):
        """Test helper: advance time without sleep side effects."""
        self._ticks += ms


# =============================================================================
# machine.Pin mock
# =============================================================================

class MockPin:
    IN = 0
    OUT = 1
    PULL_UP = 2

    _pin_states = {}  # class-level: gp_num -> value

    def __init__(self, gp, mode=None, pull=None):
        self.gp = gp
        self.mode = mode
        self.pull = pull
        if gp not in MockPin._pin_states:
            # Default: pulled high if pull-up
            MockPin._pin_states[gp] = 1 if pull == MockPin.PULL_UP else 0

    def value(self, val=None):
        if val is not None:
            MockPin._pin_states[self.gp] = val
        return MockPin._pin_states[self.gp]

    @classmethod
    def reset_all(cls):
        cls._pin_states.clear()

    @classmethod
    def set_pin(cls, gp, val):
        cls._pin_states[gp] = val


# =============================================================================
# machine module mock
# =============================================================================

class MockUART:
    def __init__(self, uart_id, baud):
        self.uart_id = uart_id
        self.baud = baud
        self._rx_buffer = b""

    def init(self, baud, bits=8, parity=None, stop=1, tx=None, rx=None):
        self.baud = baud

    def write(self, data):
        pass

    def read(self):
        if self._rx_buffer:
            data = self._rx_buffer
            self._rx_buffer = b""
            return data
        return None

    def any(self):
        return len(self._rx_buffer)

    def flush(self):
        pass


class MockMachine:
    Pin = MockPin
    UART = MockUART


# =============================================================================
# DFPlayer mock
# =============================================================================

class MockDFPlayer:
    def __init__(self):
        self.current_volume = 0
        self.playing_folder = None
        self.playing_file = None
        self.is_stopped = True
        self.commands = []  # log of all commands

    def volume(self, vol):
        self.current_volume = vol
        self.commands.append(("volume", vol))

    def play(self, folder, file):
        self.stop()
        self.playing_folder = folder
        self.playing_file = file
        self.is_stopped = False
        self.commands.append(("play", folder, file))

    def stop(self):
        self.playing_folder = None
        self.playing_file = None
        self.is_stopped = True
        self.commands.append(("stop",))

    def is_playing(self):
        if self.is_stopped:
            return 0
        return self.playing_file or 0

    def reset(self):
        self.commands.append(("reset",))


# =============================================================================
# Keypad simulator
# =============================================================================

class KeypadSimulator:
    """Simulates keypad presses for testing the scanning functions."""

    def __init__(self):
        self._key_queue = []
        self._current_press = None
        self._press_counter = 0

    def queue_keys(self, keys):
        """Queue a sequence of keys to be 'pressed'."""
        self._key_queue = list(keys)

    def queue_key(self, key):
        """Queue a single key press."""
        self._key_queue.append(key)

    def get_next_key(self):
        """Pop and return the next key, or None if queue is empty."""
        if self._key_queue:
            return self._key_queue.pop(0)
        return None

    def is_empty(self):
        return len(self._key_queue) == 0


# =============================================================================
# Phone simulator — wraps the state machine for testing
# =============================================================================

class PhoneSimulator:
    """
    High-level test harness that simulates the Poetry Phone state machine.
    Instead of importing the real module (which needs hardware), we replicate
    the logic with injectable mocks.
    """

    def __init__(self, phonebook=None, special_codes=None, hook_enabled=True):
        self.utime = MockUtime()
        self.dfplayer = MockDFPlayer()
        self.hook_enabled = hook_enabled
        self.hook_active_high = True

        # State
        self.state = 0  # IDLE
        self.number = ""
        self.dialtone_start = 0
        self.off_hook = False

        # Config
        self.phonebook = phonebook or {}
        self.special_codes = special_codes or {
            "0": 17, "311": 19, "411": 20,
            "611": 17, "711": 17, "811": 17, "911": 17, "305": 21,
        }

        # Timing (ms)
        self.DIALTONE_TIMEOUT = 30000
        self.SEVEN_DIGIT_WAIT = 2000
        self.SPECIAL_CODE_WAIT = 1000
        self.RING_DURATION = 5000
        self.BUSY_DURATION = 4000

        # SFX numbers
        self.SFX_DIALTONE = 1
        self.SFX_RINGBACK = 2
        self.SFX_BUSY = 3
        self.SFX_HANGUP = 4
        self.SFX_NOT_IN_SERVICE = 18

        # Audio tracking
        self.audio_log = []
        self.has_audio = True

        # States
        self.STATE_IDLE = 0
        self.STATE_OFF_HOOK = 1
        self.STATE_DIALING = 2
        self.STATE_CONNECTING = 3
        self.STATE_PLAYING = 4

    def set_off_hook(self, val):
        self.off_hook = val

    def is_off_hook(self):
        if not self.hook_enabled:
            return True
        return self.off_hook

    def check_hangup(self):
        if not self.hook_enabled:
            return False
        return not self.off_hook

    def play_sfx(self, file_num):
        self.dfplayer.play(1, file_num)
        self.audio_log.append(("sfx", file_num))

    def play_poem(self, file_num):
        self.dfplayer.play(2, file_num)
        self.audio_log.append(("poem", file_num))

    def stop_audio(self):
        self.dfplayer.stop()
        self.audio_log.append(("stop",))

    def start_dialtone(self):
        self.dialtone_start = self.utime.ticks_ms()
        self.play_sfx(self.SFX_DIALTONE)

    def lift_handset(self):
        """Simulate lifting the handset."""
        self.set_off_hook(True)
        if self.state == self.STATE_IDLE:
            self.state = self.STATE_OFF_HOOK
            self.number = ""
            self.start_dialtone()

    def hangup(self):
        """Simulate hanging up."""
        self.set_off_hook(False)
        self.stop_audio()
        self.state = self.STATE_IDLE
        self.number = ""

    def dial_key(self, key):
        """Simulate pressing a key. Returns the resulting state."""
        if self.state == self.STATE_OFF_HOOK:
            if key == '#':
                pass  # ignore
            elif key == '*':
                pass  # already have dial tone
            else:
                self.stop_audio()
                self.audio_log.append(("dtmf", key))
                self.number += key
                self.state = self.STATE_DIALING
        elif self.state == self.STATE_DIALING:
            if key == '*':
                self.number = ""
                self.start_dialtone()
                self.state = self.STATE_OFF_HOOK
            elif key == '#':
                pass  # ignore
            else:
                self.audio_log.append(("dtmf", key))
                self.number += key
        return self.state

    def dial_number(self, digits):
        """Dial a sequence of digits."""
        for d in digits:
            self.dial_key(d)

    def process_number(self):
        """
        Process the accumulated number (what happens after dialing is complete).
        Simulates the CONNECTING state logic.
        """
        # 10 digits: strip area code
        if len(self.number) == 10:
            self.number = self.number[3:]

        self.state = self.STATE_CONNECTING

        if self.number in self.phonebook:
            self.play_sfx(self.SFX_RINGBACK)
            self.stop_audio()
            poem_file = self.phonebook[self.number]["file"]
            self.play_poem(poem_file)
            self.state = self.STATE_PLAYING
            return ("playing", self.phonebook[self.number]["title"])
        else:
            self.play_sfx(self.SFX_NOT_IN_SERVICE)
            self.stop_audio()
            self.play_sfx(self.SFX_BUSY)
            self.stop_audio()
            self.number = ""
            self.start_dialtone()
            self.state = self.STATE_OFF_HOOK
            return ("not_in_service", self.number)

    def check_operator(self):
        """Check if current number triggers operator (single 0)."""
        return len(self.number) == 1 and self.number == "0"

    def check_special_code(self):
        """Check if current number is a 3-digit special code."""
        return len(self.number) == 3 and self.number in self.special_codes

    def poem_finished(self):
        """Simulate poem playback finishing."""
        if self.state == self.STATE_PLAYING:
            self.play_sfx(self.SFX_HANGUP)
            self.stop_audio()
            self.number = ""
            self.start_dialtone()
            self.state = self.STATE_OFF_HOOK
