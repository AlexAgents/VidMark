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
Key file management.

The key file stores:
- Algorithm name
- Embedding parameters (wavelet, dwt_level, block_size, delta, presets)
- Security parameters (scramble_seed, ECC type, rs_nsym)
- Video info and extraction hints (payload_length_bits)
- Payload info (author, uuid, timestamp) for verification UX

This file format is intentionally JSON and human-readable.

NOTE: The keyfile is CRITICAL for watermark extraction. Without it,
the scramble seed cannot be reconstructed and extraction will fail.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from config import WatermarkSettings, StrengthPreset, APP_VERSION

logger = logging.getLogger(__name__)

# FIX: Required top-level keys for a valid keyfile
_REQUIRED_KEYFILE_SECTIONS = ("params", "security", "extraction_hints")


def save_keyfile(filepath: str,
                 settings: WatermarkSettings,
                 video_info: dict,
                 embed_info: dict,
                 payload_info: dict,
                 author_text: str = "") -> str:
    data = {
        "version": APP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "DWT-DCT-QIM",
        "params": {
            "wavelet": settings.wavelet,
            "dwt_level": settings.dwt_level,
            "block_size": settings.block_size,
            "strength_preset": settings.strength_preset.value,
            "base_delta": settings.get_delta(),
        },
        "security": {
            "scramble_seed": settings.scramble_seed,
            "ecc": "Reed-Solomon",
            "rs_nsym": settings.rs_nsym,
        },
        "video_info": {
            "original_width": video_info.get("width", 0),
            "original_height": video_info.get("height", 0),
            "fps": video_info.get("fps", 30.0),
            "frame_count": video_info.get("frame_count", 0),
        },
        "extraction_hints": {
            "payload_length_bits": settings.payload_length_bits,
        },
        "payload_info": {
            "author_text": author_text,
            "uuid_hex": payload_info.get("uuid_hex", ""),
            "timestamp": payload_info.get("timestamp", 0),
            "timestamp_str": payload_info.get("timestamp_str", ""),
            "total_payload_bits": payload_info.get("total_bits", 0),
        },
        "embed_info": embed_info or {},
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_keyfile(filepath: str):
    """
    Load keyfile and reconstruct WatermarkSettings.

    Last FIX: Validates that required sections exist in the keyfile.
    Raises ValueError if the keyfile is corrupted or from an incompatible version.

    Note:
    - The keyfile stores base_delta, so we set StrengthPreset.CUSTOM to preserve it.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # FIX: Validate required sections
    missing = [key for key in _REQUIRED_KEYFILE_SECTIONS if key not in data]
    if missing:
        raise ValueError(
            f"Invalid keyfile: missing required sections: {', '.join(missing)}. "
            f"The file may be corrupted or from an incompatible version."
        )

    s = WatermarkSettings()

    p = data.get("params", {})
    s.wavelet = p.get("wavelet", s.wavelet)
    s.dwt_level = int(p.get("dwt_level", s.dwt_level))
    s.block_size = int(p.get("block_size", s.block_size))

    sp = p.get("strength_preset", "balanced")
    try:
        s.strength_preset = StrengthPreset(sp)
    except ValueError:
        s.strength_preset = StrengthPreset.BALANCED

    # Preserve exact delta stored in the keyfile
    s.custom_delta = float(p.get("base_delta", s.custom_delta))
    s.strength_preset = StrengthPreset.CUSTOM

    sec = data.get("security", {})
    s.scramble_seed = int(sec.get("scramble_seed", s.scramble_seed))
    s.rs_nsym = int(sec.get("rs_nsym", s.rs_nsym))

    hints = data.get("extraction_hints", {})
    s.payload_length_bits = int(hints.get("payload_length_bits", s.payload_length_bits))

    return s, data