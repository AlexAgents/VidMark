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
Attack simulator for watermark robustness testing.

This module applies a variety of distortions to a single frame:
- Compression (JPEG, H.264, H.265)
- Noise (Gaussian, Salt & Pepper)
- Filtering (median, blur)
- Geometric transforms (rotation, scaling, cropping)
- Color transforms (brightness, contrast, histogram equalization)

Implementation note:
- H.264/H.265 are simulated by encoding a single-frame video with ffmpeg and decoding it back.
"""

from __future__ import annotations

import logging
from typing import Dict, Callable, List

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class AttackSimulator:
    """Simulates various attacks on watermarked frames."""

    @staticmethod
    def get_all_attacks() -> List[str]:
        return [
            "No Attack",
            "JPEG Q=90", "JPEG Q=70", "JPEG Q=50",
            "H.264 CRF=18", "H.264 CRF=23", "H.264 CRF=28",
            "H.265 CRF=23", "H.265 CRF=28",
            "Gaussian Noise σ=5", "Gaussian Noise σ=10", "Gaussian Noise σ=20",
            "Salt & Pepper 1%", "Salt & Pepper 5%",
            "Median Filter 3x3", "Median Filter 5x5",
            "Gaussian Blur 3x3", "Gaussian Blur 5x5",
            "Rotation 2°", "Rotation 5°", "Rotation 10°",
            "Scale 50%", "Scale 75%", "Scale 150%",
            "Crop 10%", "Crop 20%",
            "Brightness +20", "Brightness -20",
            "Contrast 0.8", "Contrast 1.2",
            "Histogram Equalization",
        ]

    @staticmethod
    def apply_attack(frame: np.ndarray, attack_name: str) -> np.ndarray:
        attacks: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
            "No Attack": lambda f: f.copy(),
            "JPEG Q=90": lambda f: AttackSimulator._jpeg(f, 90),
            "JPEG Q=70": lambda f: AttackSimulator._jpeg(f, 70),
            "JPEG Q=50": lambda f: AttackSimulator._jpeg(f, 50),
            "H.264 CRF=18": lambda f: AttackSimulator._h264(f, 18),
            "H.264 CRF=23": lambda f: AttackSimulator._h264(f, 23),
            "H.264 CRF=28": lambda f: AttackSimulator._h264(f, 28),
            "H.265 CRF=23": lambda f: AttackSimulator._h265(f, 23),
            "H.265 CRF=28": lambda f: AttackSimulator._h265(f, 28),
            "Gaussian Noise σ=5": lambda f: AttackSimulator._gaussian_noise(f, 5),
            "Gaussian Noise σ=10": lambda f: AttackSimulator._gaussian_noise(f, 10),
            "Gaussian Noise σ=20": lambda f: AttackSimulator._gaussian_noise(f, 20),
            "Salt & Pepper 1%": lambda f: AttackSimulator._salt_pepper(f, 0.01),
            "Salt & Pepper 5%": lambda f: AttackSimulator._salt_pepper(f, 0.05),
            "Median Filter 3x3": lambda f: cv2.medianBlur(f, 3),
            "Median Filter 5x5": lambda f: cv2.medianBlur(f, 5),
            "Gaussian Blur 3x3": lambda f: cv2.GaussianBlur(f, (3, 3), 0),
            "Gaussian Blur 5x5": lambda f: cv2.GaussianBlur(f, (5, 5), 0),
            "Rotation 2°": lambda f: AttackSimulator._rotate(f, 2),
            "Rotation 5°": lambda f: AttackSimulator._rotate(f, 5),
            "Rotation 10°": lambda f: AttackSimulator._rotate(f, 10),
            "Scale 50%": lambda f: AttackSimulator._scale(f, 0.5),
            "Scale 75%": lambda f: AttackSimulator._scale(f, 0.75),
            "Scale 150%": lambda f: AttackSimulator._scale(f, 1.5),
            "Crop 10%": lambda f: AttackSimulator._crop(f, 0.1),
            "Crop 20%": lambda f: AttackSimulator._crop(f, 0.2),
            "Brightness +20": lambda f: AttackSimulator._brightness(f, 20),
            "Brightness -20": lambda f: AttackSimulator._brightness(f, -20),
            "Contrast 0.8": lambda f: AttackSimulator._contrast(f, 0.8),
            "Contrast 1.2": lambda f: AttackSimulator._contrast(f, 1.2),
            "Histogram Equalization": lambda f: AttackSimulator._histeq(f),
        }

        fn = attacks.get(attack_name)
        if fn is None:
            logger.warning("Unknown attack: %s", attack_name)
            return frame.copy()

        try:
            out = fn(frame)
            if out.shape[:2] != frame.shape[:2]:
                out = cv2.resize(out, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LANCZOS4)
            return out
        except Exception as e:
            logger.error("Attack '%s' failed: %s", attack_name, e)
            return frame.copy()

    @staticmethod
    def _jpeg(frame: np.ndarray, quality: int) -> np.ndarray:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
        ok, buf = cv2.imencode(".jpg", frame, encode_param)
        if not ok:
            return frame.copy()
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)

    @staticmethod
    def _h264(frame: np.ndarray, crf: int) -> np.ndarray:
        return AttackSimulator._video_codec_attack(frame, "libx264", crf)

    @staticmethod
    def _h265(frame: np.ndarray, crf: int) -> np.ndarray:
        return AttackSimulator._video_codec_attack(frame, "libx265", crf)

    @staticmethod
    def _video_codec_attack(frame: np.ndarray, codec: str, crf: int) -> np.ndarray:
        """
        Encode one-frame video with ffmpeg and decode it back, simulating compression.
        """
        import tempfile
        import subprocess
        import os

        h, w = frame.shape[:2]
        # Many codecs require even dimensions (yuv420p)
        h_even = h if h % 2 == 0 else h - 1
        w_even = w if w % 2 == 0 else w - 1
        frame_even = frame[:h_even, :w_even]

        with tempfile.TemporaryDirectory() as tmpdir:
            in_path = os.path.join(tmpdir, "in.avi")
            out_path = os.path.join(tmpdir, "out.mp4")

            writer = cv2.VideoWriter(in_path, cv2.VideoWriter_fourcc(*"FFV1"), 30, (w_even, h_even))
            if not writer.isOpened():
                return frame.copy()
            writer.write(frame_even)
            writer.release()

            extra = []
            if codec == "libx265":
                extra = ["-x265-params", "log-level=error"]

            cmd = [
                "ffmpeg", "-y", "-i", in_path,
                "-c:v", codec, "-crf", str(int(crf)),
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                *extra,
                "-frames:v", "1",
                out_path
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                logger.error("FFmpeg attack failed (%s CRF=%s): %s", codec, crf, r.stderr[:500])
                return frame.copy()

            cap = cv2.VideoCapture(out_path)
            try:
                ret, decoded = cap.read()
            finally:
                cap.release()

            if not ret or decoded is None:
                logger.error("FFmpeg attack output not readable: %s", out_path)
                return frame.copy()

            if decoded.shape[:2] != frame.shape[:2]:
                decoded = cv2.resize(decoded, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LANCZOS4)

            return decoded

    @staticmethod
    def _gaussian_noise(frame: np.ndarray, sigma: float) -> np.ndarray:
        noise = np.random.normal(0.0, float(sigma), frame.shape)
        out = frame.astype(np.float64) + noise
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def _salt_pepper(frame: np.ndarray, ratio: float) -> np.ndarray:
        out = frame.copy()
        total = frame.shape[0] * frame.shape[1]
        n = int(total * float(ratio) / 2.0)

        # Salt
        coords = [np.random.randint(0, i, n) for i in frame.shape[:2]]
        out[coords[0], coords[1]] = 255

        # Pepper
        coords = [np.random.randint(0, i, n) for i in frame.shape[:2]]
        out[coords[0], coords[1]] = 0

        return out

    @staticmethod
    def _rotate(frame: np.ndarray, angle: float) -> np.ndarray:
        h, w = frame.shape[:2]
        center = (w / 2.0, h / 2.0)

        M_fwd = cv2.getRotationMatrix2D(center, float(angle), 1.0)
        rotated = cv2.warpAffine(frame, M_fwd, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        M_back = cv2.getRotationMatrix2D(center, -float(angle), 1.0)
        out = cv2.warpAffine(rotated, M_back, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        return out

    @staticmethod
    def _scale(frame: np.ndarray, factor: float) -> np.ndarray:
        h, w = frame.shape[:2]
        factor = float(factor)

        new_w = max(1, int(w * factor))
        new_h = max(1, int(h * factor))

        interp = cv2.INTER_AREA if factor < 1.0 else cv2.INTER_LINEAR
        scaled = cv2.resize(frame, (new_w, new_h), interpolation=interp)
        out = cv2.resize(scaled, (w, h), interpolation=cv2.INTER_LINEAR)
        return out

    @staticmethod
    def _crop(frame: np.ndarray, ratio: float) -> np.ndarray:
        h, w = frame.shape[:2]
        ratio = float(ratio)
        ch = int(h * ratio / 2.0)
        cw = int(w * ratio / 2.0)
        cropped = frame[ch: h - ch, cw: w - cw].copy()
        return cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def _brightness(frame: np.ndarray, value: int) -> np.ndarray:
        out = frame.astype(np.int16) + int(value)
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def _contrast(frame: np.ndarray, factor: float) -> np.ndarray:
        factor = float(factor)
        mean = float(np.mean(frame))
        out = (frame.astype(np.float64) - mean) * factor + mean
        return np.clip(out, 0, 255).astype(np.uint8)

    @staticmethod
    def _histeq(frame: np.ndarray) -> np.ndarray:
        if len(frame.shape) == 3:
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        return cv2.equalizeHist(frame)