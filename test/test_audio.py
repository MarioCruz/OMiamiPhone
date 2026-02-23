"""
Tests for audio helpers: SFX, DTMF, dial tone, DFPlayer mock behavior.
"""

import pytest
from test.mock_micropython import PhoneSimulator, MockDFPlayer


# =============================================================================
# DFPlayer mock behavior
# =============================================================================

class TestMockDFPlayer:
    def test_initial_state_stopped(self):
        df = MockDFPlayer()
        assert df.is_stopped
        assert df.is_playing() == 0

    def test_play_sets_state(self):
        df = MockDFPlayer()
        df.play(1, 5)
        assert not df.is_stopped
        assert df.playing_folder == 1
        assert df.playing_file == 5

    def test_is_playing_returns_file_number(self):
        df = MockDFPlayer()
        df.play(2, 3)
        assert df.is_playing() == 3

    def test_stop_clears_state(self):
        df = MockDFPlayer()
        df.play(1, 1)
        df.stop()
        assert df.is_stopped
        assert df.is_playing() == 0

    def test_play_stops_before_playing(self):
        df = MockDFPlayer()
        df.play(1, 1)
        df.play(2, 5)
        # Should have: stop, play(1,1), stop, play(2,5)
        assert df.playing_folder == 2
        assert df.playing_file == 5

    def test_volume_tracked(self):
        df = MockDFPlayer()
        df.volume(20)
        assert df.current_volume == 20

    def test_commands_logged(self):
        df = MockDFPlayer()
        df.volume(15)
        df.play(1, 1)
        df.stop()
        assert ("volume", 15) in df.commands
        assert ("stop",) in df.commands


# =============================================================================
# Audio logging in PhoneSimulator
# =============================================================================

class TestAudioLogging:
    def test_play_sfx_logs_correctly(self):
        phone = PhoneSimulator()
        phone.play_sfx(1)
        assert ("sfx", 1) in phone.audio_log

    def test_play_poem_logs_correctly(self):
        phone = PhoneSimulator()
        phone.play_poem(3)
        assert ("poem", 3) in phone.audio_log

    def test_stop_audio_logs_correctly(self):
        phone = PhoneSimulator()
        phone.stop_audio()
        assert ("stop",) in phone.audio_log

    def test_start_dialtone_logs_sfx(self):
        phone = PhoneSimulator()
        phone.start_dialtone()
        assert ("sfx", phone.SFX_DIALTONE) in phone.audio_log

    def test_start_dialtone_sets_timer(self):
        phone = PhoneSimulator()
        phone.utime.advance(5000)
        phone.start_dialtone()
        assert phone.dialtone_start == 5000


# =============================================================================
# SFX file number consistency
# =============================================================================

class TestSfxNumbers:
    def test_dialtone_is_1(self):
        phone = PhoneSimulator()
        assert phone.SFX_DIALTONE == 1

    def test_ringback_is_2(self):
        phone = PhoneSimulator()
        assert phone.SFX_RINGBACK == 2

    def test_busy_is_3(self):
        phone = PhoneSimulator()
        assert phone.SFX_BUSY == 3

    def test_hangup_is_4(self):
        phone = PhoneSimulator()
        assert phone.SFX_HANGUP == 4

    def test_not_in_service_is_18(self):
        phone = PhoneSimulator()
        assert phone.SFX_NOT_IN_SERVICE == 18


# =============================================================================
# Audio sequence tests (correct order of sounds)
# =============================================================================

PHONEBOOK = {
    "8675309": {"file": 1, "title": "Jenny"},
}


class TestAudioSequences:
    def test_successful_call_audio_sequence(self):
        """Lift → dial → ring → poem."""
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.audio_log.clear()
        phone.process_number()

        sfx_types = [e[0] for e in phone.audio_log]
        # Should see: sfx(ringback), stop, poem
        assert "sfx" in sfx_types
        assert "poem" in sfx_types
        # Ringback before poem
        ringback_idx = next(i for i, e in enumerate(phone.audio_log) if e == ("sfx", phone.SFX_RINGBACK))
        poem_idx = next(i for i, e in enumerate(phone.audio_log) if e[0] == "poem")
        assert ringback_idx < poem_idx

    def test_unknown_call_audio_sequence(self):
        """Lift → dial unknown → ringback → random poem."""
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.lift_handset()
        phone.dial_number("9999999")
        phone.audio_log.clear()
        phone.process_number()

        sfx_nums = [e[1] for e in phone.audio_log if e[0] == "sfx"]
        assert phone.SFX_RINGBACK in sfx_nums
        random_plays = [e for e in phone.audio_log if e[0] == "random"]
        assert len(random_plays) == 1
        # Ringback before random poem
        ringback_idx = next(i for i, e in enumerate(phone.audio_log) if e == ("sfx", phone.SFX_RINGBACK))
        random_idx = next(i for i, e in enumerate(phone.audio_log) if e[0] == "random")
        assert ringback_idx < random_idx

    def test_poem_finish_audio_sequence(self):
        """Poem ends → hangup click → dial tone."""
        phone = PhoneSimulator(phonebook=PHONEBOOK)
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.audio_log.clear()
        phone.poem_finished()

        sfx_nums = [e[1] for e in phone.audio_log if e[0] == "sfx"]
        assert phone.SFX_HANGUP in sfx_nums
        assert phone.SFX_DIALTONE in sfx_nums
        # Hangup before dial tone
        hangup_idx = next(i for i, e in enumerate(phone.audio_log) if e == ("sfx", phone.SFX_HANGUP))
        dialtone_idx = next(i for i, e in enumerate(phone.audio_log) if e == ("sfx", phone.SFX_DIALTONE))
        assert hangup_idx < dialtone_idx
