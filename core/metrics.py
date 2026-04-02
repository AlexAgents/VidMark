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
Quality and extraction metrics:
- PSNR: image/video quality metric
- SSIM: structural similarity (simple implementation)
- NC: normalized correlation between bit sequences (supports hard/soft)
- BER: bit error rate
"""

from __future__ import annotations

import numpy as np
import cv2


def compute_psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """Compute PSNR for 8-bit images (assumes range 0..255)."""
    o = original.astype(np.float64)
    m = modified.astype(np.float64)
    mse = float(np.mean((o - m) ** 2))
    if mse == 0.0:
        return float("inf")
    return float(10.0 * np.log10((255.0 ** 2) / mse))


def compute_ssim(original: np.ndarray, modified: np.ndarray) -> float:
    """
    SSIM for grayscale or BGR images.
    Lightweight implementation using Gaussian blur to estimate statistics.
    """
    if len(original.shape) == 3:
        original = cv2.cvtColor(original.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        modified = cv2.cvtColor(modified.astype(np.uint8), cv2.COLOR_BGR2GRAY)

    o = original.astype(np.float64)
    m = modified.astype(np.float64)

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    mu1 = cv2.GaussianBlur(o, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(m, (11, 11), 1.5)

    # FIX: clamp variance to >= 0 to avoid floating-point negative values
    s1 = np.maximum(cv2.GaussianBlur(o ** 2, (11, 11), 1.5) - mu1 ** 2, 0)
    s2 = np.maximum(cv2.GaussianBlur(m ** 2, (11, 11), 1.5) - mu2 ** 2, 0)
    s12 = cv2.GaussianBlur(o * m, (11, 11), 1.5) - mu1 * mu2

    ssim_map = ((2 * mu1 * mu2 + C1) * (2 * s12 + C2)) / (
        (mu1 ** 2 + mu2 ** 2 + C1) * (s1 + s2 + C2)
    )
    return float(np.mean(ssim_map))


def compute_nc(orig: np.ndarray, extr: np.ndarray) -> float:
    """
    Normalized correlation between two sequences.
    Supports hard bits {0,1} and soft float values.
    """
    o = np.asarray(orig)
    e = np.asarray(extr)
    n = min(len(o), len(e))
    if n <= 0:
        return 0.0

    o = o[:n].astype(np.float64)
    e = e[:n].astype(np.float64)

    def _maybe_map_bits(x: np.ndarray) -> np.ndarray:
        u = np.unique(x)
        if u.size <= 2 and np.all(np.isin(u, [0.0, 1.0])):
            return x * 2.0 - 1.0
        return x

    o2 = _maybe_map_bits(o)
    e2 = _maybe_map_bits(e)

    denom = float(np.sqrt(np.sum(o2 ** 2) * np.sum(e2 ** 2)))
    if denom <= 0:
        return 0.0
    nc = float(np.sum(o2 * e2) / denom)
    return float(np.clip(nc, -1.0, 1.0))


def compute_ber(orig: np.ndarray, extr: np.ndarray) -> float:
    """Bit Error Rate between two hard-bit arrays."""
    o = np.asarray(orig).astype(np.int32)
    e = np.asarray(extr).astype(np.int32)
    n = min(len(o), len(e))
    if n <= 0:
        return 1.0
    return float(np.sum(o[:n] != e[:n]) / n)