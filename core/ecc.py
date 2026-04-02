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
ECC (Error Correction Code) layer using Reed-Solomon.

We represent payload as bits, convert to bytes, then RS-encode bytes, then convert back to bits.

Important:
- RS works on bytes; bit errors after extraction become byte errors after packing.
- nsym controls the number of parity bytes added (higher = more redundancy).
"""

from __future__ import annotations

import numpy as np
from reedsolo import RSCodec, ReedSolomonError

from config import RS_NSYM


class ECCCodec:
    def __init__(self, nsym: int = RS_NSYM):
        self.nsym = int(nsym)
        self.rs = RSCodec(self.nsym)

    def encode(self, bits: np.ndarray) -> np.ndarray:
        """RS-encode bits (packed into bytes) and return encoded bits."""
        data_bytes = self._bits_to_bytes(bits)
        encoded = bytes(self.rs.encode(data_bytes))
        return self._bytes_to_bits(encoded)

    def decode(self, bits: np.ndarray):
        """
        RS-decode bits (packed into bytes).
        Returns: (decoded_bits, corrected_count, success)
        corrected_count is not reliably available from reedsolo here; kept for compatibility.
        """
        data_bytes = bytearray(self._bits_to_bytes(bits))
        try:
            decoded_msg = self.rs.decode(data_bytes)
            if isinstance(decoded_msg, tuple):
                decoded_data = bytes(decoded_msg[0])
            else:
                decoded_data = bytes(decoded_msg)

            decoded_bits = self._bytes_to_bits(decoded_data)
            return decoded_bits, 0, True

        except ReedSolomonError:
            # Fallback: strip parity bytes and return raw portion if possible
            raw_len = len(data_bytes) - self.nsym
            if raw_len > 0:
                return self._bytes_to_bits(bytes(data_bytes[:raw_len])), -1, False
            return np.asarray(bits).astype(np.int32), -1, False

    def get_encoded_length_bits(self, input_bits: int) -> int:
        """
        Given input bit length, compute encoded bit length after RS encoding.
        """
        input_bytes = (int(input_bits) + 7) // 8
        return (input_bytes + self.nsym) * 8

    @staticmethod
    def _bits_to_bytes(bits: np.ndarray) -> bytes:
        """
        Pack bits (MSB-first) into bytes. Pads zeros to multiple of 8 bits.
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

    @staticmethod
    def _bytes_to_bits(data: bytes) -> np.ndarray:
        """Unpack bytes into bits (MSB-first)."""
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return np.array(bits, dtype=np.int32)