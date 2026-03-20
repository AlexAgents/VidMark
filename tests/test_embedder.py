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
Tests for watermark embedder + extractor integration.

We validate:
- output size preserved
- output range is clipped to [0..255]
- basic embed->extract correlation (NC) is reasonably high without attacks
- embedding is deterministic for the same seed/settings
"""

import numpy as np

from config import WatermarkSettings, StrengthPreset
from core.embedder import WatermarkEmbedder
from core.extractor import WatermarkExtractor
from core.metrics import compute_psnr, compute_nc


def _make_settings():
    s = WatermarkSettings()
    s.wavelet = "haar"
    s.dwt_level = 1
    s.block_size = 8
    s.strength_preset = StrengthPreset.BALANCED
    s.custom_delta = 35.0
    s.scramble_seed = 42
    return s


def test_embed_preserves_shape_and_range():
    """Embedding must preserve frame shape and keep values in [0..255]."""
    settings = _make_settings()
    embedder = WatermarkEmbedder(settings)

    rng = np.random.RandomState(0)
    frame = rng.randint(0, 256, size=(241, 319)).astype(np.float64)  # intentionally non-multiple sizes
    wm_bits = rng.randint(0, 2, size=200).astype(np.int32)

    watermarked, info = embedder.embed_frame(frame, wm_bits)

    assert watermarked.shape == frame.shape
    assert 0.0 <= float(watermarked.min()) <= 255.0
    assert 0.0 <= float(watermarked.max()) <= 255.0
    assert info["unique_bits"] == len(wm_bits)
    assert info["total_writes"] > 0


def test_embed_extract_basic_nc_and_psnr():
    """Without attacks, extraction should correlate well with embedded bits and PSNR should be reasonable."""
    settings = _make_settings()
    embedder = WatermarkEmbedder(settings)
    extractor = WatermarkExtractor(settings)

    rng = np.random.RandomState(123)
    frame = rng.randint(30, 226, size=(256, 256)).astype(np.float64)
    wm_bits = rng.randint(0, 2, size=240).astype(np.int32)

    watermarked, _ = embedder.embed_frame(frame, wm_bits)

    psnr = compute_psnr(frame, watermarked)
    assert psnr > 35.0, f"PSNR too low: {psnr}"

    extracted, soft, ex_info = extractor.extract_frame(watermarked, len(wm_bits))
    nc = compute_nc(wm_bits, extracted)

    # This is a fairly relaxed threshold because content/seed/delta can affect it.
    assert nc > 0.6, f"NC too low: {nc}"


def test_embed_is_deterministic_for_same_settings():
    """Same input + same settings -> identical output (deterministic)."""
    settings = _make_settings()
    embedder1 = WatermarkEmbedder(settings)
    embedder2 = WatermarkEmbedder(settings)

    rng = np.random.RandomState(7)
    frame = rng.randint(0, 256, size=(256, 256)).astype(np.float64)
    wm_bits = rng.randint(0, 2, size=128).astype(np.int32)

    wm1, _ = embedder1.embed_frame(frame, wm_bits)
    wm2, _ = embedder2.embed_frame(frame, wm_bits)

    assert np.allclose(wm1, wm2, atol=1e-9)