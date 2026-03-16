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
utils/video_utils.py

Video I/O utilities for VidMark.

Main responsibilities:
- Read video metadata (OpenCV + optional ffprobe)
- Frame reading helpers (streaming generator and random access)
- Color conversion helpers (BGR <-> YCrCb)
- Lossless temp video writing (FFV1 AVI)
- Final encoding via FFmpeg with correct command structure
- Detect and normalize problematic input timestamps (stream-copy remux)

Important design notes:
- read_frames() is a generator that ALWAYS releases VideoCapture (try/finally).
- encode_video_ffmpeg() ensures all inputs (-i ...) appear BEFORE codec/output options.
- Some clips have mismatched audio/video start timestamps (PTS offsets).
  We normalize the input by remuxing with:
    -fflags +genpts -avoid_negative_ts make_zero -c copy
"""
from __future__ import annotations

import os
import json
import subprocess
import logging
from typing import Generator, Tuple, Optional, List, Dict, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# -----------------------------
# ffprobe helpers
# -----------------------------
def _to_float(x: Any, default: float = 0.0) -> float:
    """Safe float conversion for ffprobe values (may be 'N/A')."""
    try:
        if x is None:
            return default
        if isinstance(x, str) and x.upper() == "N/A":
            return default
        return float(x)
    except Exception:
        return default


def get_stream_start_times(video_path: str) -> dict:
    """
    Return start_time for the first video and audio streams using ffprobe JSON.
    """
    info = {"video_start_time": 0.0, "audio_start_time": 0.0}
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", video_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0 or not r.stdout.strip():
            return info
        data = json.loads(r.stdout)
        streams = data.get("streams", [])
        v = next((s for s in streams if s.get("codec_type") == "video"), None)
        a = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if v:
            info["video_start_time"] = _to_float(v.get("start_time"), 0.0)
        if a:
            info["audio_start_time"] = _to_float(a.get("start_time"), 0.0)
        return info
    except Exception:
        return info


def detect_pts_offset_issue(video_path: str,
                            threshold_sec: float = 0.5) -> Dict[str, Any]:
    """
    Detect whether the input video has a significant mismatch between
    video and audio start times (PTS offsets).
    """
    st = get_stream_start_times(video_path)
    v_start = float(st.get("video_start_time", 0.0))
    a_start = float(st.get("audio_start_time", 0.0))
    delta = v_start - a_start

    has_issue = (abs(delta) >= float(threshold_sec)) or (v_start >= float(threshold_sec))
    reason = ""
    if has_issue:
        reason = (f"PTS offset detected: video_start={v_start:.3f}s, "
                  f"audio_start={a_start:.3f}s, delta={delta:.3f}s")
    return {
        "has_issue": has_issue,
        "video_start": v_start,
        "audio_start": a_start,
        "delta": delta,
        "reason": reason,
    }


def normalize_input_video_for_sync(input_path: str,
                                   output_path: str,
                                   timeout_sec: int = 600) -> Tuple[bool, str]:
    """
    Normalize A/V timestamps by remuxing with stream copy.
    Fast, lossless, fixes weird start times and negative timestamps.
    """
    cmd = [
        "ffmpeg", "-y",
        "-fflags", "+genpts",
        "-i", input_path,
        "-map", "0",
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if r.returncode != 0:
            return False, (r.stderr or "")[:1200]
        return True, ""
    except Exception as e:
        return False, str(e)


# -----------------------------
# OpenCV-based video info
# -----------------------------
def get_video_info(video_path: str) -> dict:
    """
    Return a dict with basic video info.
    Uses OpenCV for width/height/fps/frame_count.
    Uses ffprobe (if available) to detect audio and container format.
    """
    info: dict = {}

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    try:
        info["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        info["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        info["fps"] = float(cap.get(cv2.CAP_PROP_FPS))
        if info["fps"] <= 0:
            info["fps"] = 30.0
        info["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        info["duration"] = info["frame_count"] / info["fps"] if info["fps"] > 0 else 0.0
        info["codec"] = int(cap.get(cv2.CAP_PROP_FOURCC))
    finally:
        cap.release()

    info["has_audio"] = False
    info["format"] = "unknown"
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            probe_data = json.loads(result.stdout)
            streams = probe_data.get("streams", [])
            info["has_audio"] = any(s.get("codec_type") == "audio" for s in streams)
            info["format"] = probe_data.get("format", {}).get("format_name", "unknown")
    except Exception:
        pass

    return info


# -----------------------------
# Frame reading
# -----------------------------
def read_frames(video_path: str,
                max_frames: Optional[int] = None) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    Stream frames from a video as a generator yielding (frame_index, frame_bgr).
    Ensures resources are released even if iteration stops early.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    try:
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if max_frames is not None and idx >= max_frames:
                break
            yield idx, frame
            idx += 1
    finally:
        cap.release()


def read_specific_frames(video_path: str,
                         frame_indices: List[int]) -> List[Tuple[int, np.ndarray]]:
    """Read specific frames by indices using CAP_PROP_POS_FRAMES."""
    frames: List[Tuple[int, np.ndarray]] = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    try:
        for idx in sorted(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret:
                frames.append((int(idx), frame))
    finally:
        cap.release()

    return frames


# -----------------------------
# Color conversion
# -----------------------------
def bgr_to_ycrcb(frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert BGR uint8 frame to (Y, Cr, Cb) float64 channels."""
    ycrcb = cv2.cvtColor(frame.astype(np.uint8), cv2.COLOR_BGR2YCrCb)
    y = ycrcb[:, :, 0].astype(np.float64)
    cr = ycrcb[:, :, 1].astype(np.float64)
    cb = ycrcb[:, :, 2].astype(np.float64)
    return y, cr, cb


