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
Tests for core.payload: payload formation, parsing, CRC and length invariants.
"""

import numpy as np
from core.payload import form_payload, parse_payload
from config import DEFAULT_PAYLOAD_BITS


def test_form_payload_length_is_constant():
    """Payload bit-length must match config constant."""
    payload, info = form_payload(author_id="alice")
    assert len(payload) == DEFAULT_PAYLOAD_BITS
    assert info["total_bits"] == DEFAULT_PAYLOAD_BITS


def test_payload_roundtrip_parses_and_validates_crc():
    """Formed payload must pass parse_payload CRC and SYNC validation."""
    payload, info = form_payload(author_id="tester")
    parsed, ok = parse_payload(payload)
    assert ok
    assert parsed["sync_valid"]
    assert parsed["crc_valid"]
    assert parsed["uuid_hex"] == info["uuid_hex"]
    assert parsed["timestamp"] == info["timestamp"]


def test_payload_parse_rejects_short_input():
    """Too short bitstream must return error and ok=False."""
    short = np.zeros(10, dtype=np.int32)
    parsed, ok = parse_payload(short)
    assert not ok
    assert "error" in parsed