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
Embed Tab
"""
import os
import subprocess

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QProgressBar, QGroupBox, QFileDialog, QComboBox,
    QSizePolicy, QGridLayout, QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import qtawesome as qta

from config import VIDEO_FILTER
from i18n import tr, get_language, set_language
from utils.video_utils import get_video_info, get_first_frame
from utils.image_utils import frame_to_pixmap


class PreviewLabel(QLabel):
    """Preview label with right-click context menu for ffplay."""

    def __init__(self, parent_tab, role="original"):
        super().__init__()
        self._parent_tab = parent_tab
        self._role = role
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(280, 160)
        self.setStyleSheet(
            "border:1px solid #d2d2d7;background:#f0f0f5;border-radius:8px;")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#ffffff;border:1px solid #d2d2d7;border-radius:8px;padding:4px;}"
            "QMenu::item{padding:6px 20px;color:#1d1d1f;}"
            "QMenu::item:selected{background:#007aff;color:white;border-radius:4px;}")

        has_items = False
        if self._role == "original" and self._parent_tab.input_video_path:
            act = menu.addAction(
                qta.icon('fa5s.play-circle', color='#007aff'),
                tr("preview_original_ffplay"))
            act.triggered.connect(
                lambda: self._play_ffplay(self._parent_tab.input_video_path))
            has_items = True

        if self._role == "watermarked":
            path = getattr(self._parent_tab, '_last_output_path', '')
            if path and os.path.exists(path):
                act = menu.addAction(
                    qta.icon('fa5s.play-circle', color='#34c759'),
                    tr("preview_watermarked_ffplay"))
                act.triggered.connect(lambda: self._play_ffplay(path))
                has_items = True

        if not has_items:
            act = menu.addAction(tr("no_video_loaded"))
            act.setEnabled(False)

        menu.exec_(self.mapToGlobal(pos))

    def _play_ffplay(self, path):
        try:
            subprocess.Popen(
                ["ffplay", "-autoexit", "-window_title",
                 f"Preview — {os.path.basename(path)}", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            QMessageBox.warning(self, "ffplay", tr("ffplay_not_found"))
        except Exception as e:
            QMessageBox.warning(self, "ffplay", str(e))


class OverlayLabel(QLabel):
    """Semi-transparent overlay label inside preview."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            "background-color: rgba(0,0,0,0.45); color: white;"
            "font-size: 12px; font-weight: 600; border-radius: 4px;"
            "padding: 3px 10px;")
        self.setFixedHeight(24)

    def show_overlay(self):
        self.setVisible(True)

    def hide_overlay(self):
        self.setVisible(False)


