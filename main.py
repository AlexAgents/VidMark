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
VidMark - Main Entry Point

Packaging notes (PyInstaller-friendly):
- Do not write generated assets into the application directory (it may be read-only in .exe).
- Store generated runtime assets (like check.svg) in a writable user settings directory.
"""
from __future__ import annotations

import sys
import os
import shutil
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def _check_ffmpeg() -> bool:
    """Check if ffmpeg and ffprobe are available in PATH."""
    return (shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None)


def _runtime_base_dir() -> str:
    """
    Return base directory for resources at runtime.

    In PyInstaller: sys._MEIPASS points to the temporary extraction folder.
    In normal run: use directory of this file.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def _load_stylesheet(base_dir: str) -> str:
    """
    Load QSS stylesheet from assets/style.qss.
    Returns empty string if file not found (app will use default Qt styling).
    """
    qss_path = os.path.join(base_dir, "assets", "style.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning("Failed to load stylesheet: %s", e)
    else:
        logger.warning("Stylesheet not found: %s", qss_path)
    return ""


def _ensure_check_svg() -> str:
    """
    Ensure check.svg exists exactly once in a writable location.

    When packaged as .exe, the app directory may not be writable.
    We generate this SVG dynamically only if it does not exist yet.

    Returns:
        Absolute path to check.svg (writable, persistent).
    """
    from config import SETTINGS_DIR

    check_svg_path = os.path.join(SETTINGS_DIR, "check.svg")

    if os.path.exists(check_svg_path):
        return check_svg_path

    check_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">\n'
        '<rect width="18" height="18" rx="4" fill="#34c759"/>\n'
        '<polyline points="4,9 8,13 14,5" fill="none" stroke="white" '
        'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>\n'
        '</svg>\n'
    )

    try:
        with open(check_svg_path, "w", encoding="utf-8") as f:
            f.write(check_svg)
        logger.info("Created runtime check.svg at %s", check_svg_path)
    except Exception as e:
        logger.warning("Failed to create check.svg: %s", e)

    return check_svg_path


def main():
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon

    # Create persistent directories before any module needs them
    from config import ensure_dirs, cleanup_temp_dir
    ensure_dirs()

    cleanup_temp_dir(max_age_hours=24)

    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    app = QApplication(sys.argv)

    # Load stylesheet from external QSS file
    base = _runtime_base_dir()
    stylesheet = _load_stylesheet(base)

    # Generate checkbox check icon in a writable location
    check_svg_path = _ensure_check_svg()
    check_path_qt = check_svg_path.replace("\\", "/")

    checkbox_override = f"""
    QCheckBox::indicator:checked {{
        border: none;
        image: url({check_path_qt});
    }}
    """
    app.setStyleSheet(stylesheet + checkbox_override)

    # Set app icon (read-only asset is fine)
    icon_path = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Check FFmpeg availability before launching UI
    if not _check_ffmpeg():
        from i18n import tr
        QMessageBox.critical(
            None,
            "FFmpeg Required",
            tr("ffmpeg_not_found")
        )
        sys.exit(1)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("VidMark started")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()