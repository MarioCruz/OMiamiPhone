"""Tests for watchdog timer mock and crash recovery infrastructure."""

from test.mock_micropython import MockWDT, PhoneSimulator


class TestMockWDT:

    def test_wdt_can_be_created_and_fed(self):
        wdt = MockWDT(timeout=8000)
        wdt.feed()
        assert wdt.feed_count == 1

    def test_wdt_tracks_feed_count(self):
        wdt = MockWDT()
        for _ in range(5):
            wdt.feed()
        assert wdt.feed_count == 5


class TestCrashRecovery:

    def test_phone_recovers_after_state_reset(self):
        """Simulate what the try/except does: reset to IDLE and continue."""
        phone = PhoneSimulator()
        phone.lift_handset()
        phone.dial_number("867")
        assert phone.state == phone.STATE_DIALING

        # Simulate crash recovery
        phone.stop_audio()
        phone.state = phone.STATE_IDLE
        phone.number = ""

        # Phone should work again
        phone.lift_handset()
        assert phone.state == phone.STATE_OFF_HOOK
        phone.dial_number("8675309")
        assert phone.number == "8675309"
