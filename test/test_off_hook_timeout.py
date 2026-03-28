"""Tests for the hard off-hook timeout — prevents infinite dial tone loops
when a kid walks away with the handset dangling."""

import pytest
from test.mock_micropython import PhoneSimulator

PHONEBOOK = {"8675309": {"file": 1, "title": "Jenny"}}


class TestOffHookTimeout:

    @pytest.fixture
    def phone(self):
        return PhoneSimulator(phonebook=PHONEBOOK)

    def test_timeout_in_off_hook(self, phone):
        phone.lift_handset()
        phone.utime.advance(121000)
        assert phone.check_off_hook_timeout()
        assert phone.state == phone.STATE_IDLE

    def test_no_timeout_before_limit(self, phone):
        phone.lift_handset()
        phone.utime.advance(60000)
        assert not phone.check_off_hook_timeout()
        assert phone.state == phone.STATE_OFF_HOOK

    def test_timeout_in_dialing(self, phone):
        phone.lift_handset()
        phone.dial_number("86")
        phone.utime.advance(121000)
        assert phone.check_off_hook_timeout()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_no_timeout_in_playing(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        assert phone.state == phone.STATE_PLAYING
        phone.utime.advance(121000)
        assert not phone.check_off_hook_timeout()
        assert phone.state == phone.STATE_PLAYING

    def test_relift_after_timeout(self, phone):
        phone.lift_handset()
        phone.utime.advance(121000)
        phone.check_off_hook_timeout()
        assert phone.state == phone.STATE_IDLE
        # Must hangup then relift
        phone.hangup()
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK
