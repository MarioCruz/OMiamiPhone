"""
Tests that config.py, phonebook.json, and generate_tones.py are consistent.
These catch mismatches between file numbers, folder assignments, and naming.
"""

import json
import os
import pytest
import ast

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config_values():
    """Parse config.py using AST to extract all simple assignments (avoids MicroPython deps)."""
    config_path = os.path.join(PROJECT_ROOT, "config.py")
    with open(config_path) as f:
        source = f.read()

    tree = ast.parse(source)
    values = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass  # Skip expressions that reference other variables
    return values


def load_phonebook():
    pb_path = os.path.join(PROJECT_ROOT, "phonebook.json")
    with open(pb_path) as f:
        return json.load(f)


def load_generate_tones_constants():
    """Parse DTMF_FILE_MAP from generate_tones.py."""
    gt_path = os.path.join(PROJECT_ROOT, "tools", "generate_tones.py")
    with open(gt_path) as f:
        source = f.read()

    # Extract DTMF_FILE_MAP dict
    tree = ast.parse(source)
    dtmf_map = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DTMF_FILE_MAP":
                    # Evaluate the dict
                    dtmf_map = ast.literal_eval(node.value)
    return dtmf_map


# =============================================================================
# Config file tests
# =============================================================================

class TestConfigValues:
    def test_config_exists(self):
        assert os.path.exists(os.path.join(PROJECT_ROOT, "config.py"))

    def test_sfx_folder_is_1(self):
        cfg = load_config_values()
        assert cfg["SFX_FOLDER"] == 1

    def test_poem_folder_is_2(self):
        cfg = load_config_values()
        assert cfg["POEM_FOLDER"] == 2

    def test_sfx_dialtone_is_1(self):
        cfg = load_config_values()
        assert cfg["SFX_DIALTONE"] == 1

    def test_sfx_ringback_is_2(self):
        cfg = load_config_values()
        assert cfg["SFX_RINGBACK"] == 2

    def test_sfx_busy_is_3(self):
        cfg = load_config_values()
        assert cfg["SFX_BUSY"] == 3

    def test_sfx_hangup_is_4(self):
        cfg = load_config_values()
        assert cfg["SFX_HANGUP"] == 4

    def test_volume_in_range(self):
        cfg = load_config_values()
        assert 0 <= cfg["VOLUME"] <= 30

    def test_dtmf_file_has_all_keys(self):
        cfg = load_config_values()
        dtmf = cfg["DTMF_FILE"]
        for key in "0123456789*#":
            assert key in dtmf, f"Missing DTMF key: {key}"

    def test_dtmf_file_numbers_are_5_to_16(self):
        cfg = load_config_values()
        dtmf = cfg["DTMF_FILE"]
        values = sorted(dtmf.values())
        assert values == list(range(5, 17))

    def test_no_sfx_number_collisions(self):
        """SFX file numbers and DTMF file numbers must not overlap."""
        cfg = load_config_values()
        sfx_nums = {
            cfg["SFX_DIALTONE"], cfg["SFX_RINGBACK"],
            cfg["SFX_BUSY"], cfg["SFX_HANGUP"],
            cfg["SFX_OPERATOR"], cfg["SFX_NOT_IN_SERVICE"],
            cfg.get("SFX_311", 19), cfg.get("SFX_411", 20), cfg.get("SFX_305", 21),
        }
        dtmf_nums = set(cfg["DTMF_FILE"].values())
        overlap = sfx_nums & dtmf_nums
        assert not overlap, f"SFX/DTMF file number collision: {overlap}"


# =============================================================================
# Phonebook tests
# =============================================================================

class TestPhonebook:
    def test_phonebook_exists(self):
        assert os.path.exists(os.path.join(PROJECT_ROOT, "phonebook.json"))

    def test_phonebook_valid_json(self):
        pb = load_phonebook()
        assert isinstance(pb, dict)

    def test_all_keys_are_7_digits(self):
        pb = load_phonebook()
        for key in pb:
            assert len(key) == 7, f"Key '{key}' is not 7 digits"
            assert key.isdigit(), f"Key '{key}' contains non-digits"

    def test_all_entries_have_file(self):
        pb = load_phonebook()
        for key, entry in pb.items():
            assert "file" in entry, f"Entry '{key}' missing 'file'"
            assert isinstance(entry["file"], int)

    def test_all_entries_have_title(self):
        pb = load_phonebook()
        for key, entry in pb.items():
            assert "title" in entry, f"Entry '{key}' missing 'title'"
            assert isinstance(entry["title"], str)
            assert len(entry["title"]) > 0

    def test_file_numbers_are_unique(self):
        pb = load_phonebook()
        files = [e["file"] for e in pb.values()]
        assert len(files) == len(set(files)), "Duplicate file numbers in phonebook"

    def test_file_numbers_start_at_1(self):
        pb = load_phonebook()
        files = sorted(e["file"] for e in pb.values())
        assert files[0] >= 1

    def test_no_phonebook_collision_with_sfx(self):
        """Poem file numbers must not collide (they're in different folders, but verify)."""
        pb = load_phonebook()
        files = [e["file"] for e in pb.values()]
        for f in files:
            assert f > 0


# =============================================================================
# generate_tones.py consistency
# =============================================================================

class TestGenerateTonesConsistency:
    def test_generate_tones_exists(self):
        assert os.path.exists(os.path.join(PROJECT_ROOT, "tools", "generate_tones.py"))

    def test_dtmf_map_matches_config(self):
        """DTMF file numbers in generate_tones.py must match config.py."""
        cfg = load_config_values()
        gt_map = load_generate_tones_constants()

        for key in "0123456789*#":
            gt_num = gt_map[key][0]  # tuple: (file_num, name)
            cfg_num = cfg["DTMF_FILE"][key]
            assert gt_num == cfg_num, (
                f"DTMF '{key}': generate_tones says {gt_num}, config says {cfg_num}"
            )

    def test_dtmf_map_has_all_keys(self):
        gt_map = load_generate_tones_constants()
        for key in "0123456789*#":
            assert key in gt_map, f"Missing key '{key}' in generate_tones DTMF_FILE_MAP"


# =============================================================================
# Pin assignments
# =============================================================================

class TestPinAssignments:
    def test_no_pin_conflicts(self):
        """All GPIO pins must be unique (no two functions share a pin)."""
        cfg = load_config_values()
        pins = []
        pins.extend(cfg["COL_PINS"])
        pins.extend(cfg["ROW_PINS"])
        pins.append(cfg["HOOK_PIN"])
        pins.append(cfg["DFPLAYER_TX"])
        pins.append(cfg["DFPLAYER_RX"])
        assert len(pins) == len(set(pins)), f"Pin conflict: {pins}"

    def test_keypad_pins_are_gp0_to_gp6(self):
        cfg = load_config_values()
        all_keypad = cfg["COL_PINS"] + cfg["ROW_PINS"]
        for pin in all_keypad:
            assert 0 <= pin <= 6, f"Keypad pin GP{pin} outside expected range"

    def test_hook_pin_is_gp22(self):
        cfg = load_config_values()
        assert cfg["HOOK_PIN"] == 22

    def test_dfplayer_pins_are_gp20_gp21(self):
        cfg = load_config_values()
        assert cfg["DFPLAYER_TX"] == 20
        assert cfg["DFPLAYER_RX"] == 21
