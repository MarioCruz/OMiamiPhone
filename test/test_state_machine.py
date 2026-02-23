"""
Tests for the Poetry Phone state machine transitions.
"""

import pytest
from test.mock_micropython import PhoneSimulator


PHONEBOOK = {
    "8675309": {"file": 1, "title": "Jenny"},
    "5551212": {"file": 2, "title": "Directory Blues"},
    "1234567": {"file": 4, "title": "Hello World"},
}


@pytest.fixture
def phone():
    return PhoneSimulator(phonebook=PHONEBOOK)


@pytest.fixture
def phone_no_hook():
    return PhoneSimulator(phonebook=PHONEBOOK, hook_enabled=False)


# =============================================================================
# IDLE state
# =============================================================================

class TestIdleState:
    def test_starts_in_idle(self, phone):
        assert phone.state == phone.STATE_IDLE

    def test_lift_handset_goes_to_off_hook(self, phone):
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK

    def test_lift_handset_plays_dial_tone(self, phone):
        phone.lift_handset()
        assert ("sfx", phone.SFX_DIALTONE) in phone.audio_log

    def test_lift_handset_clears_number(self, phone):
        phone.number = "12345"
        phone.lift_handset()
        assert phone.number == ""

    def test_stays_idle_when_on_hook(self, phone):
        phone.set_off_hook(False)
        assert phone.state == phone.STATE_IDLE
        assert not phone.is_off_hook()


# =============================================================================
# OFF_HOOK state
# =============================================================================

class TestOffHookState:
    def test_first_digit_goes_to_dialing(self, phone):
        phone.lift_handset()
        phone.dial_key("5")
        assert phone.state == phone.STATE_DIALING
        assert phone.number == "5"

    def test_hash_ignored_stays_off_hook(self, phone):
        phone.lift_handset()
        phone.dial_key("#")
        assert phone.state == phone.STATE_OFF_HOOK
        assert phone.number == ""

    def test_star_ignored_stays_off_hook(self, phone):
        phone.lift_handset()
        phone.dial_key("*")
        assert phone.state == phone.STATE_OFF_HOOK
        assert phone.number == ""

    def test_hash_does_not_stop_dial_tone(self, phone):
        phone.lift_handset()
        phone.audio_log.clear()
        phone.dial_key("#")
        # No stop_audio should appear in log
        assert ("stop",) not in phone.audio_log

    def test_digit_stops_dial_tone(self, phone):
        phone.lift_handset()
        phone.audio_log.clear()
        phone.dial_key("5")
        assert ("stop",) in phone.audio_log

    def test_digit_plays_dtmf(self, phone):
        phone.lift_handset()
        phone.audio_log.clear()
        phone.dial_key("5")
        assert ("dtmf", "5") in phone.audio_log

    def test_hangup_from_off_hook(self, phone):
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK
        phone.hangup()
        assert phone.state == phone.STATE_IDLE


# =============================================================================
# DIALING state
# =============================================================================

class TestDialingState:
    def test_accumulates_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        assert phone.number == "867"
        assert phone.state == phone.STATE_DIALING

    def test_star_clears_goes_to_off_hook(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        phone.dial_key("*")
        assert phone.number == ""
        assert phone.state == phone.STATE_OFF_HOOK

    def test_hash_ignored_during_dialing(self, phone):
        phone.lift_handset()
        phone.dial_number("86")
        phone.dial_key("#")
        assert phone.number == "86"
        assert phone.state == phone.STATE_DIALING

    def test_seven_digits_accumulated(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        assert phone.number == "8675309"

    def test_ten_digits_accumulated(self, phone):
        phone.lift_handset()
        phone.dial_number("3058675309")
        assert phone.number == "3058675309"

    def test_hangup_during_dialing(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""


# =============================================================================
# CONNECTING state
# =============================================================================

class TestConnectingState:
    def test_known_number_plays_poem(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Jenny"
        assert phone.state == phone.STATE_PLAYING

    def test_unknown_number_not_in_service(self, phone):
        phone.lift_handset()
        phone.dial_number("9999999")
        result = phone.process_number()
        assert result[0] == "not_in_service"
        assert phone.state == phone.STATE_OFF_HOOK

    def test_ten_digit_strips_area_code(self, phone):
        phone.lift_handset()
        phone.dial_number("3058675309")
        result = phone.process_number()
        assert phone.number == "8675309" or result[0] == "playing"
        assert result[0] == "playing"
        assert result[1] == "Jenny"

    def test_unknown_ten_digit_not_in_service(self, phone):
        phone.lift_handset()
        phone.dial_number("3059999999")
        result = phone.process_number()
        assert result[0] == "not_in_service"

    def test_ringback_played_for_known_number(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.audio_log.clear()
        phone.process_number()
        sfx_plays = [e for e in phone.audio_log if e[0] == "sfx"]
        assert ("sfx", phone.SFX_RINGBACK) in sfx_plays

    def test_not_in_service_played_for_unknown(self, phone):
        phone.lift_handset()
        phone.dial_number("9999999")
        phone.audio_log.clear()
        phone.process_number()
        sfx_plays = [e for e in phone.audio_log if e[0] == "sfx"]
        assert ("sfx", phone.SFX_NOT_IN_SERVICE) in sfx_plays

    def test_busy_signal_after_not_in_service(self, phone):
        phone.lift_handset()
        phone.dial_number("9999999")
        phone.audio_log.clear()
        phone.process_number()
        sfx_plays = [e for e in phone.audio_log if e[0] == "sfx"]
        assert ("sfx", phone.SFX_BUSY) in sfx_plays


# =============================================================================
# PLAYING state
# =============================================================================

class TestPlayingState:
    def test_poem_finished_goes_to_off_hook(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        assert phone.state == phone.STATE_PLAYING
        phone.poem_finished()
        assert phone.state == phone.STATE_OFF_HOOK

    def test_poem_finished_plays_hangup_click(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.audio_log.clear()
        phone.poem_finished()
        assert ("sfx", phone.SFX_HANGUP) in phone.audio_log

    def test_poem_finished_restarts_dial_tone(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.audio_log.clear()
        phone.poem_finished()
        assert ("sfx", phone.SFX_DIALTONE) in phone.audio_log

    def test_hangup_during_poem(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        assert phone.state == phone.STATE_PLAYING
        phone.hangup()
        assert phone.state == phone.STATE_IDLE

    def test_can_dial_again_after_poem(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.poem_finished()
        assert phone.state == phone.STATE_OFF_HOOK
        phone.dial_number("5551212")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Directory Blues"
