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
Tests for core.metrics: PSNR/BER/NC basic invariants.

Note: compute_nc supports both hard bits and soft values. Here we test hard bits primarily.
"""

import numpy as np
from core.metrics import compute_psnr, compute_nc, compute_ber


def test_psnr_identical_is_inf():
    """PSNR for identical images should be +inf."""
    a = np.zeros((64, 64), dtype=np.uint8)
    b = np.zeros((64, 64), dtype=np.uint8)
    assert compute_psnr(a, b) == float("inf")


def test_ber_identical_is_zero():
    """BER for identical sequences should be 0."""
    a = np.array([0, 1, 1, 0, 1], dtype=np.int32)
    b = np.array([0, 1, 1, 0, 1], dtype=np.int32)
    assert compute_ber(a, b) == 0.0


def test_nc_identical_hard_bits_is_one():
    """NC for identical hard-bit sequences should be ~1."""
    a = np.array([0, 1, 1, 0, 1], dtype=np.int32)
    b = np.array([0, 1, 1, 0, 1], dtype=np.int32)
    assert abs(compute_nc(a, b) - 1.0) < 1e-9


def test_nc_soft_and_hard_are_supported():
    """NC should accept soft values without crashing and return a bounded result."""
    hard = np.array([0, 1, 0, 1, 1, 0], dtype=np.int32)
    soft = np.array([-0.2, 0.9, -1.5, 0.3, 2.0, -0.1], dtype=np.float64)
    nc = compute_nc(hard, soft)
    assert -1.0 <= nc <= 1.0