"""
Tests for dialing edge cases: operator, special codes, area code stripping,
# and * handling, number validation.
"""

import pytest
from test.mock_micropython import PhoneSimulator


PHONEBOOK = {
    "8675309": {"file": 1, "title": "Jenny"},
    "5551212": {"file": 2, "title": "Directory Blues"},
    "4115555": {"file": 3, "title": "Starts with 411"},
    "1234567": {"file": 4, "title": "Hello World"},
}


@pytest.fixture
def phone():
    return PhoneSimulator(phonebook=PHONEBOOK)


# =============================================================================
# Operator (dialing 0)
# =============================================================================

class TestOperator:
    def test_zero_triggers_operator_check(self, phone):
        phone.lift_handset()
        phone.dial_key("0")
        assert phone.check_operator()

    def test_zero_not_operator_after_more_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("05")
        assert not phone.check_operator()

    def test_non_zero_not_operator(self, phone):
        phone.lift_handset()
        phone.dial_key("5")
        assert not phone.check_operator()


# =============================================================================
# Special codes (311, 411, 911, etc.)
# =============================================================================

class TestSpecialCodes:
    def test_311_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("311")
        assert phone.check_special_code()

    def test_411_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("411")
        assert phone.check_special_code()

    def test_911_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("911")
        assert phone.check_special_code()

    def test_611_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("611")
        assert phone.check_special_code()

    def test_711_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("711")
        assert phone.check_special_code()

    def test_811_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("811")
        assert phone.check_special_code()

    def test_305_is_special_code(self, phone):
        phone.lift_handset()
        phone.dial_number("305")
        assert phone.check_special_code()

    def test_random_3_digits_not_special(self, phone):
        phone.lift_handset()
        phone.dial_number("123")
        assert not phone.check_special_code()

    def test_2_digits_not_special(self, phone):
        phone.lift_handset()
        phone.dial_number("41")
        assert not phone.check_special_code()

    def test_4_digits_not_special(self, phone):
        phone.lift_handset()
        phone.dial_number("4115")
        assert not phone.check_special_code()

    def test_special_code_sfx_mapping(self, phone):
        """Each special code maps to a valid SFX file number."""
        for code, sfx in phone.special_codes.items():
            assert isinstance(sfx, int)
            assert sfx > 0


# =============================================================================
# Area code stripping (10 digits → 7)
# =============================================================================

