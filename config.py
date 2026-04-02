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
config.py

Global configuration for VidMark.

This module contains:
- Application constants
- Default watermarking parameters
- Presets and compatibility hints
- Persistent directories for temp data and user settings
"""

from __future__ import annotations

import os
import json
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StrengthPreset(Enum):
    """User-friendly watermark strength presets."""
    INVISIBLE = "invisible"
    BALANCED = "balanced"
    ROBUST = "robust"
    CUSTOM = "custom"


class ECCType(Enum):
    """Supported ECC types (currently only Reed-Solomon).
    Placeholder for future extensibility."""
    REED_SOLOMON = "Reed-Solomon"


# ----------------------------
# Application metadata
# ----------------------------
APP_NAME = "VidMark"
APP_VERSION = "1.0.0"
APP_AUTHOR = "AlexAgents"
APP_DESCRIPTION = "Video Watermark Shield — Robust invisible video watermarking tool"

WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 620


# ----------------------------
# File format filters
# ----------------------------
SUPPORTED_VIDEO_FORMATS = [
    "*.mp4", "*.avi", "*.mkv", "*.mov", "*.webm",
    "*.MP4", "*.AVI", "*.MKV", "*.MOV", "*.WEBM"
]
VIDEO_FILTER = "Video Files ({})".format(" ".join(SUPPORTED_VIDEO_FORMATS))


# ----------------------------
# Payload layout (bit lengths)
# ----------------------------
SYNC_MARKER = 0xA5
SYNC_BITS = 8

UUID_BITS = 64
TIMESTAMP_BITS = 32

CRC_BITS = 16

DEFAULT_PAYLOAD_BITS = SYNC_BITS + UUID_BITS + TIMESTAMP_BITS + CRC_BITS  # 120


# ----------------------------
# ECC defaults
# ----------------------------
RS_NSYM = 32


# ----------------------------
# Watermark algorithm defaults
# ----------------------------
DEFAULT_WAVELET = "haar"
DEFAULT_DWT_LEVEL = 1
DEFAULT_DCT_BLOCK_SIZE = 8

# QIM delta per strength preset.
STRENGTH_DELTAS = {
    StrengthPreset.INVISIBLE: 20.0,
    StrengthPreset.BALANCED: 35.0,
    StrengthPreset.ROBUST: 55.0,
}

# Output quality presets mapped to CRF.
OUTPUT_QUALITY = {
    "lossless": 0,
    "high": 4,
    "standard": 18,
}

# Normalized correlation thresholds
NC_GOOD = 0.85
NC_WARNING = 0.70

# Extraction defaults
DEFAULT_EXTRACT_FRAMES = 15
MAX_EXTRACT_FRAMES = 30
MIN_EXTRACT_FRAMES = 3


# ----------------------------
# Mid-frequency DCT coefficient positions (shared by embedder & extractor)
# ----------------------------
# Last fix: Centralized here to avoid duplication between embedder.py and extractor.py.
# These are candidate (row, col) positions within a DCT block; filtered by block_size at runtime.
MID_FREQ_POSITIONS = [
    (0, 3), (1, 2), (2, 1), (3, 0),
    (0, 4), (1, 3), (2, 2), (3, 1), (4, 0),
]


# ----------------------------
# Persistent directories
# ----------------------------
TEMP_DIR = os.path.join(os.path.expanduser("~"), ".vws_temp")
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".vws_settings")
LANGUAGE_FILE = os.path.join(SETTINGS_DIR, "language.json")


def ensure_dirs():
    """Create persistent directories. Call from main() instead of module-level.
    Avoids side effects on import (important for tests and CI)."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(SETTINGS_DIR, exist_ok=True)

def cleanup_temp_dir(max_age_hours: int = 24):
    """
    Remove temp files older than max_age_hours from TEMP_DIR.
    LAst fix: Prevents unbounded accumulation of temp files after crashes/cancels.
    Called from main() at startup.
    """
    import time
    try:
        if not os.path.isdir(TEMP_DIR):
            return
        now = time.time()
        cutoff = max_age_hours * 3600
        for filename in os.listdir(TEMP_DIR):
            filepath = os.path.join(TEMP_DIR, filename)
            if os.path.isfile(filepath):
                try:
                    if (now - os.path.getmtime(filepath)) > cutoff:
                        os.remove(filepath)
                        logger.debug("Cleaned up old temp file: %s", filepath)
                except Exception:
                    pass
    except Exception as e:
        logger.warning("Failed to cleanup temp dir: %s", e)

