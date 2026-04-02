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
Payload formation and parsing.

Payload layout (bit-level):
- SYNC marker: SYNC_BITS
- UUID: UUID_BITS
- Timestamp: TIMESTAMP_BITS
- CRC16 of (SYNC || UUID || TIMESTAMP): CRC_BITS

This module keeps the exact format expected by the rest of the project.
"""

from __future__ import annotations

import time
import hashlib
import secrets
import numpy as np

from config import SYNC_MARKER, SYNC_BITS, UUID_BITS, TIMESTAMP_BITS, CRC_BITS


def generate_uuid_from_string(author_string: str) -> int:
    """Derive a stable 64-bit UUID from an author string using SHA-256."""
    h = hashlib.sha256(author_string.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def generate_random_uuid() -> int:
    """Generate a random 64-bit UUID."""
    return secrets.randbits(UUID_BITS)


def get_timestamp() -> int:
    """Get a 32-bit Unix timestamp."""
    return int(time.time()) & 0xFFFFFFFF


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """
    Pack bits (0/1) into bytes (MSB-first in each byte).
    Pads with zeros to a multiple of 8 bits.
    """
    bits = np.asarray(bits).astype(np.int32)
    padded_len = ((len(bits) + 7) // 8) * 8
    padded = np.zeros(padded_len, dtype=np.int32)
    padded[: len(bits)] = bits[:]

    out = bytearray()
    for i in range(0, padded_len, 8):
        b = 0
        for j in range(8):
            b = (b << 1) | int(padded[i + j] & 1)
        out.append(b)
    return bytes(out)


def int_to_bits(value: int, num_bits: int) -> np.ndarray:
    """Convert integer to big-endian bit array of fixed length."""
    bits = np.zeros(num_bits, dtype=np.int32)
    for i in range(num_bits):
        bits[num_bits - 1 - i] = (value >> i) & 1
    return bits


def bits_to_int(bits: np.ndarray) -> int:
    """Convert big-endian bit array to integer."""
    bits = np.asarray(bits).astype(np.int32)
    v = 0
    for b in bits:
        v = (v << 1) | int(b & 1)
    return int(v)


def compute_crc16(data_bits: np.ndarray) -> int:
    """
    CRC-16/Modbus-like implementation (polynomial 0xA001, init 0xFFFF).
    Note: This matches your existing code behavior for compatibility.
    """
    data_bytes = bits_to_bytes(data_bits)
    crc = 0xFFFF
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def form_payload(author_id: str | None = None, uuid_value: int | None = None):
    """
    Create payload bits and a human-readable info dict.

    If uuid_value is provided -> used directly (masked to UUID_BITS).
    Else if author_id provided -> derived deterministic UUID.
    Else -> random UUID.
    """
    if uuid_value is not None:
        uuid_val = int(uuid_value) & ((1 << UUID_BITS) - 1)
    elif author_id:
        uuid_val = generate_uuid_from_string(author_id)
    else:
        uuid_val = generate_random_uuid()

    ts = get_timestamp()

    sync_bits = int_to_bits(SYNC_MARKER, SYNC_BITS)
    uuid_bits = int_to_bits(uuid_val, UUID_BITS)
    ts_bits = int_to_bits(ts, TIMESTAMP_BITS)

    data_for_crc = np.concatenate([sync_bits, uuid_bits, ts_bits])
    crc_val = compute_crc16(data_for_crc)
    crc_bits = int_to_bits(crc_val, CRC_BITS)

    payload = np.concatenate([sync_bits, uuid_bits, ts_bits, crc_bits])

    info = {
        "uuid": uuid_val,
        "uuid_hex": format(uuid_val, "016x"),
        "timestamp": ts,
        "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts)),
        "crc": crc_val,
        "total_bits": int(len(payload)),
    }
    return payload, info


def parse_payload(payload_bits: np.ndarray):
    """
    Parse payload into fields and validate SYNC + CRC.
    Returns (info_dict, valid_bool).
    """
    expected_len = SYNC_BITS + UUID_BITS + TIMESTAMP_BITS + CRC_BITS
    payload_bits = np.asarray(payload_bits).astype(np.int32)

    if len(payload_bits) < expected_len:
        return {"error": "Payload too short"}, False

    idx = 0
    sync = bits_to_int(payload_bits[idx: idx + SYNC_BITS]); idx += SYNC_BITS
    uuid_val = bits_to_int(payload_bits[idx: idx + UUID_BITS]); idx += UUID_BITS
    ts = bits_to_int(payload_bits[idx: idx + TIMESTAMP_BITS]); idx += TIMESTAMP_BITS
    crc_extracted = bits_to_int(payload_bits[idx: idx + CRC_BITS])

    data_for_crc = payload_bits[: SYNC_BITS + UUID_BITS + TIMESTAMP_BITS]
    crc_computed = compute_crc16(data_for_crc)

    valid = (sync == SYNC_MARKER) and (crc_extracted == crc_computed)

    info = {
        "sync_valid": sync == SYNC_MARKER,
        "sync_value": format(sync, "02x"),
        "uuid": uuid_val,
        "uuid_hex": format(uuid_val, "016x"),
        "timestamp": ts,
        "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))
        if 0 < ts < 2**32 - 1 else "N/A",
        "crc_valid": crc_extracted == crc_computed,
        "crc_extracted": format(crc_extracted, "04x"),
        "crc_computed": format(crc_computed, "04x"),
    }
    return info, bool(valid)