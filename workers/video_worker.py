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

# workers/video_worker.py
"""
workers/video_worker.py

Background workers (PyQt5 QThread) for:
- Embedding watermark into a full video
- Extracting and verifying watermark from a watermarked video
- Running attack robustness tests on a single frame

This version includes robustness improvements:
- Handles videos where OpenCV reports frame_count <= 0 (unknown frame count).
- Verifies watermark from multiple frames (not only the first frame).
- Ensures VideoCapture/VideoWriter are always released (try/finally).
- Cleans up temporary files on cancel/error.
"""
from __future__ import annotations

import os
import time
import uuid
import math
import re
import traceback
import logging
from typing import Optional, Tuple, List

import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal

from config import WatermarkSettings, TEMP_DIR
from i18n import tr
from core.payload import form_payload, parse_payload
from core.ecc import ECCCodec
from core.scrambler import Scrambler
from core.embedder import WatermarkEmbedder
from core.extractor import WatermarkExtractor
from core.metrics import compute_psnr, compute_ssim, compute_nc, compute_ber
from core.attacks import AttackSimulator
from utils.video_utils import (
    detect_pts_offset_issue,
    normalize_input_video_for_sync,
    get_video_info,
    bgr_to_ycrcb,
    ycrcb_to_bgr,
    encode_video_ffmpeg,
    read_specific_frames,
    select_extraction_frames,
    get_first_frame,
    read_frames,
)

logger = logging.getLogger(__name__)

METRIC_FRAMES = 10


def _bits_to_visual(bits: np.ndarray, target_size: int = 256) -> np.ndarray:
    """Convert hard bits into a square visualization image."""
    n = int(len(bits))
    if n <= 0:
        return np.zeros((target_size, target_size), dtype=np.uint8)
    side = int(math.ceil(math.sqrt(n)))
    padded = np.zeros(side * side, dtype=np.uint8)
    padded[:n] = bits[:n].astype(np.uint8)
    grid = padded.reshape(side, side) * 255
    return cv2.resize(grid, (target_size, target_size), interpolation=cv2.INTER_NEAREST)


def _soft_to_visual(values: np.ndarray, target_size: int = 256) -> np.ndarray:
    """Convert soft values to grayscale visualization."""
    n = int(len(values))
    if n <= 0:
        return np.full((target_size, target_size), 127, dtype=np.uint8)
    side = int(math.ceil(math.sqrt(n)))
    padded = np.zeros(side * side, dtype=np.float64)
    padded[:n] = values[:n].astype(np.float64)
    vmax = float(np.max(np.abs(padded)))
    if vmax < 1e-9:
        norm = np.full_like(padded, 127.0)
    else:
        norm = 127.5 + 127.5 * (padded / vmax)
    grid = np.clip(norm.reshape(side, side), 0, 255).astype(np.uint8)
    return cv2.resize(grid, (target_size, target_size), interpolation=cv2.INTER_NEAREST)