# ----------------------------
# Wavelet compatibility hints (UX guidance)
# ----------------------------
WAVELET_COMPATIBILITY = {
    "haar": {
        "levels": {1: "excellent", 2: "doubtful", 3: "poor"},
        "note_en": "Best choice. Simple, fast, most robust after compression.",
        "note_ru": "Лучший выбор. Простой, быстрый, наиболее устойчив после сжатия.",
        "recommended_delta_min": 25,
    },
    "db2": {
        "levels": {1: "excellent", 2: "doubtful", 3: "poor"},
        "note_en": "Good choice. Slightly better frequency separation than Haar.",
        "note_ru": "Хороший выбор. Чуть лучшее частотное разделение чем Haar.",
        "recommended_delta_min": 30,
    },
    "db4": {
        "levels": {1: "doubtful", 2: "doubtful", 3: "poor"},
        "note_en": "Acceptable. Needs higher delta. Level 1 recommended.",
        "note_ru": "Приемлемо. Требуется большая дельта. Рекомендуется уровень 1.",
        "recommended_delta_min": 40,
    },
    "db6": {
        "levels": {1: "doubtful", 2: "poor", 3: "poor"},
        "note_en": "Not recommended. Long filter causes boundary effects.",
        "note_ru": "Не рекомендуется. Длинный фильтр вызывает граничные эффекты.",
        "recommended_delta_min": 50,
    },
    "bior4.4": {
        "levels": {1: "doubtful", 2: "excellent", 3: "poor"},
        "note_en": "Good at level 2 with balanced/robust delta.",
        "note_ru": "Хорош на уровне 2 со сбалансированной/устойчивой дельтой.",
        "recommended_delta_min": 30,
    },
    "coif2": {
        "levels": {1: "poor", 2: "poor", 3: "poor"},
        "note_en": "NOT recommended. Poor robustness after video compression.",
        "note_ru": "НЕ рекомендуется. Плохая устойчивость после видеосжатия.",
        "recommended_delta_min": 60,
    },
}


# ----------------------------
# UI presets
# ----------------------------
# NOTE: scramble_seed=42 is a BASE seed only. At embedding time it is XOR-ed with
# the UUID and timestamp to produce a unique per-watermark seed. The keyfile is
# REQUIRED for extraction because it stores the exact UUID/timestamp needed to
# reconstruct the seed. Without the keyfile, recovery is impossible.

SETTINGS_PRESETS = {
    "recommended": {
        "name_en": "Recommended (Balanced)",
        "name_ru": "Рекомендуемый (Баланс)",
        "wavelet": "haar",
        "dwt_level": 1,
        "block_size": 8,
        "strength_preset": "balanced",
        "custom_delta": 35.0,
        "output_quality": "standard",
        "custom_crf": 18,
        "scramble_seed": 42,
        "rs_nsym": 32,
        "extract_frames": 15,
    },
    "maximum_robustness": {
        "name_en": "Maximum Robustness",
        "name_ru": "Максимальная устойчивость",
        "wavelet": "haar",
        "dwt_level": 1,
        "block_size": 8,
        "strength_preset": "robust",
        "custom_delta": 55.0,
        "output_quality": "high",
        "custom_crf": 4,
        "scramble_seed": 42,
        "rs_nsym": 48,
        "extract_frames": 20,
    },
    "invisible": {
        "name_en": "Maximum Invisibility",
        "name_ru": "Максимальная невидимость",
        "wavelet": "haar",
        "dwt_level": 1,
        "block_size": 8,
        "strength_preset": "invisible",
        "custom_delta": 20.0,
        "output_quality": "lossless",
        "custom_crf": 0,
        "scramble_seed": 42,
        "rs_nsym": 32,
        "extract_frames": 20,
    },
    "fast": {
        "name_en": "Fast Processing",
        "name_ru": "Быстрая обработка",
        "wavelet": "haar",
        "dwt_level": 1,
        "block_size": 8,
        "strength_preset": "balanced",
        "custom_delta": 35.0,
        "output_quality": "standard",
        "custom_crf": 18,
        "scramble_seed": 42,
        "rs_nsym": 16,
        "extract_frames": 5,
    },
}


