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
Additional integration tests for embedder/extractor.

These tests catch:
- padding alignment regressions (non-multiple sizes)
- determinism of extraction
- capacity errors on too small frames
- compatibility with smaller block sizes (e.g., 4x4)
"""

import numpy as np
import pytest

from config import WatermarkSettings, StrengthPreset
from core.embedder import WatermarkEmbedder
from core.extractor import WatermarkExtractor
from core.metrics import compute_nc


def _settings(bs=8, level=1, delta=35.0, seed=123):
    s = WatermarkSettings()
    s.wavelet = "haar"
    s.dwt_level = level
    s.block_size = bs
    s.strength_preset = StrengthPreset.CUSTOM
    s.custom_delta = float(delta)
    s.scramble_seed = int(seed)
    return s


@pytest.mark.parametrize("shape", [
    (241, 319),
    (239, 401),
    (1080, 1920),
    (721, 1281),
])
def test_embed_extract_padding_alignment_random_sizes(shape):
    settings = _settings(bs=8, level=1, delta=35.0, seed=42)
    emb = WatermarkEmbedder(settings)
    ext = WatermarkExtractor(settings)

    rng = np.random.RandomState(0)
    frame = rng.randint(0, 256, size=shape).astype(np.float64)
    bits = rng.randint(0, 2, size=240).astype(np.int32)

    wm, _ = emb.embed_frame(frame, bits)
    hard, _, _ = ext.extract_frame(wm, len(bits))

    nc = compute_nc(bits, hard)
    assert nc > 0.55, f"NC too low for shape={shape}: {nc}"


def test_extraction_is_deterministic():
    """
    Extractor uses seeded block selection; for same input it must be deterministic.

    NOTE: payload length must fit capacity, otherwise embedder should raise ValueError.
    """
    settings = _settings(bs=8, level=1, delta=35.0, seed=777)
    emb = WatermarkEmbedder(settings)
    ext = WatermarkExtractor(settings)

    rng = np.random.RandomState(1)
    frame = rng.randint(0, 256, size=(255, 257)).astype(np.float64)

    # Keep bit length safely below capacity for this shape.
    bits = rng.randint(0, 2, size=200).astype(np.int32)

    wm, _ = emb.embed_frame(frame, bits)

    hard1, soft1, _ = ext.extract_frame(wm, len(bits))
    hard2, soft2, _ = ext.extract_frame(wm, len(bits))

    assert np.array_equal(hard1, hard2)
    assert np.allclose(soft1, soft2, atol=0.0)


def test_embed_raises_capacity_error_on_too_small_frame():
    settings = _settings(bs=8, level=1, delta=35.0, seed=42)
    emb = WatermarkEmbedder(settings)

    rng = np.random.RandomState(2)
    frame = rng.randint(0, 256, size=(32, 32)).astype(np.float64)
    bits = rng.randint(0, 2, size=500).astype(np.int32)

    with pytest.raises(ValueError):
        emb.embed_frame(frame, bits)


def test_block_size_4_does_not_crash_and_uses_valid_positions():
    settings = _settings(bs=4, level=1, delta=35.0, seed=99)
    emb = WatermarkEmbedder(settings)
    ext = WatermarkExtractor(settings)

    rng = np.random.RandomState(3)
    frame = rng.randint(0, 256, size=(256, 256)).astype(np.float64)
    bits = rng.randint(0, 2, size=200).astype(np.int32)

    wm, _ = emb.embed_frame(frame, bits)
    hard, _, _ = ext.extract_frame(wm, len(bits))

    assert len(hard) == len(bits)
    nc = compute_nc(bits, hard)
    assert nc > 0.3