def ycrcb_to_bgr(y: np.ndarray, cr: np.ndarray, cb: np.ndarray) -> np.ndarray:
    """Convert (Y, Cr, Cb) float channels back to BGR uint8."""
    ycrcb = np.stack([
        np.clip(np.round(y), 0, 255).astype(np.uint8),
        np.clip(np.round(cr), 0, 255).astype(np.uint8),
        np.clip(np.round(cb), 0, 255).astype(np.uint8),
    ], axis=2)
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


# -----------------------------
# Writing temp video
# -----------------------------
def save_frames_as_lossless_video(frames: List[np.ndarray],
                                 output_path: str,
                                 fps: float) -> str:
    """Save frames as a lossless FFV1 AVI."""
    if not frames:
        raise ValueError("No frames to save")

    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    writer = cv2.VideoWriter(output_path, fourcc, float(fps), (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open VideoWriter: {output_path}")

    try:
        for frame in frames:
            writer.write(frame.astype(np.uint8))
    finally:
        writer.release()

    return output_path


# -----------------------------
# Final encoding
# -----------------------------
def _get_ffmpeg_major_version() -> Optional[int]:
    """Detect FFmpeg major version number. Returns None on failure."""
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            # Parse "ffmpeg version N.x.x" or "ffmpeg version n7.1-..."
            import re
            match = re.search(r"ffmpeg version (?:n)?(\d+)", r.stdout)
            if match:
                return int(match.group(1))
    except Exception:
        pass
    return None


def encode_video_ffmpeg(input_path: str,
                        output_path: str,
                        crf: int = 18,
                        codec: str = "libx264",
                        audio_source: Optional[str] = None,
                        timeout_sec: int = 3600) -> Tuple[bool, str]:
    """
    Encode a video using ffmpeg. Optionally attach audio from audio_source.

    Returns:
        (ok, stderr_excerpt_or_empty)
    """
    cmd = ["ffmpeg", "-y", "-i", input_path]

    use_audio = bool(audio_source and os.path.exists(audio_source))
    if use_audio:
        cmd += ["-i", audio_source]

    # FIX: Use -fps_mode for FFmpeg 5.1+, fall back to -vsync for older versions
    ffmpeg_ver = _get_ffmpeg_major_version()
    if ffmpeg_ver is not None and ffmpeg_ver >= 5:
        cmd += ["-fflags", "+genpts", "-fps_mode", "cfr"]
    else:
        cmd += ["-fflags", "+genpts", "-vsync", "cfr"]

    # Video encoding
    cmd += ["-c:v", codec]
    if codec in ("libvpx-vp9", "libvpx"):
        cmd += ["-crf", str(int(crf)), "-b:v", "0"]
    else:
        preset = "ultrafast" if int(crf) == 0 else "medium"
        cmd += ["-crf", str(int(crf)), "-preset", preset]
    cmd += ["-pix_fmt", "yuv420p"]

    # Mapping
    if use_audio:
        cmd += [
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:a", "copy",
            "-shortest",
        ]
    else:
        cmd += ["-an"]

    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".mp4", ".mov", ".m4v"):
        cmd += ["-movflags", "+faststart"]

    cmd += [output_path]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if r.returncode != 0:
            err = (r.stderr or "")[:1500]
            logger.error("FFmpeg failed (rc=%s). cmd=%s", r.returncode, " ".join(cmd))
            logger.error("FFmpeg stderr (first 1500 chars): %s", err)
            return False, err
        return True, ""
    except subprocess.TimeoutExpired:
        msg = f"FFmpeg timeout after {timeout_sec} seconds."
        logger.error("%s cmd=%s", msg, " ".join(cmd))
        return False, msg
    except Exception as e:
        msg = f"FFmpeg encoding error: {e}"
        logger.error(msg)
        return False, msg


def get_first_frame(video_path: str) -> Optional[np.ndarray]:
    """Read first frame of a video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    try:
        ret, frame = cap.read()
        return frame if ret else None
    finally:
        cap.release()


def select_extraction_frames(total_frames: int, num_frames: int) -> List[int]:
    """Select indices uniformly across [0..total_frames-1]."""
    if total_frames <= 0:
        return []
    if total_frames <= num_frames:
        return list(range(total_frames))
    step = total_frames / num_frames
    return [int(i * step) for i in range(num_frames)]