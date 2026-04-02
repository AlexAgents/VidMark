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
utils/image_utils.py

Small helpers for converting numpy/OpenCV images to Qt images/pixmaps.

Notes:
- OpenCV uses BGR order, Qt expects RGB for color images.
- We always create contiguous uint8 arrays to avoid Qt referencing freed memory.
"""

from __future__ import annotations

import cv2
import numpy as np


def frame_to_pixmap(frame: np.ndarray, max_width: int = 500, max_height: int = 400):
    """
    Convert an OpenCV frame (numpy array) into a QPixmap for GUI preview.

    Args:
        frame: np.ndarray, either grayscale (H,W) or BGR (H,W,3)
        max_width/max_height: output pixmap will be scaled to fit within these bounds

    Returns:
        QPixmap (scaled).
    """
    from PyQt5.QtGui import QImage, QPixmap
    from PyQt5.QtCore import Qt

    frame_u8 = np.ascontiguousarray(frame.astype(np.uint8))

    if frame_u8.ndim == 2:
        # Grayscale
        h, w = frame_u8.shape
        bytes_per_line = w
        qimg = QImage(frame_u8.data, w, h, bytes_per_line, QImage.Format_Grayscale8).copy()
    else:
        # Color: BGR -> RGB
        rgb = cv2.cvtColor(frame_u8, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

    pixmap = QPixmap.fromImage(qimg)
    return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def numpy_to_qimage(arr: np.ndarray):
    """
    Convert numpy array to QImage (no scaling).

    Args:
        arr: grayscale (H,W) or BGR (H,W,3)

    Returns:
        QImage (deep-copied).
    """
    from PyQt5.QtGui import QImage

    arr_u8 = np.ascontiguousarray(arr.astype(np.uint8))

    if arr_u8.ndim == 2:
        h, w = arr_u8.shape
        return QImage(arr_u8.data, w, h, w, QImage.Format_Grayscale8).copy()

    rgb = cv2.cvtColor(arr_u8, cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()