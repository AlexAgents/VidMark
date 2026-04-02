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
Main Window
"""
import os
import sys
import json
import logging
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMessageBox, QLabel, QDialog, QDialogButtonBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QApplication,
    QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QColor
import qtawesome as qta

from config import (APP_NAME, APP_VERSION, APP_AUTHOR,
                    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
                    WatermarkSettings, SETTINGS_DIR)
from i18n import tr, get_language
from ui.embed_tab import EmbedTab
from ui.extract_tab import ExtractTab
from ui.attack_tab import AttackTab
# FIX: MetricsTab removed.
# All metrics functionality lives in AllMetricsDialog below.
from ui.log_tab import LogTab
from ui.settings_dialog import SettingsDialog
from workers.video_worker import (EmbedWorker, ExtractWorker,
                                  AttackTestWorker)

logger = logging.getLogger(__name__)

GITHUB_URL = "https://github.com/AlexAgents/VidMark"

# File to persist "don't show again" preferences
_PREFS_FILE = os.path.join(SETTINGS_DIR, "prefs.json")


def _load_prefs() -> dict:
    try:
        if os.path.exists(_PREFS_FILE):
            with open(_PREFS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Failed to load preferences: %s", e)
    return {}


def _save_prefs(prefs: dict):
    try:
        with open(_PREFS_FILE, 'w') as f:
            json.dump(prefs, f)
    except Exception as e:
        logger.warning("Failed to save preferences: %s", e)


STATUS_TIMEOUT_MS = 8000  # 8 seconds


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("about_title"))
        self.setFixedSize(480, 280)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowContextHelpButtonHint
            | Qt.MSWindowsFixedSizeDialogHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "assets", "icon.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            pm = icon.pixmap(256, 256)
            if not pm.isNull():
                pm = pm.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pm)
            else:
                pm = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pm)
        else:
            icon_label.setPixmap(
                qta.icon('fa5s.shield-alt', color='#007aff').pixmap(64, 64))
        layout.addWidget(icon_label)

        name_l = QLabel(f"{APP_NAME} v{APP_VERSION}")
        name_l.setAlignment(Qt.AlignCenter)
        name_l.setStyleSheet("font-size:20px;font-weight:700;color:#1d1d1f;")
        layout.addWidget(name_l)

        desc_l = QLabel(tr("about_description"))
        desc_l.setAlignment(Qt.AlignCenter)
        desc_l.setWordWrap(True)
        desc_l.setStyleSheet("font-size:12px;color:#1d1d1f;")
        layout.addWidget(desc_l)

        layout.addSpacing(10)

        auth_l = QLabel(f"\u00A9 2026 {APP_AUTHOR}")
        auth_l.setAlignment(Qt.AlignCenter)
        auth_l.setStyleSheet("font-size:12px;color:#86868b;")
        layout.addWidget(auth_l)

        gh = QLabel(
            f'<a href="{GITHUB_URL}" '
            f'style="color:#007aff;font-size:11px;text-decoration:none;">'
            f'{GITHUB_URL}</a>')
        gh.setAlignment(Qt.AlignCenter)
        gh.setOpenExternalLinks(True)
        layout.addWidget(gh)

        layout.addStretch()

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.setCenterButtons(True)
        bb.button(QDialogButtonBox.Close).setText(tr("close"))
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)


def _color_for_value(val, good_thresh, warn_thresh, higher_is_better=True):
    if higher_is_better:
        if val >= good_thresh:
            return "#34c759"
        elif val >= warn_thresh:
            return "#ff9500"
        else:
            return "#ff3b30"
    else:
        if val <= good_thresh:
            return "#34c759"
        elif val <= warn_thresh:
            return "#ff9500"
        else:
            return "#ff3b30"


def _create_metrics_table(headers, rows):
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionMode(QTableWidget.NoSelection)
    table.setAlternatingRowColors(True)
    table.setStyleSheet(
        "QTableWidget{background:#ffffff;border:1px solid #d2d2d7;border-radius:6px;}"
        "QTableWidget::item{padding:6px;}"
        "QHeaderView::section{background:#f5f5f7;border:1px solid #d2d2d7;"
        "padding:6px;font-weight:600;font-size:12px;color:#6e6e73;}"
    )
    for r, row_data in enumerate(rows):
        for c, (text, color) in enumerate(row_data):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(Qt.AlignCenter)
            if color:
                item.setForeground(QColor(color))
                item.setData(Qt.FontRole, None)
            table.setItem(r, c, item)
    table.resizeRowsToContents()
    return table


def _table_to_text(table: QTableWidget) -> str:
    lines = []
    headers = []
    for c in range(table.columnCount()):
        h = table.horizontalHeaderItem(c)
        headers.append(h.text() if h else "")
    lines.append("\t".join(headers))
    for r in range(table.rowCount()):
        row = []
        for c in range(table.columnCount()):
            item = table.item(r, c)
            row.append(item.text() if item else "")
        lines.append("\t".join(row))
    return "\n".join(lines)


class AllMetricsDialog(QDialog):
    """Dialog showing all metrics in two styled tables."""
    def __init__(self, video_info, wm_info, settings_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("all_metrics"))
        self.setMinimumSize(720, 540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        vid_label = QLabel(tr("video_information"))
        vid_label.setStyleSheet("font-size:14px;font-weight:700;color:#1d1d1f;")
        layout.addWidget(vid_label)

        vid_rows = []
        if video_info:
            vid_rows.append([("Resolution", None),
                             (f"{video_info.get('width', 'N/A')}x{video_info.get('height', 'N/A')}", None)])
            vid_rows.append([("FPS", None), (f"{video_info.get('fps', 'N/A')}", None)])
            vid_rows.append([("Total Frames", None), (f"{video_info.get('frame_count', 'N/A')}", None)])
            dur = video_info.get('duration', 0)
            vid_rows.append([("Duration", None), (f"{dur:.1f}s", None)])
            vid_rows.append([("Audio", None),
                             ("Yes" if video_info.get('has_audio') else "No",
                              "#34c759" if video_info.get('has_audio') else "#ff9500")])
            vid_rows.append([("Format", None), (f"{video_info.get('format', 'N/A')}", None)])
            vid_rows.append([("Input", None), (f"{video_info.get('input_path', 'N/A')}", None)])
            vid_rows.append([("Output", None), (f"{video_info.get('output_path', 'N/A')}", None)])
        else:
            vid_rows.append([(tr("no_video_info"), None), ("—", None)])

        self.vid_table = _create_metrics_table(
            [tr("metric_parameter"), tr("metric_value")], vid_rows)
        layout.addWidget(self.vid_table)

        copy_vid_btn = QPushButton(
            qta.icon('fa5s.copy', color='#007aff'), tr("copy_table"))
        copy_vid_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;border-radius:6px;"
            "padding:5px 12px;font-weight:500;}"
            "QPushButton:hover{background:#e8e8ed;}")
        copy_vid_btn.clicked.connect(lambda: self._copy_table(self.vid_table))
        layout.addWidget(copy_vid_btn, 0, Qt.AlignRight)

        wm_label = QLabel(tr("watermark_information"))
        wm_label.setStyleSheet("font-size:14px;font-weight:700;color:#1d1d1f;")
        layout.addWidget(wm_label)

        wm_rows = []
        if wm_info:
            wm_rows.append([("Author", None), (f"{wm_info.get('author_text', 'N/A')}", "#007aff")])
            wm_rows.append([("UUID", None), (f"{wm_info.get('uuid_hex', 'N/A')}", None)])
            wm_rows.append([("Timestamp", None), (f"{wm_info.get('timestamp_str', 'N/A')}", None)])
            wm_rows.append([("Total bits", None), (f"{wm_info.get('total_bits', 'N/A')}", None)])
            wm_rows.append([("WM bits", None), (f"{wm_info.get('wm_bits_length', 'N/A')}", None)])
            if settings_info:
                wv = settings_info.get('wavelet', 'N/A')
                wv_color = "#34c759" if wv in ("haar", "db2") else "#ff9500" if wv in ("db4", "bior4.4") else "#ff3b30"
                wm_rows.append([("Wavelet", None), (wv, wv_color)])
                lvl = settings_info.get('dwt_level', 'N/A')
                lvl_color = "#34c759" if lvl == 1 else "#ff9500" if lvl == 2 else "#ff3b30"
                wm_rows.append([("DWT Level", None), (str(lvl), lvl_color)])
                wm_rows.append([("Block", None), (f"{settings_info.get('block_size', 'N/A')}", None)])
                delta = settings_info.get('delta', 0)
                d_color = _color_for_value(delta, 30, 15) if isinstance(delta, (int, float)) else None
                wm_rows.append([("Delta", None), (f"{delta}", d_color)])
                crf = settings_info.get('crf', 0)
                c_color = _color_for_value(crf, 10, 23, higher_is_better=False) if isinstance(crf, (int, float)) else None
                wm_rows.append([("CRF", None), (f"{crf}", c_color)])
                wm_rows.append([("ECC", None), (f"{settings_info.get('ecc_type', 'N/A')}", None)])
                wm_rows.append([("Strength", None), (f"{settings_info.get('strength', 'N/A')}", None)])
        else:
            wm_rows.append([(tr("no_video_info"), None), ("—", None)])

        self.wm_table = _create_metrics_table(
            [tr("metric_parameter"), tr("metric_value")], wm_rows)
        layout.addWidget(self.wm_table)

        copy_wm_btn = QPushButton(
            qta.icon('fa5s.copy', color='#007aff'), tr("copy_table"))
        copy_wm_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;border-radius:6px;"
            "padding:5px 12px;font-weight:500;}"
            "QPushButton:hover{background:#e8e8ed;}")
        copy_wm_btn.clicked.connect(lambda: self._copy_table(self.wm_table))
        layout.addWidget(copy_wm_btn, 0, Qt.AlignRight)

        layout.addStretch()
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.setCenterButtons(True)
        bb.button(QDialogButtonBox.Close).setText(tr("close"))
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _copy_table(self, table):
        QApplication.clipboard().setText(_table_to_text(table))
        p = self.parent()
        if p and hasattr(p, '_set_status'):
            p._set_status(tr("status_copied"))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = WatermarkSettings()
        self.embed_worker = None
        self.extract_worker = None
        self.attack_worker = None
        self.atk_frame = None
        self.atk_bits = None
        self.atk_settings = None
        self._metrics_video_info = None
        self._metrics_wm_info = None
        self._metrics_settings_info = None
        self._prefs = _load_prefs()
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status)
        self._setup_ui()

    def _set_status(self, msg: str, timeout_ms: int = STATUS_TIMEOUT_MS):
        """Show status bar message with auto-clear timeout."""
        self.statusBar().showMessage(msg)
        if timeout_ms > 0:
            self._status_timer.start(timeout_ms)

    def _clear_status(self):
        self.statusBar().showMessage(tr("ready"))

    def _confirm_with_dont_show(self, pref_key: str, title: str, message: str) -> bool:
        """Show confirmation dialog with 'Don't show again' checkbox."""
        if self._prefs.get(pref_key, False):
            return True

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-size:13px;")
        layout.addWidget(msg_label)

        cb = QCheckBox(tr("dont_show_again"))
        cb.setStyleSheet("font-size:11px;color:#86868b;")
        layout.addWidget(cb)

        bb = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        bb.setCenterButtons(True)
        no_btn = bb.button(QDialogButtonBox.No)
        if no_btn:
            no_btn.setText(tr("cancel"))
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        layout.addWidget(bb)

        result = dlg.exec_()
        if result == QDialog.Accepted:
            if cb.isChecked():
                self._prefs[pref_key] = True
                _save_prefs(self._prefs)
            return True
        return False

    def _setup_ui(self):
        self.setWindowTitle(tr("app_title", version=APP_VERSION))
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1060, 700)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(6, 6, 6, 6)

        self.tabs = QTabWidget()
        self.embed_tab = EmbedTab()
        self.extract_tab = ExtractTab()
        self.attack_tab = AttackTab()
        self.log_tab = LogTab()

        self.tabs.addTab(self.embed_tab,
                         qta.icon('fa5s.stamp', color='#007aff'),
                         tr("tab_embed"))
        self.tabs.addTab(self.extract_tab,
                         qta.icon('fa5s.search', color='#5ac8fa'),
                         tr("tab_extract"))
        self.tabs.addTab(self.attack_tab,
                         qta.icon('fa5s.flask', color='#ff9500'),
                         tr("tab_attack"))
        self.tabs.addTab(self.log_tab,
                         qta.icon('fa5s.file-alt', color='#86868b'),
                         tr("tab_log"))
        layout.addWidget(self.tabs)
        self._set_status(tr("ready"))

        # Connections
        self.embed_tab.embed_requested.connect(self._start_embed)
        self.embed_tab.stop_requested.connect(self._cancel)
        self.embed_tab.settings_requested.connect(self._open_settings)
        self.embed_tab.language_changed.connect(self._on_language_changed)
        self.embed_tab.all_metrics_requested.connect(self._show_all_metrics)
        self.embed_tab.reset_requested.connect(self._handle_reset)
        self.embed_tab.about_requested.connect(self._show_about)
        self.embed_tab.status_message.connect(self._set_status)

        self.extract_tab.extract_requested.connect(self._start_extract)
        self.extract_tab.reset_requested.connect(lambda: self._handle_reset("extract"))

        self.attack_tab.test_requested.connect(self._start_attack)
        self.attack_tab.reset_requested.connect(lambda: self._handle_reset("attack"))
        self.attack_tab.status_message.connect(self._set_status)

        self.log_tab.clear_requested.connect(self._handle_clear_log)
        self.log_tab.status_message.connect(self._set_status)

    def _show_about(self):
        AboutDialog(self).exec_()

    def _show_all_metrics(self):
        AllMetricsDialog(
            self._metrics_video_info,
            self._metrics_wm_info,
            self._metrics_settings_info,
            self
        ).exec_()

    def _handle_reset(self, scope):
        pref_key = "skip_reset_confirm"
        title = tr("reset_confirm_title")
        msg = tr("reset_confirm_all_message") if scope == "all" else tr("reset_confirm_message")

        if not self._confirm_with_dont_show(pref_key, title, msg):
            return

        # FIX: Do NOT reset self._prefs here.
        # Previously this cleared all prefs including "don't show again" flags,
        # which was unexpected behavior for the user.

        if scope in ("embed", "all"):
            self.embed_tab.reset_tab()
            self.atk_frame = None
            self.atk_bits = None
            self.atk_settings = None
            self.attack_tab.set_ready(False)
        if scope in ("extract", "all"):
            self.extract_tab.reset_tab()
        if scope in ("attack", "all"):
            self.attack_tab.reset_tab()
        if scope in ("log", "all"):
            self.log_tab.force_clear()

        self._set_status(tr("status_reset_done"))

    def _handle_clear_log(self):
        pref_key = "skip_clear_confirm"
        if not self._confirm_with_dont_show(
                pref_key, tr("clear_confirm_title"), tr("clear_confirm_message")):
            return
        self.log_tab.force_clear()
        self._set_status(tr("status_log_cleared"))

    def _refresh_texts(self):
        self.setWindowTitle(tr("app_title", version=APP_VERSION))
        self.tabs.setTabText(0, tr("tab_embed"))
        self.tabs.setTabText(1, tr("tab_extract"))
        self.tabs.setTabText(2, tr("tab_attack"))
        self.tabs.setTabText(3, tr("tab_log"))
        self._set_status(tr("ready"))
        self.embed_tab.retranslate_ui()
        self.extract_tab.retranslate_ui()
        self.attack_tab.retranslate_ui()
        self.log_tab.retranslate_ui()

    def _on_language_changed(self):
        self._refresh_texts()
        self._set_status(tr("language_switched"))

    def _log(self, msg):
        self.log_tab.append_log(msg)

    def _start_embed(self, inp, out, author):
        if self.embed_worker and self.embed_worker.isRunning():
            return
        # FIX: disable UI before creating worker to prevent double-click race
        self.embed_tab.set_enabled(False)
        s = self.settings.copy()
        self.embed_worker = EmbedWorker(inp, out, s, author)
        self.embed_worker.progress.connect(
            lambda p, m: (
                self.embed_tab.set_progress(p, m),
                self._set_status(m)))
        self.embed_worker.finished.connect(self._on_embed_done)
        self.embed_worker.log.connect(self._log)
        self.embed_worker.start()

    def _on_embed_done(self, ok, msg, info):
        self.embed_tab.set_enabled(True)
        if not ok:
            if msg == tr("status_cancelled"):
                self.embed_tab.reset_status()
                self._set_status(tr("status_cancelled"))
                self._log(f" {tr('status_cancelled')}")
                return
            self._log(f" {msg}")
            self._set_status(tr("error"))
            QMessageBox.warning(self, tr("error"), msg)
            return

        self._log(f" {msg}")
        self._set_status(tr("status_done"))

        avg_p = info.get("avg_psnr", 0)
        avg_s = info.get("avg_ssim", 0)
        vnc = info.get("verification_nc", 0)
        elapsed = info.get("elapsed_time", 0)
        pi = info.get("payload_info", {})
        kf_path = info.get("keyfile_path", "")

        self.embed_tab.update_metrics(
            avg_p, avg_s, vnc, elapsed,
            uuid_hex=pi.get('uuid_hex', ''),
            keyfile_path=kf_path)

        vi = info.get("video_info")
        if vi:
            self._metrics_video_info = vi
        pi["wm_bits_length"] = info.get("wm_bits_length", 0)
        pi["author_text"] = info.get("author_text", "")
        self._metrics_wm_info = pi

        es = info.get("embed_settings")
        if es:
            self._metrics_settings_info = {
                "wavelet": es.wavelet, "dwt_level": es.dwt_level,
                "block_size": es.block_size, "strength": es.strength_preset.value,
                "delta": es.get_delta(), "crf": es.get_crf(),
                "ecc_type": es.ecc_type.value,
            }

        frame = info.get("first_wm_frame")
        bits = info.get("wm_bits")
        embed_s = info.get("embed_settings")
        if frame is not None and bits is not None and embed_s is not None:
            self.atk_frame = frame.copy()
            self.atk_bits = bits.copy()
            self.atk_settings = embed_s
            self.embed_tab.set_watermarked_preview(frame)
            self.attack_tab.set_ready(True)

        author = info.get("author_text", "")
        QMessageBox.information(
            self, tr("success"),
            f"{msg}\n\n"
            f"{tr('author')}: {author or tr('auto_uuid')}\n"
            f"UUID: {pi.get('uuid_hex', '')}\n"
            f"PSNR: {avg_p:.2f} dB\n"
            f"SSIM: {avg_s:.4f}\n"
            f"NC: {vnc:.4f}\n"
            f"Key: {kf_path}")

    def _start_extract(self, video, keyfile):
        if self.extract_worker and self.extract_worker.isRunning():
            return
        self.extract_worker = ExtractWorker(video, keyfile)
        self.extract_worker.progress.connect(
            lambda p, m: (
                self.extract_tab.set_progress(p, m),
                self._set_status(m)))
        self.extract_worker.finished.connect(self._on_extract_done)
        self.extract_worker.log.connect(self._log)
        self.extract_tab.set_enabled(False)
        self.extract_worker.start()

    def _on_extract_done(self, ok, msg, info):
        self.extract_tab.set_enabled(True)
        self._set_status(tr("status_done") if ok else tr("error"))
        if ok:
            self.extract_tab.display_results(info)
            atk_frame = info.get("attack_frame")
            atk_bits = info.get("attack_bits")
            atk_settings = info.get("attack_settings")
            status = info.get("status")

            if (atk_frame is not None and
                atk_bits is not None and
                atk_settings is not None and
                status == "VERIFIED"):

                self.atk_frame = atk_frame
                self.atk_bits = atk_bits
                self.atk_settings = atk_settings
                self.attack_tab.set_ready(True)
                self._log(f"{tr('log_result')}: {msg}")
            else:
                self.attack_tab.set_ready(False)
                if status != "VERIFIED":
                    self._log(f"Attack tab disabled: Watermark status is {status}")

    def _start_attack(self, attacks, save, spath):
        if self.attack_worker and self.attack_worker.isRunning():
            return
        if self.atk_frame is None:
            QMessageBox.warning(self, tr("not_ready"), tr("embed_first"))
            return
        self.attack_worker = AttackTestWorker(
            self.atk_frame, self.atk_bits,
            self.atk_settings, attacks, save, spath)
        self.attack_worker.progress.connect(
            lambda p, m: (
                self.attack_tab.set_progress(p, m),
                self._set_status(m)))
        self.attack_worker.result_ready.connect(self.attack_tab.add_result)
        self.attack_worker.finished.connect(self._on_attack_done)
        self.attack_worker.log.connect(self._log)
        self.attack_tab.set_enabled(False)
        self.attack_worker.start()

    def _on_attack_done(self, ok, msg):
        self.attack_tab.set_enabled(True)
        if not ok and msg == tr("status_cancelled"):
            self.attack_tab.reset_status()
            self._set_status(tr("status_cancelled"))
        else:
            self._set_status(
                tr("attack_test_complete") if ok else tr("error"))
        self._log(msg)

    def _cancel(self):
        for w in [self.embed_worker, self.extract_worker, self.attack_worker]:
            if w and w.isRunning():
                w.cancel()
        self._set_status(tr("status_cancelled"))

    def _open_settings(self):
        d = SettingsDialog(self.settings, self)
        if d.exec_() == d.Accepted:
            self.settings = d.get_settings()
            c = self.settings.get_compatibility_color()
            i = {"excellent": "", "doubtful": "", "poor": ""}.get(c, "")
            self._log(
                f"{i} {tr('log_settings')}: "
                f"{self.settings.wavelet} L{self.settings.dwt_level} "
                f"B{self.settings.block_size} "
                f"Δ={self.settings.get_delta()} "
                f"CRF={self.settings.get_crf()} "
                f"key={self.settings.scramble_seed}")
            self._set_status(tr("status_settings_applied"))

    def closeEvent(self, event):
        self._cancel()
        event.accept()