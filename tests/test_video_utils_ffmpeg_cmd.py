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
Tests for utils.video_utils.encode_video_ffmpeg command structure.

We do not actually run ffmpeg. Instead we monkeypatch subprocess.run and inspect the command.
"""

import os
import types
import utils.video_utils as vu


class _FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_encode_video_ffmpeg_inputs_come_before_codec_options(monkeypatch, tmp_path):
    """
    Regression test:
    all '-i' inputs must come BEFORE '-c:v' and other output options.
    """
    # Create dummy file paths
    input_path = str(tmp_path / "in.avi")
    audio_path = str(tmp_path / "audio.mp4")
    output_path = str(tmp_path / "out.mp4")

    # Create fake files so os.path.exists(audio_source) returns True
    open(input_path, "wb").close()
    open(audio_path, "wb").close()

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(vu.subprocess, "run", fake_run)

    # FIX: monkeypatch version detection to avoid calling real ffmpeg
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: 5)

    # FIX: encode_video_ffmpeg returns (bool, str)
    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
        audio_source=audio_path,
        timeout_sec=10,
    )

    assert ok
    assert err == ""

    cmd = captured["cmd"]

    # Find positions
    i_positions = [i for i, x in enumerate(cmd) if x == "-i"]
    assert len(i_positions) == 2, f"Expected 2 inputs (-i), got cmd={cmd}"

    cv_pos = cmd.index("-c:v")
    # Ensure both inputs appear before -c:v
    assert max(i_positions) < cv_pos, f"'-c:v' appears before the last '-i': cmd={cmd}"


def test_encode_video_ffmpeg_uses_fps_mode_for_ffmpeg5(monkeypatch, tmp_path):
    """FIX: FFmpeg 5+ should use -fps_mode cfr instead of deprecated -vsync cfr."""
    input_path = str(tmp_path / "in.avi")
    output_path = str(tmp_path / "out.mp4")
    open(input_path, "wb").close()

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(vu.subprocess, "run", fake_run)
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: 7)

    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
    )

    assert ok
    cmd = captured["cmd"]
    assert "-fps_mode" in cmd, f"Expected -fps_mode in cmd: {cmd}"
    assert "-vsync" not in cmd, f"Unexpected -vsync in cmd for FFmpeg 7: {cmd}"


def test_encode_video_ffmpeg_uses_vsync_for_old_ffmpeg(monkeypatch, tmp_path):
    """Old FFmpeg (<5) should use -vsync cfr."""
    input_path = str(tmp_path / "in.avi")
    output_path = str(tmp_path / "out.mp4")
    open(input_path, "wb").close()

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(vu.subprocess, "run", fake_run)
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: 4)

    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
    )

    assert ok
    cmd = captured["cmd"]
    assert "-vsync" in cmd, f"Expected -vsync in cmd for FFmpeg 4: {cmd}"
    assert "-fps_mode" not in cmd, f"Unexpected -fps_mode in cmd for FFmpeg 4: {cmd}"


def test_encode_video_ffmpeg_uses_vsync_when_version_unknown(monkeypatch, tmp_path):
    """If FFmpeg version cannot be detected, fall back to -vsync cfr."""
    input_path = str(tmp_path / "in.avi")
    output_path = str(tmp_path / "out.mp4")
    open(input_path, "wb").close()

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(vu.subprocess, "run", fake_run)
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: None)

    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
    )

    assert ok
    cmd = captured["cmd"]
    assert "-vsync" in cmd, f"Expected -vsync fallback: {cmd}"


def test_encode_video_ffmpeg_returns_error_on_failure(monkeypatch, tmp_path):
    """FIX: On failure, function returns (False, error_message)."""
    input_path = str(tmp_path / "in.avi")
    output_path = str(tmp_path / "out.mp4")
    open(input_path, "wb").close()

    def fake_run(cmd, capture_output, text, timeout):
        return _FakeCompleted(returncode=1, stderr="Some ffmpeg error")

    monkeypatch.setattr(vu.subprocess, "run", fake_run)
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: 5)

    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
    )

    assert not ok
    assert "Some ffmpeg error" in err


def test_encode_video_ffmpeg_no_audio_uses_an_flag(monkeypatch, tmp_path):
    """Without audio source, command should contain -an."""
    input_path = str(tmp_path / "in.avi")
    output_path = str(tmp_path / "out.mp4")
    open(input_path, "wb").close()

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return _FakeCompleted(returncode=0)

    monkeypatch.setattr(vu.subprocess, "run", fake_run)
    monkeypatch.setattr(vu, "_get_ffmpeg_major_version", lambda: 5)

    ok, err = vu.encode_video_ffmpeg(
        input_path=input_path,
        output_path=output_path,
        crf=18,
        codec="libx264",
        audio_source=None,
    )

    assert ok
    cmd = captured["cmd"]
    assert "-an" in cmd, f"Expected -an when no audio: {cmd}"

    i_positions = [i for i, x in enumerate(cmd) if x == "-i"]
    assert len(i_positions) == 1, f"Expected 1 input without audio: {cmd}"