class EmbedTab(QWidget):
    embed_requested = pyqtSignal(str, str, str)
    stop_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    language_changed = pyqtSignal()
    reset_requested = pyqtSignal(str)
    all_metrics_requested = pyqtSignal()
    about_requested = pyqtSignal()
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.input_video_path = ""
        self._last_output_path = ""
        self._busy = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header row
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        self.about_btn = QPushButton(
            qta.icon('fa5s.info-circle', color='#007aff'), tr("about_btn"))
        self.about_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;"
            "border-radius:6px;padding:5px 12px;color:#007aff;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#e8e8ed;}")
        self.about_btn.clicked.connect(self.about_requested.emit)
        header_row.addWidget(self.about_btn)

        header_row.addStretch()

        self.lang_label = QLabel(tr("language_short") + ":")
        self.lang_label.setStyleSheet("color:#86868b;font-size:12px;")
        header_row.addWidget(self.lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(75)
        self.lang_combo.setFixedHeight(30)
        self.lang_combo.addItem("EN", "en")
        self.lang_combo.addItem("RU", "ru")

        current_lang = get_language()
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == current_lang:
                self.lang_combo.setCurrentIndex(i)
                break

        self.lang_combo.currentIndexChanged.connect(self._change_language)
        header_row.addWidget(self.lang_combo)

        self.reset_btn = QPushButton(
            qta.icon('fa5s.undo', color='#ff3b30'), tr("reset"))
        self.reset_btn.setFixedHeight(30)
        self.reset_btn.setMinimumWidth(75)
        self.reset_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;"
            "border-radius:6px;padding:5px 12px;color:#ff3b30;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#ffe5e5;}")
        self.reset_btn.clicked.connect(self._do_reset_current)
        header_row.addWidget(self.reset_btn)

        layout.addLayout(header_row)

        # Input group
        self.input_group = QGroupBox(tr("input_video"))
        input_inner = QVBoxLayout(self.input_group)
        input_inner.setContentsMargins(10, 14, 10, 10)
        input_inner.setSpacing(4)

        input_row = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText(tr("select_input_video"))
        self.input_path_edit.setReadOnly(True)
        self.browse_btn = QPushButton(
            qta.icon('fa5s.folder-open', color='#ffffff'), tr("browse"))
        self.browse_btn.setMinimumHeight(34)
        self.browse_btn.setStyleSheet(
            "QPushButton{background:#007aff;color:white;border:none;border-radius:6px;"
            "padding:6px 14px;font-weight:600;}"
            "QPushButton:hover{background:#0051d5;}")
        self.browse_btn.clicked.connect(self._browse_input)
        input_row.addWidget(self.input_path_edit, 1)
        input_row.addWidget(self.browse_btn, 0)
        input_inner.addLayout(input_row)

        self.video_info_label = QLabel(tr("no_video_loaded"))
        self.video_info_label.setStyleSheet(
            "color:#86868b;font-size:11px;padding:0 4px;")
        self.video_info_label.setWordWrap(True)
        input_inner.addWidget(self.video_info_label)
        layout.addWidget(self.input_group)

        # Payload group
        self.payload_group = QGroupBox(tr("watermark_payload"))
        payload_layout = QHBoxLayout(self.payload_group)
        payload_layout.setContentsMargins(10, 14, 10, 10)

        self.author_label_w = QLabel(tr("author_id"))
        self.author_label_w.setStyleSheet("font-weight:600;color:#1d1d1f;font-size:12px;")
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText(tr("author_placeholder"))
        self.author_edit.setMaxLength(64)
        payload_layout.addWidget(self.author_label_w)
        payload_layout.addWidget(self.author_edit, 1)
        layout.addWidget(self.payload_group)

        # Preview group
        self.preview_group = QGroupBox(tr("preview"))
        preview_outer = QVBoxLayout(self.preview_group)
        preview_outer.setContentsMargins(10, 14, 10, 10)
        preview_outer.setSpacing(6)

        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(10)

        orig_container = QWidget()
        orig_container.setMinimumSize(280, 165)
        orig_vbox = QVBoxLayout(orig_container)
        orig_vbox.setContentsMargins(0, 0, 0, 0)
        orig_vbox.setSpacing(0)
        self.preview_original = PreviewLabel(self, "original")
        self.orig_overlay = OverlayLabel(tr("original"), self.preview_original)
        orig_vbox.addWidget(self.preview_original)
        preview_layout.addWidget(orig_container, 1)

        wm_container = QWidget()
        wm_container.setMinimumSize(280, 165)
        wm_vbox = QVBoxLayout(wm_container)
        wm_vbox.setContentsMargins(0, 0, 0, 0)
        wm_vbox.setSpacing(0)
        self.preview_watermarked = PreviewLabel(self, "watermarked")
        self.wm_overlay = OverlayLabel(tr("watermarked"), self.preview_watermarked)
        wm_vbox.addWidget(self.preview_watermarked)
        preview_layout.addWidget(wm_container, 1)

        preview_outer.addLayout(preview_layout)

        # Metrics row — unified fixed height, stretch to fill
        self.metrics_row_widget = QWidget()
        metrics_row = QHBoxLayout(self.metrics_row_widget)
        metrics_row.setContentsMargins(0, 0, 0, 0)
        metrics_row.setSpacing(0)

        self.metrics_panel = QWidget()
        mp_layout = QGridLayout(self.metrics_panel)
        mp_layout.setContentsMargins(8, 6, 8, 6)
        mp_layout.setHorizontalSpacing(6)
        mp_layout.setVerticalSpacing(3)
        self.metrics_panel.setStyleSheet(
            "background:#ffffff;border:1px solid #e5e5ea;border-radius:6px;")
        self.metrics_panel.setFixedHeight(70)

        lbl_s = "color:#86868b;font-size:11px;"
        val_s = "font-size:13px;font-family:'SF Mono',monospace;font-weight:600;"
        FIELD_W = 90  # Increased from 80

        self.m_psnr_t = QLabel("PSNR:")
        self.m_psnr_t.setStyleSheet(lbl_s)
        self.m_psnr_v = QLabel("—")
        self.m_psnr_v.setStyleSheet(val_s)
        self.m_psnr_v.setMinimumWidth(FIELD_W)

        self.m_ssim_t = QLabel("SSIM:")
        self.m_ssim_t.setStyleSheet(lbl_s)
        self.m_ssim_v = QLabel("—")
        self.m_ssim_v.setStyleSheet(val_s)
        self.m_ssim_v.setMinimumWidth(FIELD_W)

        self.m_nc_t = QLabel("NC:")
        self.m_nc_t.setStyleSheet(lbl_s)
        self.m_nc_v = QLabel("—")
        self.m_nc_v.setStyleSheet(val_s)
        self.m_nc_v.setMinimumWidth(FIELD_W)

        self.m_time_t = QLabel(tr("time_elapsed"))
        self.m_time_t.setStyleSheet(lbl_s)
        self.m_time_v = QLabel("—")
        self.m_time_v.setStyleSheet(val_s)
        self.m_time_v.setMinimumWidth(FIELD_W)

        self.m_uuid_t = QLabel("UUID:")
        self.m_uuid_t.setStyleSheet(lbl_s)
        self.m_uuid_v = QLabel("—")
        self.m_uuid_v.setStyleSheet(lbl_s + "font-family:monospace;font-size:10px;")
        self.m_uuid_v.setMinimumWidth(140)
        self.m_uuid_v.setWordWrap(True)
        
        # Row 0: PSNR | SSIM | NC
        mp_layout.addWidget(self.m_psnr_t, 0, 0)
        mp_layout.addWidget(self.m_psnr_v, 0, 1)
        mp_layout.addWidget(self.m_ssim_t, 0, 2)
        mp_layout.addWidget(self.m_ssim_v, 0, 3)
        mp_layout.addWidget(self.m_nc_t, 0, 4)
        mp_layout.addWidget(self.m_nc_v, 0, 5)

        # Row 1: Time | UUID | All Metrics button
        mp_layout.addWidget(self.m_time_t, 1, 0)
        mp_layout.addWidget(self.m_time_v, 1, 1)
        mp_layout.addWidget(self.m_uuid_t, 1, 2)
        mp_layout.addWidget(self.m_uuid_v, 1, 3)

        # All Metrics button — same height as NC row
        self.metrics_btn = QPushButton(
            qta.icon('fa5s.chart-bar', color='#007aff'), tr("all_metrics"))
        self.metrics_btn.setFixedHeight(28)
        self.metrics_btn.setMinimumWidth(FIELD_W * 2 + 6)
        self.metrics_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;"
            "border-radius:6px;padding:5px 12px;color:#007aff;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#e8e8ed;}")
        self.metrics_btn.clicked.connect(self.all_metrics_requested.emit)
        mp_layout.addWidget(self.metrics_btn, 1, 4, 1, 2)

        # Let columns stretch equally
        for col in range(6):
            mp_layout.setColumnStretch(col, 1)

        metrics_row.addWidget(self.metrics_panel, 1)
        self.metrics_row_widget.setVisible(False)
        preview_outer.addWidget(self.metrics_row_widget)

        layout.addWidget(self.preview_group, 1)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 4, 0, 4)
        actions_layout.setSpacing(10)

        self.settings_btn = QPushButton(
            qta.icon('fa5s.cog', color='#6e6e73'), tr("settings_short"))
        self.settings_btn.setFixedSize(150, 44)
        self.settings_btn.setStyleSheet(
            "QPushButton{background:#ffffff;color:#1d1d1f;font-size:13px;font-weight:600;"
            "border:1px solid #d2d2d7;border-radius:8px;}"
            "QPushButton:hover{background:#e8e8ed;border-color:#c7c7cc;}"
            "QPushButton:pressed{background:#d1d1d6;}")
        self.settings_btn.clicked.connect(self.settings_requested.emit)

        self.embed_btn = QPushButton(
            qta.icon('fa5s.play', color='#FFFFFF'), tr("start"))
        self.embed_btn.setMinimumHeight(44)
        self.embed_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.embed_btn.setStyleSheet(
            "QPushButton{background:#007aff;color:white;font-size:16px;font-weight:700;"
            "border-radius:8px;padding:4px 16px;border:none;}"
            "QPushButton:hover{background:#0051d5;}"
            "QPushButton:disabled{background:#e5e5ea;color:#aeaeb2;}")
        self.embed_btn.clicked.connect(self._start_embed)
        self.embed_btn.setEnabled(False)

        self.stop_btn = QPushButton(
            qta.icon('fa5s.stop', color='#FFFFFF'), tr("stop_short"))
        self.stop_btn.setFixedSize(120, 44)
        self.stop_btn.setStyleSheet(
            "QPushButton{background:#ff3b30;color:white;font-size:13px;font-weight:600;"
            "border-radius:8px;border:none;}"
            "QPushButton:hover{background:#d63028;}"
            "QPushButton:disabled{background:#e5e5ea;color:#aeaeb2;}")
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        self.stop_btn.setEnabled(False)

        actions_layout.addWidget(self.settings_btn, 0)
        actions_layout.addWidget(self.embed_btn, 1)
        actions_layout.addWidget(self.stop_btn, 0)
        layout.addLayout(actions_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(18)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _do_reset_current(self):
        """Reset only the currently active tab (determined by parent tab widget)."""
        main_win = self.window()
        if hasattr(main_win, 'tabs'):
            idx = main_win.tabs.currentIndex()
            scope_map = {0: "embed", 1: "extract", 2: "attack", 3: "log"}
            scope = scope_map.get(idx, "embed")
        else:
            scope = "embed"
        self.reset_requested.emit(scope)

    def retranslate_ui(self):
        self.about_btn.setText(tr("about_btn"))
        self.lang_label.setText(tr("language_short") + ":")
        self.input_group.setTitle(tr("input_video"))
        self.input_path_edit.setPlaceholderText(tr("select_input_video"))
        self.browse_btn.setText(tr("browse"))
        if not self.input_video_path:
            self.video_info_label.setText(tr("no_video_loaded"))
        self.payload_group.setTitle(tr("watermark_payload"))
        self.author_label_w.setText(tr("author_id"))
        self.author_edit.setPlaceholderText(tr("author_placeholder"))
        self.preview_group.setTitle(tr("preview"))
        self.orig_overlay.setText(tr("original"))
        self.wm_overlay.setText(tr("watermarked"))
        self.settings_btn.setText(tr("settings_short"))
        self.embed_btn.setText(tr("start"))
        self.stop_btn.setText(tr("stop_short"))
        self.m_time_t.setText(tr("time_elapsed"))
        self.metrics_btn.setText(tr("all_metrics"))
        self.reset_btn.setText(tr("reset"))

    def update_metrics(self, psnr, ssim, nc, elapsed,
                       uuid_hex="", keyfile_path=""):
        self.metrics_row_widget.setVisible(True)

        def _color(val, good, warn):
            return "#34c759" if val >= good else "#ff9500" if val >= warn else "#ff3b30"

        pc = _color(psnr, 40, 35)
        self.m_psnr_v.setText(f"{psnr:.2f} dB")
        self.m_psnr_v.setStyleSheet(
            f"color:{pc};font-size:13px;font-family:monospace;font-weight:700;")

        sc = _color(ssim, 0.95, 0.90)
        self.m_ssim_v.setText(f"{ssim:.4f}")
        self.m_ssim_v.setStyleSheet(
            f"color:{sc};font-size:13px;font-family:monospace;font-weight:700;")

        ncc = _color(nc, 0.85, 0.70)
        self.m_nc_v.setText(f"{nc:.4f}")
        self.m_nc_v.setStyleSheet(
            f"color:{ncc};font-size:13px;font-family:monospace;font-weight:700;")

        self.m_time_v.setText(f"{elapsed:.1f}s")
        self.m_time_v.setStyleSheet(
            "color:#007aff;font-size:13px;font-family:monospace;font-weight:700;")

        if uuid_hex:
            self.m_uuid_v.setText(uuid_hex)

    def _change_language(self, index):
        lang = self.lang_combo.itemData(index)
        if lang and lang != get_language():
            set_language(lang)
            self.language_changed.emit()

    def _browse_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("select_input_video_title"), "", VIDEO_FILTER)
        if path:
            self.input_video_path = path
            self.input_path_edit.setText(path)
            self.embed_btn.setEnabled(not self._busy)
            self.status_message.emit(
                tr("status_video_loaded", name=os.path.basename(path)))

            # Clear previous watermarked preview and metrics when loading new video
            self.preview_watermarked.clear()
            self.preview_watermarked.setText("")
            self.wm_overlay.show_overlay()
            self.metrics_row_widget.setVisible(False)
            self._last_output_path = ""

            try:
                info = get_video_info(path)
                audio_str = "Yes" if info.get('has_audio') else "No"
                self.video_info_label.setText(
                    tr("video_info_fmt",
                       w=info['width'], h=info['height'],
                       fps=info['fps'], fc=info['frame_count'],
                       dur=info['duration'], audio=audio_str))
                self.video_info_label.setStyleSheet(
                    "color:#34c759;font-size:11px;font-weight:600;padding:0 4px;")
                frame = get_first_frame(path)
                if frame is not None:
                    pixmap = frame_to_pixmap(frame, 340, 200)
                    self.preview_original.setPixmap(pixmap)
            except Exception as e:
                self.video_info_label.setText(tr("error_reading_video", e=str(e)))
                self.video_info_label.setStyleSheet(
                    "color:#ff3b30;font-size:11px;padding:0 4px;")

    def _start_embed(self):
        if not self.input_video_path:
            QMessageBox.information(self, tr("not_ready"), tr("no_video_selected"))
            return
        if self._busy:
            return
        default_name = os.path.splitext(self.input_video_path)[0] + "_watermarked.mp4"
        output_path, _ = QFileDialog.getSaveFileName(
            self, tr("save_watermarked_video"), default_name,
            "MP4 (*.mp4);;AVI (*.avi);;MKV (*.mkv);;MOV (*.mov);;WebM (*.webm)")
        if not output_path:
            return
        self._last_output_path = output_path
        self.embed_requested.emit(
            self.input_video_path, output_path, self.author_edit.text())

    def set_progress(self, percent, message):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)

    def set_watermarked_preview(self, frame):
        if frame is not None:
            pixmap = frame_to_pixmap(frame, 340, 200)
            self.preview_watermarked.setPixmap(pixmap)

    def reset_status(self):
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def reset_tab(self):
        self.input_video_path = ""
        self._last_output_path = ""
        self.input_path_edit.clear()
        self.author_edit.clear()
        self.video_info_label.setText(tr("no_video_loaded"))
        self.video_info_label.setStyleSheet("color:#86868b;font-size:11px;padding:0 4px;")
        self.preview_original.clear()
        self.preview_watermarked.clear()
        self.orig_overlay.show_overlay()
        self.wm_overlay.show_overlay()
        self.metrics_row_widget.setVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.embed_btn.setEnabled(False)

    def set_enabled(self, enabled):
        self._busy = not enabled
        self.embed_btn.setEnabled(enabled and bool(self.input_video_path))
        self.settings_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
        self.progress_bar.setVisible(not enabled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for overlay, parent in [(self.orig_overlay, self.preview_original),
                                (self.wm_overlay, self.preview_watermarked)]:
            w = parent.width()
            overlay.setFixedWidth(min(w - 10, 140))
            overlay.move(5, 5)