class TestAreaCodeStripping:
    def test_10_digits_strip_to_7(self, phone):
        phone.lift_handset()
        phone.dial_number("3058675309")
        phone.process_number()
        # After processing, number should be 7 digits
        # (process_number strips it internally)
        assert phone.state == phone.STATE_PLAYING

    def test_any_area_code_stripped(self, phone):
        """Different area codes all strip to same 7-digit lookup."""
        for area_code in ["305", "786", "212", "415", "800"]:
            phone2 = PhoneSimulator(phonebook=PHONEBOOK)
            phone2.lift_handset()
            phone2.dial_number(area_code + "8675309")
            result = phone2.process_number()
            assert result[0] == "playing", f"Area code {area_code} failed"
            assert result[1] == "Jenny"

    def test_7_digits_work_directly(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Jenny"

    def test_unknown_10_digit_plays_random(self, phone):
        phone.lift_handset()
        phone.dial_number("2129999999")
        result = phone.process_number()
        assert result[0] == "random"
        assert phone.state == phone.STATE_PLAYING


# =============================================================================
# Star key (clear/reset)
# =============================================================================

class TestStarKey:
    def test_star_in_off_hook_does_nothing(self, phone):
        phone.lift_handset()
        phone.dial_key("*")
        assert phone.state == phone.STATE_OFF_HOOK
        assert phone.number == ""

    def test_star_clears_partial_number(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        assert phone.number == "867"
        phone.dial_key("*")
        assert phone.number == ""
        assert phone.state == phone.STATE_OFF_HOOK

    def test_star_clears_full_number(self, phone):
        phone.lift_handset()
        phone.dial_number("867530")
        phone.dial_key("*")
        assert phone.number == ""
        assert phone.state == phone.STATE_OFF_HOOK

    def test_can_dial_new_number_after_star(self, phone):
        phone.lift_handset()
        phone.dial_number("999")
        phone.dial_key("*")
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Jenny"

    def test_multiple_star_presses(self, phone):
        phone.lift_handset()
        phone.dial_number("123")
        phone.dial_key("*")
        phone.dial_number("456")
        phone.dial_key("*")
        assert phone.number == ""
        assert phone.state == phone.STATE_OFF_HOOK

    def test_star_restarts_dial_tone(self, phone):
        phone.lift_handset()
        phone.dial_number("867")
        phone.audio_log.clear()
        phone.dial_key("*")
        assert ("sfx", phone.SFX_DIALTONE) in phone.audio_log


# =============================================================================
# Hash key (ignored)
# =============================================================================

class TestHashKey:
    def test_hash_ignored_in_off_hook(self, phone):
        phone.lift_handset()
        phone.dial_key("#")
        assert phone.state == phone.STATE_OFF_HOOK
        assert phone.number == ""

    def test_hash_ignored_during_dialing(self, phone):
        phone.lift_handset()
        phone.dial_number("86")
        phone.dial_key("#")
        assert phone.number == "86"
        assert phone.state == phone.STATE_DIALING

    def test_hash_does_not_add_to_number(self, phone):
        phone.lift_handset()
        phone.dial_number("8")
        phone.dial_key("#")
        phone.dial_key("#")
        phone.dial_key("#")
        assert phone.number == "8"

    def test_hash_between_digits(self, phone):
        phone.lift_handset()
        phone.dial_key("8")
        phone.dial_key("#")
        phone.dial_key("6")
        phone.dial_key("#")
        phone.dial_key("7")
        assert phone.number == "867"


# =============================================================================
# Numbers starting with 0
# =============================================================================

class TestLeadingZero:
    def test_zero_as_first_digit_enters_dialing(self, phone):
        phone.lift_handset()
        phone.dial_key("0")
        assert phone.state == phone.STATE_DIALING
        assert phone.number == "0"

    def test_single_zero_is_operator_candidate(self, phone):
        phone.lift_handset()
        phone.dial_key("0")
        assert phone.check_operator()


# =============================================================================
# Full call flow integration tests
# =============================================================================

class TestFullCallFlow:
    def test_dial_listen_hangup(self, phone):
        """Full flow: lift → dial → poem → hangup."""
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        assert phone.state == phone.STATE_PLAYING
        phone.hangup()
        assert phone.state == phone.STATE_IDLE

    def test_dial_listen_finish_redial(self, phone):
        """Full flow: lift → dial → poem finishes → dial again."""
        phone.lift_handset()
        phone.dial_number("8675309")
        phone.process_number()
        phone.poem_finished()
        assert phone.state == phone.STATE_OFF_HOOK
        phone.dial_number("5551212")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Directory Blues"

    def test_wrong_number_plays_random(self, phone):
        """Dial wrong number, get random poem."""
        phone.lift_handset()
        phone.dial_number("9999999")
        result = phone.process_number()
        assert result[0] == "random"
        assert phone.state == phone.STATE_PLAYING

    def test_wrong_number_then_hangup_redial(self, phone):
        """Dial wrong number, hear random poem, hang up, dial correct one."""
        phone.lift_handset()
        phone.dial_number("9999999")
        phone.process_number()
        phone.hangup()
        phone.lift_handset()
        phone.dial_number("8675309")
        result = phone.process_number()
        assert result[0] == "playing"

    def test_star_clear_then_dial(self, phone):
        """Start dialing, clear with *, then dial correct number."""
        phone.lift_handset()
        phone.dial_number("999")
        phone.dial_key("*")
        assert phone.state == phone.STATE_OFF_HOOK
        phone.dial_number("1234567")
        result = phone.process_number()
        assert result[0] == "playing"
        assert result[1] == "Hello World"

    def test_hangup_mid_dial(self, phone):
        """Hangup partway through dialing."""
        phone.lift_handset()
        phone.dial_number("867")
        phone.hangup()
        assert phone.state == phone.STATE_IDLE
        assert phone.number == ""

    def test_all_phonebook_entries_reachable(self, phone):
        """Every entry in the phonebook can be dialed."""
        for number, entry in PHONEBOOK.items():
            p = PhoneSimulator(phonebook=PHONEBOOK)
            p.lift_handset()
            p.dial_number(number)
            result = p.process_number()
            assert result[0] == "playing", f"Number {number} not reachable"
            assert result[1] == entry["title"]

    def test_all_phonebook_entries_reachable_with_area_code(self, phone):
        """Every entry reachable with any area code prefix."""
        for number, entry in PHONEBOOK.items():
            p = PhoneSimulator(phonebook=PHONEBOOK)
            p.lift_handset()
            p.dial_number("786" + number)
            result = p.process_number()
            assert result[0] == "playing", f"Number 786-{number} not reachable"


# =============================================================================
# Digit count boundaries
# =============================================================================

class TestDigitCountBoundaries:
    def test_1_digit(self, phone):
        phone.lift_handset()
        phone.dial_key("5")
        assert len(phone.number) == 1
        assert phone.state == phone.STATE_DIALING

    def test_6_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("867530")
        assert len(phone.number) == 6
        assert phone.state == phone.STATE_DIALING

    def test_7_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("8675309")
        assert len(phone.number) == 7
        assert phone.state == phone.STATE_DIALING

    def test_8_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("86753091")
        assert len(phone.number) == 8

    def test_9_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("867530912")
        assert len(phone.number) == 9

    def test_10_digits(self, phone):
        phone.lift_handset()
        phone.dial_number("3058675309")
        assert len(phone.number) == 10