# ----------------------------
# Language persistence helpers
# ----------------------------
def get_saved_language() -> str:
    """Load saved language setting. Returns 'en' on any failure."""
    try:
        if os.path.exists(LANGUAGE_FILE):
            with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return str(data.get("language", "en"))
    except Exception as e:
        logger.warning("Failed to load language setting: %s", e)
    return "en"


def save_language(lang: str):
    """Persist language setting to disk (best-effort)."""
    try:
        with open(LANGUAGE_FILE, "w", encoding="utf-8") as f:
            json.dump({"language": str(lang)}, f)
    except Exception as e:
        logger.warning("Failed to save language setting: %s", e)


# ----------------------------
# Main settings object
# ----------------------------
@dataclass
class WatermarkSettings:
    """
    Watermark algorithm parameters.

    Note:
    - get_delta() returns a preset delta unless StrengthPreset.CUSTOM is selected.
    - When loading from keyfile we force CUSTOM and set custom_delta from stored base_delta
      to exactly reproduce embedding parameters.
    """
    wavelet: str = DEFAULT_WAVELET
    dwt_level: int = DEFAULT_DWT_LEVEL
    block_size: int = DEFAULT_DCT_BLOCK_SIZE

    strength_preset: StrengthPreset = StrengthPreset.BALANCED

    custom_delta: float = 35.0

    scramble_seed: int = 42

    ecc_type: ECCType = ECCType.REED_SOLOMON
    rs_nsym: int = RS_NSYM

    extract_frames: int = DEFAULT_EXTRACT_FRAMES

    output_quality: str = "standard"
    custom_crf: int = 18

    payload_length_bits: int = DEFAULT_PAYLOAD_BITS

    def get_delta(self) -> float:
        """Return effective QIM delta based on strength preset."""
        if self.strength_preset == StrengthPreset.CUSTOM:
            return float(self.custom_delta)
        return float(STRENGTH_DELTAS.get(self.strength_preset, 45.0))

    def get_crf(self) -> int:
        """Return effective CRF based on output quality setting."""
        if self.output_quality == "custom":
            return int(self.custom_crf)
        return int(OUTPUT_QUALITY.get(self.output_quality, 18))

    def copy(self) -> "WatermarkSettings":
        """Return a deep copy of settings (safe to pass to workers)."""
        return WatermarkSettings(
            wavelet=self.wavelet,
            dwt_level=int(self.dwt_level),
            block_size=int(self.block_size),
            strength_preset=self.strength_preset,
            custom_delta=float(self.custom_delta),
            scramble_seed=int(self.scramble_seed),
            ecc_type=self.ecc_type,
            rs_nsym=int(self.rs_nsym),
            extract_frames=int(self.extract_frames),
            output_quality=str(self.output_quality),
            custom_crf=int(self.custom_crf),
            payload_length_bits=int(self.payload_length_bits),
        )

    def get_compatibility_color(self) -> str:
        """Return 'excellent', 'doubtful' or 'poor'."""
        wc = WAVELET_COMPATIBILITY.get(self.wavelet, {})
        levels = wc.get("levels", {})
        return str(levels.get(self.dwt_level, "poor"))

    def get_compatibility_note(self) -> str:
        """Return localized compatibility note for current wavelet/level."""
        from i18n import get_language
        wc = WAVELET_COMPATIBILITY.get(self.wavelet, {})
        lang = get_language()
        return str(wc.get(f"note_{lang}", wc.get("note_en", "Unknown wavelet")))

    def apply_preset(self, preset_key: str):
        """Apply one of SETTINGS_PRESETS by key."""
        preset = SETTINGS_PRESETS.get(preset_key)
        if not preset:
            return

        self.wavelet = preset.get("wavelet", self.wavelet)
        self.dwt_level = int(preset.get("dwt_level", self.dwt_level))
        self.block_size = int(preset.get("block_size", self.block_size))

        sp = preset.get("strength_preset", "balanced")
        try:
            self.strength_preset = StrengthPreset(sp)
        except ValueError:
            self.strength_preset = StrengthPreset.BALANCED

        self.custom_delta = float(preset.get("custom_delta", self.custom_delta))
        self.output_quality = preset.get("output_quality", self.output_quality)
        self.custom_crf = int(preset.get("custom_crf", self.custom_crf))
        self.scramble_seed = int(preset.get("scramble_seed", self.scramble_seed))
        self.rs_nsym = int(preset.get("rs_nsym", self.rs_nsym))
        self.extract_frames = int(preset.get("extract_frames", self.extract_frames))