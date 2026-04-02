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
Tests for core.ecc: RS encode/decode should round-trip in the error-free case.
"""

import numpy as np
from core.ecc import ECCCodec


def test_ecc_encode_decode_no_errors_roundtrip():
    """RS encode then decode without corruption should restore the message."""
    ecc = ECCCodec(nsym=32)
    original = np.array([1, 0, 1, 1, 0, 0, 1, 0] * 15, dtype=np.int32)  # 120 bits

    encoded = ecc.encode(original)
    decoded, corrected, success = ecc.decode(encoded)

    assert success
    assert np.array_equal(decoded[: len(original)], original)


def test_ecc_encoded_length_bits_matches_helper():
    """Encoded length helper must match actual encoded output length."""
    ecc = ECCCodec(nsym=32)
    original = np.random.RandomState(0).randint(0, 2, size=120).astype(np.int32)

    encoded = ecc.encode(original)
    expected = ecc.get_encoded_length_bits(len(original))
    assert len(encoded) == expected