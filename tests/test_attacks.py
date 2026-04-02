# VidMark
# Copyright (C) 2026 AlexAgents
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
Tests for AttackSimulator.
These are mostly shape/type sanity checks.

Note: H.264/H.265 attacks require ffmpeg available in PATH.
If ffmpeg is missing, we skip those tests.
"""

import shutil
import numpy as np
import pytest

from core.attacks import AttackSimulator


def test_apply_gaussian_noise():
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    noisy = AttackSimulator.apply_attack(frame, "Gaussian Noise σ=10")
    assert noisy.shape == frame.shape
    assert noisy.dtype == np.uint8
    assert not np.array_equal(frame, noisy)


def test_apply_jpeg():
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    compressed = AttackSimulator.apply_attack(frame, "JPEG Q=50")
    assert compressed.shape == frame.shape
    assert compressed.dtype == np.uint8


def test_apply_rotation():
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    rotated = AttackSimulator.apply_attack(frame, "Rotation 5°")
    assert rotated.shape == frame.shape
    assert rotated.dtype == np.uint8


def test_apply_scaling():
    frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    scaled = AttackSimulator.apply_attack(frame, "Scale 50%")
    assert scaled.shape == frame.shape
    assert scaled.dtype == np.uint8


def test_apply_brightness():
    frame = np.full((100, 100, 3), 128, dtype=np.uint8)
    bright = AttackSimulator.apply_attack(frame, "Brightness +20")
    assert bright.mean() > frame.mean()


def test_get_all_attacks_contains_expected():
    attacks = AttackSimulator.get_all_attacks()
    assert len(attacks) > 20
    assert "No Attack" in attacks
    assert "JPEG Q=50" in attacks


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not available")
def test_h264_attack_runs():
    frame = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
    out = AttackSimulator.apply_attack(frame, "H.264 CRF=23")
    assert out.shape == frame.shape
    assert out.dtype == np.uint8


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not available")
def test_h265_attack_runs():
    frame = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
    out = AttackSimulator.apply_attack(frame, "H.265 CRF=28")
    assert out.shape == frame.shape
    assert out.dtype == np.uint8

def test_apply_crop_keeps_size():
    frame = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
    out = AttackSimulator.apply_attack(frame, "Crop 20%")
    assert out.shape == frame.shape
    assert out.dtype == np.uint8