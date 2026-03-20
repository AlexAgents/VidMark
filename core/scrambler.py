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
Scrambling (bit permutation) based on a seed.

Security note:
- This is NOT cryptographic encryption.
- Purpose: spread payload bits and prevent trivial localized attacks.
"""

from __future__ import annotations

import hashlib
import numpy as np


class Scrambler:
    def __init__(self, seed: int):
        self.seed = int(seed) & 0xFFFFFFFF

    @classmethod
    def from_string_key(cls, key_string: str) -> "Scrambler":
        """Derive a 32-bit seed from a text key using SHA-256."""
        h = hashlib.sha256(key_string.encode("utf-8")).digest()
        seed = int.from_bytes(h[:4], "big")
        return cls(seed)

    def _perm(self, n: int) -> np.ndarray:
        rng = np.random.RandomState(self.seed)
        return rng.permutation(n)

    def scramble(self, bits: np.ndarray) -> np.ndarray:
        """
        Apply a deterministic permutation:
            scrambled[perm[i]] = bits[i]
        """
        bits = np.asarray(bits).astype(np.int32)
        n = len(bits)
        perm = self._perm(n)

        scrambled = np.zeros(n, dtype=np.int32)
        scrambled[perm] = bits  # vectorized version of the loop
        return scrambled

    def descramble(self, scrambled_bits: np.ndarray) -> np.ndarray:
        """
        Invert scramble().

        Since scramble did: scrambled[perm[i]] = original[i]
        The inverse is: original[i] = scrambled[perm[i]]
        """
        scrambled_bits = np.asarray(scrambled_bits).astype(np.int32)
        n = len(scrambled_bits)
        perm = self._perm(n)

        original = np.zeros(n, dtype=np.int32)
        original[:] = scrambled_bits[perm]  # vectorized
        return original