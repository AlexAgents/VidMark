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
Tests for watermark extractor outputs (length, binary hard bits, confidence).
"""

import numpy as np
from config import WatermarkSettings
from core.extractor import WatermarkExtractor


def test_extractor_output_length_and_types():
    """Extractor must return arrays of expected length and types."""
    settings = WatermarkSettings()
    extractor = WatermarkExtractor(settings)

    rng = np.random.RandomState(0)
    frame = rng.randint(0, 256, size=(256, 256)).astype(np.float64)

    num_bits = 100
    hard, soft, info = extractor.extract_frame(frame, num_bits)

    assert len(hard) == num_bits
    assert len(soft) == num_bits
    assert hard.dtype == np.int32
    assert soft.dtype == np.float64
    assert isinstance(info, dict)
    assert "confidence" in info


def test_extractor_hard_bits_are_binary():
    """Hard bits must be subset of {0,1}."""
    settings = WatermarkSettings()
    extractor = WatermarkExtractor(settings)

    rng = np.random.RandomState(1)
    frame = rng.randint(0, 256, size=(256, 256)).astype(np.float64)

    hard, _, _ = extractor.extract_frame(frame, 50)
    assert set(np.unique(hard)).issubset({0, 1})