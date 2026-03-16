# VidMark
# Copyright (C) 2026 qexela
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tests for core.keyfile: save/load roundtrip and validation.
FIX: Validates that corrupted/incomplete keyfiles are rejected.
"""

import json
import os
import pytest
import numpy as np

from config import WatermarkSettings
from core.keyfile import save_keyfile, load_keyfile

def _make_test_settings():
    s = WatermarkSettings()
    s.wavelet = "haar"
    s.dwt_level = 1
    s.block_size = 8
    s.scramble_seed = 42
    s.rs_nsym = 32
    return s


def _make_test_data():
    video_info = {"width": 1920, "height": 1080, "fps": 30.0, "frame_count": 300}
    embed_info = {}
    payload_info = {
        "uuid_hex": "abcdef0123456789",
        "timestamp": 1700000000,
        "timestamp_str": "2023-11-14 22:13:20",
        "total_bits": 120,
    }
    return video_info, embed_info, payload_info


def test_keyfile_save_load_roundtrip(tmp_path):
    """Save then load should reconstruct settings with correct delta."""
    settings = _make_test_settings()
    video_info, embed_info, payload_info = _make_test_data()

    kf_path = str(tmp_path / "test_key.json")
    save_keyfile(kf_path, settings, video_info, embed_info, payload_info, author_text="alice")

    loaded_settings, loaded_data = load_keyfile(kf_path)

    assert loaded_settings.wavelet == "haar"
    assert loaded_settings.dwt_level == 1
    assert loaded_settings.block_size == 8
    assert loaded_settings.scramble_seed == 42
    assert loaded_settings.rs_nsym == 32
    assert abs(loaded_settings.get_delta() - settings.get_delta()) < 0.01

    assert loaded_data["payload_info"]["uuid_hex"] == "abcdef0123456789"
    assert loaded_data["payload_info"]["author_text"] == "alice"


def test_keyfile_load_rejects_missing_params(tmp_path):
    """FIX: Keyfile without 'params' section must raise ValueError."""
    kf_path = str(tmp_path / "bad_key.json")
    bad_data = {
        "version": "1.0.0",
        "security": {"scramble_seed": 42, "rs_nsym": 32},
        "extraction_hints": {"payload_length_bits": 120},
        # "params" is missing!
    }
    with open(kf_path, "w") as f:
        json.dump(bad_data, f)

    with pytest.raises(ValueError, match="missing required sections"):
        load_keyfile(kf_path)


def test_keyfile_load_rejects_missing_security(tmp_path):
    """FIX: Keyfile without 'security' section must raise ValueError."""
    kf_path = str(tmp_path / "bad_key2.json")
    bad_data = {
        "version": "1.0.0",
        "params": {"wavelet": "haar", "dwt_level": 1, "block_size": 8},
        "extraction_hints": {"payload_length_bits": 120},
        # "security" is missing!
    }
    with open(kf_path, "w") as f:
        json.dump(bad_data, f)

    with pytest.raises(ValueError, match="missing required sections"):
        load_keyfile(kf_path)


def test_keyfile_load_rejects_empty_json(tmp_path):
    """Empty JSON object should be rejected."""
    kf_path = str(tmp_path / "empty_key.json")
    with open(kf_path, "w") as f:
        json.dump({}, f)

    with pytest.raises(ValueError, match="missing required sections"):
        load_keyfile(kf_path)


def test_keyfile_load_rejects_invalid_json(tmp_path):
    """Non-JSON file should raise json.JSONDecodeError."""
    kf_path = str(tmp_path / "garbage.json")
    with open(kf_path, "w") as f:
        f.write("this is not json!!!")

    with pytest.raises(json.JSONDecodeError):
        load_keyfile(kf_path)


def test_keyfile_preserves_custom_delta(tmp_path):
    """Loaded settings must use CUSTOM preset to preserve exact delta from keyfile."""
    from config import StrengthPreset

    settings = _make_test_settings()
    settings.custom_delta = 42.5
    settings.strength_preset = StrengthPreset.CUSTOM

    video_info, embed_info, payload_info = _make_test_data()
    kf_path = str(tmp_path / "delta_key.json")
    save_keyfile(kf_path, settings, video_info, embed_info, payload_info)

    loaded, _ = load_keyfile(kf_path)
    assert loaded.strength_preset == StrengthPreset.CUSTOM
    assert abs(loaded.get_delta() - 42.5) < 0.01