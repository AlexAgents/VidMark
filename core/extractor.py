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
DWT-DCT Watermark Extractor (QIM from DCT coefficients of DWT-LL subband)

Must match the embedder exactly:
- Same padding rule: multiple of (2^level * block_size)
- Same DWT wavelet/level and mode='symmetric'
- Same block selection RNG seed and target_blocks rule
- Same coefficient position schedule: positions[i % len(positions)]
"""

import numpy as np
import pywt
from scipy.fft import dctn
from typing import Tuple
import logging

from config import WatermarkSettings, MID_FREQ_POSITIONS

logger = logging.getLogger(__name__)


class WatermarkExtractor:
    def __init__(self, settings: WatermarkSettings):
        self.settings = settings
        self.block_size = int(settings.block_size)
        self.wavelet = settings.wavelet
        self.dwt_level = int(settings.dwt_level)
        self.delta = float(settings.get_delta())
        self.seed = int(settings.scramble_seed)

        if self.block_size <= 0:
            raise ValueError("block_size must be > 0")
        if self.dwt_level <= 0:
            raise ValueError("dwt_level must be >= 1")
        if self.delta <= 0:
            raise ValueError("Delta must be > 0")

    def extract_frame(self, frame_y: np.ndarray,
                      num_bits: int) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        Extract watermark bits from one luminance (Y) frame.

        Returns:
            hard_bits: int32 array of shape (num_bits,)
            soft_bits: float64 array of shape (num_bits,) (signed confidence)
            info: dict with 'confidence' = mean(abs(soft_bits))
        """
        if num_bits <= 0:
            return (
                np.zeros(0, dtype=np.int32),
                np.zeros(0, dtype=np.float64),
                {"confidence": 0.0},
            )

        h, w = frame_y.shape
        work = frame_y.astype(np.float64, copy=True)

        # Must match embedder: pad to multiple of (2^level * block_size)
        align = (2 ** self.dwt_level) * self.block_size
        pad_h = (align - (h % align)) % align
        pad_w = (align - (w % align)) % align
        if pad_h or pad_w:
            work = np.pad(work, ((0, pad_h), (0, pad_w)), mode="reflect")

        coeffs = pywt.wavedec2(work, self.wavelet, level=self.dwt_level, mode="symmetric")
        ll = coeffs[0].astype(np.float64)

        if ll.shape[0] < self.block_size or ll.shape[1] < self.block_size:
            hard = np.zeros(num_bits, dtype=np.int32)
            soft = np.zeros(num_bits, dtype=np.float64)
            return hard, soft, {"confidence": 0.0}

        soft_bits = self._extract_dct(ll, num_bits)
        hard_bits = (soft_bits > 0).astype(np.int32)

        info = {"confidence": float(np.mean(np.abs(soft_bits))) if len(soft_bits) else 0.0}
        return hard_bits, soft_bits, info

    def _valid_positions(self) -> list[tuple[int, int]]:
        bs = self.block_size
        return [(r, c) for (r, c) in MID_FREQ_POSITIONS if r < bs and c < bs]

    def _extract_dct(self, band: np.ndarray, num_bits: int) -> np.ndarray:
        """
        Extract soft bits from band using the same block selection
        and coefficient schedule as embedder.
        Accumulates soft evidence per bit index and returns the average.
        """
        bh, bw = band.shape
        bs = self.block_size

        nrows = bh // bs
        ncols = bw // bs
        total_blocks = nrows * ncols

        accum = np.zeros(num_bits, dtype=np.float64)
        counts = np.zeros(num_bits, dtype=np.float64)

        if total_blocks <= 0:
            return accum

        positions = self._valid_positions()
        if not positions:
            return accum

        # Must match embedder's target_blocks policy
        target_blocks = max(num_bits * 2, total_blocks // 4)
        target_blocks = min(target_blocks, total_blocks)

        rng = np.random.RandomState(self.seed)
        selected_blocks = rng.permutation(total_blocks)[:target_blocks]

        for i, block_idx in enumerate(selected_blocks):
            r0 = (block_idx // ncols) * bs
            c0 = (block_idx % ncols) * bs

            block = band[r0:r0 + bs, c0:c0 + bs].copy()
            dct_block = dctn(block, type=2, norm="ortho")

            bit_idx = i % num_bits
            pos = positions[i % len(positions)]
            val = float(dct_block[pos])

            soft = self._qim_extract(val)
            accum[bit_idx] += soft
            counts[bit_idx] += 1.0

        mask = counts > 0
        out = np.zeros(num_bits, dtype=np.float64)
        out[mask] = accum[mask] / counts[mask]
        return out

    def _qim_extract(self, val: float) -> float:
        """
        Soft QIM decision:
        - Compute distances to q0 (bit=0 lattice) and q1 (bit=1 lattice)
        - Return signed confidence (>0 means closer to bit=1)
        - Normalization by (d/4) keeps magnitudes comparable across deltas
        """
        d = self.delta

        q0 = np.round(val / d) * d
        dist0 = abs(val - q0)

        q1 = np.round((val - d / 2.0) / d) * d + d / 2.0
        dist1 = abs(val - q1)

        denom = max(d / 4.0, 1e-9)

        if dist1 < dist0:
            return (dist0 - dist1) / denom
        return -(dist1 - dist0) / denom