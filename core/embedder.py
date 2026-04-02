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
DWT-DCT Watermark Embedder (QIM in DCT coefficients of DWT-LL subband)

Pipeline:
1) Pad frame to multiple of (2^dwt_level * block_size).
2) DWT (wavedec2) with explicit boundary mode='symmetric'.
3) Take LL subband.
4) Split LL into blocks, apply orthonormal DCT-II.
5) Embed 1 bit per selected block using QIM into ONE DCT coefficient.
6) Inverse DCT, replace LL, inverse DWT, unpad back to original frame size.
"""

import numpy as np
import pywt
from scipy.fft import dctn, idctn
from typing import Tuple
import logging

from config import WatermarkSettings, MID_FREQ_POSITIONS

logger = logging.getLogger(__name__)


class WatermarkEmbedder:
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

    def embed_frame(self, frame_y: np.ndarray,
                    watermark_bits: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Embed watermark_bits into one luminance (Y) frame.

        Returns:
            result_y: float64 Y channel in [0..255]
            info: dict with keys: unique_bits, total_writes, used_blocks
        """
        if watermark_bits is None or len(watermark_bits) == 0:
            raise ValueError("watermark_bits is empty")

        h, w = frame_y.shape
        work = frame_y.astype(np.float64, copy=True)

        # Pad to multiple of (2^level * block_size) to ensure LL is block-aligned
        align = (2 ** self.dwt_level) * self.block_size
        pad_h = (align - (h % align)) % align
        pad_w = (align - (w % align)) % align
        if pad_h or pad_w:
            work = np.pad(work, ((0, pad_h), (0, pad_w)), mode="reflect")

        # DWT with fixed boundary mode for reproducibility
        coeffs = pywt.wavedec2(work, self.wavelet, level=self.dwt_level, mode="symmetric")
        ll = coeffs[0].astype(np.float64, copy=True)

        if ll.shape[0] < self.block_size or ll.shape[1] < self.block_size:
            raise ValueError(
                f"DWT level too high / frame too small: LL={ll.shape} < block_size={self.block_size}"
            )

        ll_mod, total_writes, used_blocks = self._embed_dct(ll, watermark_bits)
        coeffs[0] = ll_mod

        # Inverse DWT, unpad back to original size
        result_raw = pywt.waverec2(coeffs, self.wavelet, mode="symmetric")
        result_raw = result_raw[:h, :w]
        result_y = np.clip(result_raw, 0.0, 255.0)

        info = {
            "unique_bits": int(len(watermark_bits)),
            "total_writes": int(total_writes),
            "used_blocks": int(used_blocks),
        }
        return result_y, info

    def _valid_positions(self) -> list[tuple[int, int]]:
        """Filter MID_FREQ_POSITIONS that are inside current block_size."""
        bs = self.block_size
        return [(r, c) for (r, c) in MID_FREQ_POSITIONS if r < bs and c < bs]

    def _embed_dct(self, band: np.ndarray,
                   bits: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """
        Embed watermark bits into a 2D band via block DCT + QIM.

        Strategy:
        - Select a deterministic subset of blocks using seed.
        - Embed 1 bit per selected block.
        - Coefficient position changes cyclically across MID_FREQ_POSITIONS.
        - Bits are repeated across blocks for redundancy.
        """
        bh, bw = band.shape
        bs = self.block_size

        nrows = bh // bs
        ncols = bw // bs
        total_blocks = nrows * ncols

        modified = band.copy()
        if total_blocks <= 0:
            return modified, 0, 0

        positions = self._valid_positions()
        if not positions:
            raise ValueError(f"No valid MID_FREQ_POSITIONS for block_size={bs}")

        # Redundancy: at least 2 blocks per bit, up to total_blocks
        target_blocks = max(len(bits) * 2, total_blocks // 4)
        target_blocks = min(target_blocks, total_blocks)

        rng = np.random.RandomState(self.seed)
        selected_blocks = rng.permutation(total_blocks)[:target_blocks]

        if len(selected_blocks) < len(bits):
            raise ValueError(
                f"Capacity error: need {len(bits)} blocks, got {len(selected_blocks)}")

        writes = 0
        for i, block_idx in enumerate(selected_blocks):
            r0 = (block_idx // ncols) * bs
            c0 = (block_idx % ncols) * bs

            block = modified[r0:r0 + bs, c0:c0 + bs].copy()
            dct_block = dctn(block, type=2, norm="ortho")

            bit_idx = i % len(bits)
            bit = int(bits[bit_idx] & 1)

            pos = positions[i % len(positions)]
            val = float(dct_block[pos])
            dct_block[pos] = self._qim_embed(val, bit)

            block_rec = idctn(dct_block, type=2, norm="ortho")
            modified[r0:r0 + bs, c0:c0 + bs] = block_rec
            writes += 1

        return modified, writes, len(selected_blocks)

    def _qim_embed(self, val: float, bit: int) -> float:
        """
        2-coset QIM:
          bit=0 -> quantize to multiples of d
          bit=1 -> quantize to multiples of d with half-step offset (d/2)
        """
        d = self.delta
        if bit == 0:
            return np.round(val / d) * d
        return np.round((val - d / 2.0) / d) * d + d / 2.0