def _safe_remove(path: str):
    """Best-effort file removal."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


class EmbedWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, dict)
    log = pyqtSignal(str)

    def __init__(self, input_video: str, output_video: str,
                 settings: WatermarkSettings, author_id: str = "", parent=None):
        super().__init__(parent)
        # save it as an instance attribute, not a local var
        self.input_video = input_video
        self.output_video = output_video
        self.settings = settings.copy()
        self.author_id = author_id
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self._embed()
        except Exception as e:
            self.finished.emit(False, f"{tr('error')}: {str(e)}", {})
            self.log.emit(f"ERROR:\n{traceback.format_exc()}")

    def _embed(self):
        t0 = time.time()
        self.log.emit("=" * 50)
        self.log.emit(tr("log_embedding_start"))
        self.log.emit("=" * 50)
        self.progress.emit(0, tr("status_reading_video"))

        # take path from self.input_video
        input_for_processing = self.input_video

        # 1) Video info
        vi = get_video_info(input_for_processing)
        vi["input_path"] = input_for_processing
        vi["output_path"] = self.output_video

        # --- Detect and auto-fix problematic PTS offsets ---
        normalized_tmp = None
        issue = detect_pts_offset_issue(input_for_processing, threshold_sec=0.5)

        if issue.get("has_issue", False) and vi.get("has_audio", False):
            self.log.emit(
                f"[ERROR] Input clip has unusual timestamps: {issue.get('reason', 'PTS issue')}. "
                f"This may cause audio desync and can DAMAGE watermark extraction."
            )
            self.log.emit(
                "[TIP] Recommended safe cutting command:\n"
                "  ffmpeg -ss HH:MM:SS -t DURATION -i input.mp4 "
                "-fflags +genpts -avoid_negative_ts make_zero -c copy output.mp4"
            )
            unique = f"norm_{os.getpid()}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            normalized_tmp = os.path.join(TEMP_DIR, f"{unique}.mp4")
            self.log.emit("[TIP] Attempting automatic normalization (stream copy) to fix timestamps...")
            ok_norm, norm_err = normalize_input_video_for_sync(input_for_processing, normalized_tmp)
            if ok_norm:
                input_for_processing = normalized_tmp
                self.log.emit("[TIP] Normalization succeeded. Using normalized clip for embedding.")
                vi = get_video_info(input_for_processing)
            else:
                self.log.emit(f"[ERROR] Normalization failed. Proceeding with original input. Details: {norm_err}")

        total_frames = int(vi.get("frame_count", 0))
        fps = float(vi.get("fps", 30.0))
        w = int(vi.get("width", 0))
        h = int(vi.get("height", 0))
        self.log.emit(
            f"{tr('log_video_info')}: {w}x{h}, {fps:.1f}fps, "
            f"{total_frames} {tr('log_frames')}, {tr('log_audio')}: {vi.get('has_audio', False)}"
        )
        self.log.emit(f"{tr('author')}: '{self.author_id}'")

        # 2) Payload
        payload_bits, payload_info = form_payload(
            author_id=(self.author_id if self.author_id else None))
        self.log.emit(f"UUID: {payload_info.get('uuid_hex', '')}")
        self.log.emit(f"{tr('log_timestamp')}: {payload_info.get('timestamp_str', '')}")
        self.log.emit(f"{tr('log_payload')}: {payload_info.get('total_bits', 0)} {tr('log_bits')}")

        # 3) Unique seed
        unique_seed = (
            int(self.settings.scramble_seed)
            ^ int(payload_info.get("uuid", 0))
            ^ int(payload_info.get("timestamp", 0))
        ) & 0xFFFFFFFF
        self.settings.scramble_seed = unique_seed
        self.log.emit(f"{tr('log_delta')}: {self.settings.get_delta():.1f}")
        self.log.emit(f"CRF: {self.settings.get_crf()} ({self.settings.output_quality})")

        # 4) ECC
        ecc = ECCCodec(self.settings.rs_nsym)
        ecc_bits = ecc.encode(payload_bits)
        self.log.emit(f"{tr('log_after_ecc')}: {len(ecc_bits)} {tr('log_bits')}")

        # 5) Scramble
        scrambler = Scrambler(self.settings.scramble_seed)
        wm_bits = scrambler.scramble(ecc_bits)
        self.log.emit(f"{tr('log_wm_bits')}: {len(wm_bits)}")

        # 6) Embedder
        embedder = WatermarkEmbedder(self.settings)
        self.log.emit(
            f"{tr('log_embedder')}: DWT-DCT {embedder.wavelet} "
            f"L{embedder.dwt_level} B{embedder.block_size} D={embedder.delta}"
        )
        compat = self.settings.get_compatibility_color()
        note = self.settings.get_compatibility_note()
        if compat == "poor":
            self.log.emit(f" {tr('log_warning')}: {note}")
        elif compat == "doubtful":
            self.log.emit(f" {tr('log_note')}: {note}")

        # 7) Quick in-memory lossless test
        self.log.emit(tr("log_lossless_test"))
        cap_t = cv2.VideoCapture(input_for_processing)
        try:
            ret_t, frame_t = cap_t.read()
        finally:
            cap_t.release()

        if ret_t:
            y_t, _, _ = bgr_to_ycrcb(frame_t)
            y_wm_t, _ = embedder.embed_frame(y_t, wm_bits)
            y_wm_t_sim = np.clip(np.round(y_wm_t), 0, 255).astype(np.uint8).astype(np.float64)
            ext_t = WatermarkExtractor(self.settings)
            hard_t, _, _ = ext_t.extract_frame(y_wm_t_sim, len(wm_bits))
            nc_t = compute_nc(wm_bits, hard_t)
            self.log.emit(f"  {tr('log_lossless_nc')}: {nc_t:.4f}")
            if nc_t < 0.95:
                self.log.emit(f"  {tr('log_low_nc')}")

        # 8) Frame processing to temp lossless AVI
        self.log.emit(tr("log_processing_frames"))
        cap = cv2.VideoCapture(input_for_processing)
        if not cap.isOpened():
            # cleanup normalized_tmp on early exit
            if normalized_tmp:
                _safe_remove(normalized_tmp)
            self.finished.emit(False, tr("log_cannot_open_video"), {})
            return

        unique_suffix = f"{os.getpid()}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        temp_path = os.path.join(TEMP_DIR, f"temp_wm_{unique_suffix}.avi")
        writer = cv2.VideoWriter(temp_path, cv2.VideoWriter_fourcc(*"FFV1"), fps, (w, h))
        if not writer.isOpened():
            cap.release()
            if normalized_tmp:
                _safe_remove(normalized_tmp)
            raise RuntimeError(f"Cannot open VideoWriter: {temp_path}")

        psnrs: List[float] = []
        ssims: List[float] = []
        first_wm_frame: Optional[np.ndarray] = None
        cancelled = False
        idx = 0

        try:
            while True:
                if self._cancelled:
                    cancelled = True
                    break
                ret, frame = cap.read()
                if not ret:
                    break

                y, cr, cb = bgr_to_ycrcb(frame)
                y_wm, _ = embedder.embed_frame(y, wm_bits)

                if idx < METRIC_FRAMES:
                    psnrs.append(compute_psnr(y, y_wm))
                    ssims.append(compute_ssim(
                        y.astype(np.uint8),
                        np.clip(np.round(y_wm), 0, 255).astype(np.uint8),
                    ))
                    if idx == 0 and psnrs and ssims:
                        self.log.emit(
                            f"  {tr('log_frame')} 0: PSNR={psnrs[0]:.2f}, SSIM={ssims[0]:.4f}")

                frame_wm = ycrcb_to_bgr(y_wm, cr, cb)
                if first_wm_frame is None:
                    first_wm_frame = frame_wm.copy()
                writer.write(frame_wm)

                # Progress
                if total_frames > 0:
                    if idx % max(1, total_frames // 20) == 0:
                        self.progress.emit(
                            int(5 + 80 * (idx + 1) / total_frames),
                            tr("status_processing_frame", current=idx + 1, total=total_frames)
                        )
                else:
                    if idx % 30 == 0:
                        self.progress.emit(
                            5 + min(80, idx // 3),
                            tr("status_processing_frame", current=idx + 1, total=0)
                        )
                idx += 1
        finally:
            try:
                writer.release()
            finally:
                cap.release()

        if cancelled:
            _safe_remove(temp_path)
            # cleanup normalized_tmp on cancel
            if normalized_tmp:
                _safe_remove(normalized_tmp)
            self.finished.emit(False, tr("status_cancelled"), {})
            return

        # 9) Encode output with ffmpeg
        self.log.emit(tr("status_encoding"))
        self.progress.emit(88, tr("status_encoding"))
        audio_source = input_for_processing if vi.get("has_audio") else None
        ext = os.path.splitext(self.output_video)[1].lower()
        codec = "libvpx-vp9" if ext == ".webm" else "libx264"

        # correctly unpack tuple (bool, str)
        ok, encode_err = encode_video_ffmpeg(
            temp_path,
            self.output_video,
            crf=int(self.settings.get_crf()),
            codec=codec,
            audio_source=audio_source,
        )

        # Fallback: copy lossless temp as output
        if not ok:
            self.log.emit(f"FFmpeg encoding failed: {encode_err[:200]}")
            import shutil
            try:
                shutil.copy2(temp_path, self.output_video)
                ok = True
                self.log.emit("FFmpeg failed, saved uncompressed backup.")
            except Exception:
                pass

        # Cleanup temp files
        _safe_remove(temp_path)
        # cleanup normalized_tmp
        if normalized_tmp:
            _safe_remove(normalized_tmp)

        # 10) Verify watermark from multiple frames
        self.log.emit(tr("status_verifying"))
        self.progress.emit(93, tr("status_verifying"))
        vnc = self._verify_multi(self.output_video, wm_bits, frames_to_check=5)
        self.log.emit(f"  {tr('log_output_nc')}: {vnc:.4f}")

        # 11) Save keyfile
        kf_path = os.path.splitext(self.output_video)[0] + "_key.json"
        from core.keyfile import save_keyfile
        save_keyfile(kf_path, self.settings, vi, {}, payload_info, author_text=self.author_id)
        self.log.emit(f"{tr('log_key_file')}: {kf_path}")

        avg_p = float(np.mean(psnrs)) if psnrs else 0.0
        avg_s = float(np.mean(ssims)) if ssims else 0.0
        elapsed = time.time() - t0

        result = {
            "avg_psnr": avg_p,
            "avg_ssim": avg_s,
            "keyfile_path": kf_path,
            "elapsed_time": elapsed,
            "total_frames": total_frames,
            "payload_info": payload_info,
            "wm_bits_length": len(wm_bits),
            "verification_nc": vnc,
            "first_wm_frame": first_wm_frame,
            "wm_bits": wm_bits,
            "embed_settings": self.settings.copy(),
            "author_text": self.author_id,
            "video_info": vi,
        }

        self.progress.emit(100, tr("status_done"))
        self.log.emit(
            f"\n {tr('status_done')} PSNR={avg_p:.2f}, SSIM={avg_s:.4f}, NC={vnc:.4f}, "
            f"{tr('time_elapsed')} {elapsed:.1f}s"
        )
        self.finished.emit(ok, tr("embed_success"), result)

    def _verify_multi(self, video_path: str, bits: np.ndarray, frames_to_check: int = 5) -> float:
        """
        Verify watermark by extracting from multiple frames and averaging NC.
        """
        try:
            vi = get_video_info(video_path)
            total = int(vi.get("frame_count", 0))
            if total > 0:
                idxs = select_extraction_frames(total, max(1, frames_to_check))
                frames = read_specific_frames(video_path, idxs)
            else:
                frames = []
                for i, (idx, frame) in enumerate(read_frames(video_path, max_frames=frames_to_check)):
                    frames.append((idx, frame))
            if not frames:
                return 0.0
            ex = WatermarkExtractor(self.settings)
            ncs = []
            for _, frame in frames:
                y, _, _ = bgr_to_ycrcb(frame)
                hard, _, _ = ex.extract_frame(y, len(bits))
                ncs.append(compute_nc(bits, hard))
            return float(np.mean(ncs)) if ncs else 0.0
        except Exception:
            return 0.0


class ExtractWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, dict)
    log = pyqtSignal(str)

    def __init__(self, video_path: str, keyfile_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.keyfile_path = keyfile_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self._extract()
        except Exception as e:
            self.finished.emit(False, f"{tr('error')}: {str(e)}", {})
            self.log.emit(f"ERROR:\n{traceback.format_exc()}")

    def _extract(self):
        from core.keyfile import load_keyfile

        t0 = time.time()
        self.log.emit("=" * 50)
        self.log.emit(tr("log_extracting_start"))
        self.log.emit("=" * 50)

        settings, kd = load_keyfile(self.keyfile_path)
        jp = kd.get("payload_info", {})
        json_uuid = jp.get("uuid_hex", "")
        json_author = jp.get("author_text", "")
        json_ts = int(jp.get("timestamp", 0))
        json_ts_str = jp.get("timestamp_str", "")

        self.log.emit(f"  {tr('log_expected_author')}: '{json_author}'")
        self.log.emit(f"  {tr('log_expected_uuid')}: {json_uuid}")
        self.log.emit(f"  {tr('log_expected_time')}: {json_ts_str}")
        self.log.emit(
            f"  {tr('log_settings')}: {settings.wavelet} "
            f"L{settings.dwt_level} B{settings.block_size} "
            f"δ={settings.get_delta()} key={settings.scramble_seed}"
        )

        vi = get_video_info(self.video_path)
        total = int(vi.get("frame_count", 0))
        n_ext = min(int(settings.extract_frames), total) if total > 0 else int(settings.extract_frames)
        if n_ext <= 0:
            self.finished.emit(False, tr("error"), {"status": "NO_FRAMES"})
            return

        ecc = ECCCodec(settings.rs_nsym)
        num_wm = ecc.get_encoded_length_bits(settings.payload_length_bits)
        self.log.emit(f"  {tr('log_expected_wm_bits')}: {num_wm}")
        extractor = WatermarkExtractor(settings)

        # Select frames
        if total > 0:
            indices = select_extraction_frames(total, n_ext)
            frames = read_specific_frames(self.video_path, indices)
        else:
            frames = []
            for i, (idx, frame) in enumerate(read_frames(self.video_path, max_frames=n_ext)):
                frames.append((idx, frame))

        self.log.emit(f"  {tr('log_frames_to_extract')}: {len(frames)}")

        all_soft = []
        for i, (idx, frame) in enumerate(frames):
            if self._cancelled:
                self.finished.emit(False, tr("status_cancelled"), {})
                return
            y, _, _ = bgr_to_ycrcb(frame)
            _, soft, _ = extractor.extract_frame(y, num_wm)
            all_soft.append(soft)
            self.progress.emit(
                int(10 + 60 * (i + 1) / max(1, len(frames))),
                tr("status_extracting_frame", current=i + 1, total=len(frames))
            )

        if not all_soft:
            self.finished.emit(False, tr("error"), {"status": "NO_FRAMES"})
            return

        self.log.emit(f"  {tr('log_majority_voting')}")
        mn = min(len(s) for s in all_soft)
        avg_soft = np.mean(np.array([s[:mn] for s in all_soft]), axis=0)
        voted = (avg_soft > 0).astype(np.int32)

        raw_conf = float(np.mean(np.abs(avg_soft)))
        avg_conf = float(np.tanh(raw_conf))

        self.log.emit(f"  {tr('log_descrambling')}")
        scrambler = Scrambler(settings.scramble_seed)
        descrambled = scrambler.descramble(voted)

        self.log.emit(f"  {tr('log_ecc_decoding')}")
        decoded, _, ecc_ok = ecc.decode(descrambled)
        if not ecc_ok:
            eob = int(settings.rs_nsym) * 8
            raw_len_bits = len(descrambled) - eob
            if raw_len_bits > 0:
                decoded = descrambled[: (raw_len_bits // 8) * 8]

        self.log.emit(f"  {tr('log_parsing_payload')}")
        payload_info, crc_ok = parse_payload(decoded)

        ext_uuid = payload_info.get("uuid_hex", "")
        ext_ts = int(payload_info.get("timestamp", 0))

        uuid_match = (ext_uuid == json_uuid) if json_uuid else True
        ts_match = (ext_ts == json_ts) if json_ts else True

        elapsed = time.time() - t0
        data_visual = _soft_to_visual(avg_soft)

        if ecc_ok and crc_ok and uuid_match and ts_match:
            status, msg = "VERIFIED", tr("status_verified")
        elif ecc_ok and crc_ok and uuid_match:
            status, msg = "TIMESTAMP_MISMATCH", tr("status_ts_mismatch")
        elif ecc_ok and crc_ok:
            status, msg = "MISMATCH", tr("status_uuid_mismatch")
        elif ecc_ok:
            status, msg = "DAMAGED", tr("status_damaged")
        else:
            status, msg = "NOT_FOUND", tr("status_not_found")

        attack_frame = None
        attack_bits = None
        attack_settings = None
        if frames and ecc_ok:
            _, first_frame = frames[0]
            attack_frame = first_frame.copy()
            attack_bits = voted.copy()
            attack_settings = settings

        result = {
            "status": status,
            "payload_info": payload_info,
            "crc_valid": crc_ok,
            "ecc_success": ecc_ok,
            "uuid_match": uuid_match,
            "ts_match": ts_match,
            "confidence": avg_conf,
            "confidence_raw": raw_conf,
            "elapsed_time": elapsed,
            "frames_used": len(frames),
            "data_visual": data_visual,
            "json_uuid": json_uuid,
            "json_author": json_author,
            "json_timestamp": json_ts,
            "json_ts_str": json_ts_str,
            "attack_frame": attack_frame,
            "attack_bits": attack_bits,
            "attack_settings": attack_settings,
        }

        self.progress.emit(100, tr("status_done"))
        self.log.emit(f"\n{tr('log_result')}: {msg}")
        self.finished.emit(True, msg, result)


class AttackTestWorker(QThread):
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(str, float, float, float, str)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)

    def __init__(self, frame: np.ndarray, bits: np.ndarray, settings: WatermarkSettings,
                 attacks: List[str], save_wm: bool = False, save_path: str = "", parent=None):
        super().__init__(parent)
        self.frame = frame.copy()
        self.bits = bits.copy()
        self.settings = settings
        self._attacks = attacks
        self.save_wm = save_wm
        self.save_path = save_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self._test()
        except Exception as e:
            self.finished.emit(False, f"{tr('error')}: {e}")
            self.log.emit(f"ERROR:\n{traceback.format_exc()}")

    @staticmethod
    def _safe_filename(name: str) -> str:
        return re.sub(r"[^\w\-.]", "_", name)

    def _test(self):
        extractor = WatermarkExtractor(self.settings)
        n_payload = int(len(self.bits))
        total = int(len(self._attacks))

        self.log.emit(f"\n{'=' * 50}")
        self.log.emit(f"{tr('log_attack_testing')} ({total} {tr('log_attacks')})")
        self.log.emit(
            f"  Δ={extractor.delta}, DWT-DCT {extractor.wavelet} "
            f"L{extractor.dwt_level} B{extractor.block_size}"
        )
        self.log.emit(f"  Payload: {n_payload} {tr('log_bits')}")
        if self.save_wm and self.save_path:
            self.log.emit(f"  {tr('log_saving_wm_to')}: {self.save_path}")
        self.log.emit(f"{'=' * 50}")

        if self.save_wm and self.save_path:
            os.makedirs(self.save_path, exist_ok=True)
            cv2.imwrite(
                os.path.join(self.save_path, "00_original_data.png"),
                _bits_to_visual(self.bits))
            self.log.emit(f"  {tr('log_saved_original_wm')}")

        for i, name in enumerate(self._attacks):
            if self._cancelled:
                self.finished.emit(False, tr("status_cancelled"))
                return

            self.progress.emit(
                int(100 * i / max(1, total)),
                tr("status_testing", name=name))

            attacked = (self.frame.copy() if name == "No Attack"
                        else AttackSimulator.apply_attack(self.frame, name))
            psnr_val = compute_psnr(self.frame, attacked)

            y, _, _ = bgr_to_ycrcb(attacked)
            extracted_bits, soft_bits, _ = extractor.extract_frame(y, n_payload)
            mn = min(n_payload, len(extracted_bits))
            nc_val = compute_nc(self.bits[:mn], extracted_bits[:mn])
            ber_val = compute_ber(self.bits[:mn], extracted_bits[:mn])
            status_str = "Good" if nc_val >= 0.85 else "Fair" if nc_val >= 0.70 else "Poor"

            self.log.emit(
                f"  {name}: NC={nc_val:.4f} BER={ber_val:.4f} "
                f"PSNR={psnr_val:.1f} {status_str}")
            self.result_ready.emit(name, nc_val, ber_val, psnr_val, status_str)

            if self.save_wm and self.save_path:
                safe = self._safe_filename(name)
                vis = _soft_to_visual(soft_bits[:mn])
                cv2.imwrite(
                    os.path.join(self.save_path, f"{i + 1:02d}_{safe}_data.png"), vis)

        if self.save_wm and self.save_path:
            self.log.emit(tr("wm_saved_to", path=self.save_path))

        self.progress.emit(100, tr("status_complete"))
        self.finished.emit(True, tr("attack_test_complete"))