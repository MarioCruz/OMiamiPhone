"""
Tests for hook switch behavior and hangup from every state.
"""

import pytest
from test.mock_micropython import PhoneSimulator


PHONEBOOK = {
    "8675309": {"file": 1, "title": "Jenny"},
}


@pytest.fixture
def phone():
    return PhoneSimulator(phonebook=PHONEBOOK)


@pytest.fixture
def phone_no_hook():
    return PhoneSimulator(phonebook=PHONEBOOK, hook_enabled=False)


# =============================================================================
# Hook switch basics
# =============================================================================

class TestHookSwitch:
    def test_off_hook_when_lifted(self, phone):
        phone.set_off_hook(True)
        assert phone.is_off_hook()

    def test_on_hook_when_down(self, phone):
        phone.set_off_hook(False)
        assert not phone.is_off_hook()

    def test_check_hangup_true_when_on_hook(self, phone):
        phone.set_off_hook(False)
        assert phone.check_hangup()

    def test_check_hangup_false_when_off_hook(self, phone):
        phone.set_off_hook(True)
        assert not phone.check_hangup()


# =============================================================================
# Hook disabled mode
# =============================================================================

class TestHookDisabled:
    def test_always_off_hook(self, phone_no_hook):
        assert phone_no_hook.is_off_hook()

    def test_never_hangup(self, phone_no_hook):
        assert not phone_no_hook.check_hangup()

    def test_can_still_dial(self, phone_no_hook):
        phone_no_hook.lift_handset()
        phone_no_hook.dial_number("8675309")
        result = phone_no_hook.process_number()
        assert result[0] == "playing"


# =============================================================================
# Hangup from every state
# =============================================================================

class TestHangupFromEveryState:
    def test_hangup_from_idle(self, phone):
        """Hangup in IDLE is a no-op (already idle)."""
        phone.hangup()
        assert phone.state == phone.STATE_IDLE

    def test_hangup_from_off_hook(self, phone):
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_hangup_from_dialing_1_digit(self, phone):
        phone.lift_handset()
        phone.dial_key("8")
        assert phone.state == phone.STATE_DIALING
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_hangup_from_dialing_partial(self, phone):
        phone.lift_handset()
        phone.dial_number("8675")
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_hangup_from_dialing_7_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_hangup_from_playing(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        assert phone.state == phone.STATE_PLAYING
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_hangup_stops_audio(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.audio_log.clear()
        phone.hangup()
        assert ("stop",) in phone.audio_log


# =============================================================================
# State after hangup is clean
# =============================================================================

class TestHangupCleanup:
    def test_number_cleared_after_hangup(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        phone.hangup()
        assert phone.number == ""

    def test_state_is_idle_after_hangup(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.hangup()
        assert phone.state == phone.STATE_IDLE

    def test_can_redial_after_hangup(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.hangup()
        # Lift again
        phone.lift_handset()
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"

    def test_hangup_and_relift_plays_dial_tone(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        phone.hangup()
        phone.audio_log.clear()
        phone.lift_handset()
        assert ("sfx", phone.SFX_DIALTONE) in phone.audio_log


# =============================================================================
# Rapid hangup/lift cycles
# =============================================================================

class TestRapidHookCycles:
    def test_rapid_lift_hangup_lift(self, phone):
        phone.lift_handset()
        phone.hangup()
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK

    def test_rapid_lift_dial_hangup_lift_dial(self, phone):
        phone.lift_handset()
        phone.dial_number("123")
        phone.hangup()
        phone.lift_handset()
        assert phone.number == ""
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"

    def test_three_complete_calls(self, phone):
        """Three full call cycles back to back."""
        for _ in range(3):
            phone.lift_handset()
            phone.dial_number("8675309")
            result = phone.process_number()
            assert result[0] == "playing"
            phone.hangup()
            assert phone.state == phone.STATE_IDLE


# =============================================================================
# Dialtone timeout
# =============================================================================

class TestDialtoneTimeout:
    def test_dialtone_start_set_on_lift(self):
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.utime.advance(1000)  # some time passes
        phone.lift_handset()
        assert phone.dialtone_start == 1000

    def test_dialtone_start_reset_on_star(self):
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.lift_handset()
        phone.dial_number("867")
        phone.utime.advance(5000)
        phone.dial_key("*")
        # dialtone_start should be updated to current time
        assert phone.dialtone_start == phone.utime.ticks_ms()

    def test_dialtone_start_reset_after_poem(self):
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.utime.advance(60000)  # long poem
        phone.poem_finished()
        # After poem, dialtone_start should be updated
        assert phone.dialtone_start == phone.utime.ticks_ms()
