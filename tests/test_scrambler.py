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
Tests for core.scrambler: scramble/descramble must be inverse operations.
"""

import numpy as np
from core.scrambler import Scrambler


def test_scramble_descramble_roundtrip():
    """Scramble then descramble must restore original bits."""
    rng = np.random.RandomState(123)
    bits = rng.randint(0, 2, size=376).astype(np.int32)

    s = Scrambler(12345)
    scrambled = s.scramble(bits)
    restored = s.descramble(scrambled)

    assert np.array_equal(bits, restored)


def test_scramble_is_deterministic_for_same_seed():
    """Same seed and same input -> same scrambled output."""
    rng = np.random.RandomState(42)
    bits = rng.randint(0, 2, size=200).astype(np.int32)

    s1 = Scrambler(999)
    s2 = Scrambler(999)
    assert np.array_equal(s1.scramble(bits), s2.scramble(bits))


def test_scramble_changes_bits_positions():
    """Scrambling should typically change at least one position (not identity) for random input."""
    rng = np.random.RandomState(7)
    bits = rng.randint(0, 2, size=128).astype(np.int32)

    s = Scrambler(123)
    scrambled = s.scramble(bits)

    # It's possible but extremely unlikely to be identical for random bits/permutation.
    assert not np.array_equal(bits, scrambled)