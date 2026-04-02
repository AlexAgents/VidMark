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
Extract Tab
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFileDialog, QProgressBar, QTabWidget,
    QScrollArea, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import qtawesome as qta
import numpy as np

from config import VIDEO_FILTER
from i18n import tr


class ExtractTab(QWidget):
    extract_requested = pyqtSignal(str, str)
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = ""
        self.keyfile_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        self.sub_tabs = QTabWidget()

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_inner = QWidget()
        main_layout = QVBoxLayout(main_inner)
        main_layout.setSpacing(8)

        # Video group
        self.vg = QGroupBox(tr("watermarked_video"))
        vl = QHBoxLayout(self.vg)
        vl.setContentsMargins(10, 14, 10, 10)
        self.video_edit = QLineEdit()
        self.video_edit.setPlaceholderText(tr("select_watermarked_video"))
        self.video_edit.setReadOnly(True)
        self.vb = QPushButton(
            qta.icon('fa5s.film', color='#ffffff'), tr("browse"))
        self.vb.setMinimumHeight(34)
        self.vb.setStyleSheet(
            "QPushButton{background:#007aff;color:white;border:none;border-radius:6px;"
            "padding:6px 14px;font-weight:600;}"
            "QPushButton:hover{background:#0051d5;}")
        self.vb.clicked.connect(self._browse_video)
        vl.addWidget(self.video_edit, 3)
        vl.addWidget(self.vb)
        main_layout.addWidget(self.vg)

        # Key group
        self.kg = QGroupBox(tr("key_file"))
        kl = QHBoxLayout(self.kg)
        kl.setContentsMargins(10, 14, 10, 10)
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(tr("select_key_file"))
        self.key_edit.setReadOnly(True)
        self.kb = QPushButton(
            qta.icon('fa5s.key', color='#ffffff'), tr("browse"))
        self.kb.setMinimumHeight(34)
        self.kb.setStyleSheet(
            "QPushButton{background:#ff9500;color:white;border:none;border-radius:6px;"
            "padding:6px 14px;font-weight:600;}"
            "QPushButton:hover{background:#e68600;}")
        self.kb.clicked.connect(self._browse_key)
        kl.addWidget(self.key_edit, 3)
        kl.addWidget(self.kb)
        main_layout.addWidget(self.kg)

        # Extract button + Reset button in same row
        extract_row = QHBoxLayout()
        self.extract_btn = QPushButton(
            qta.icon('fa5s.search', color='#ffffff'), tr("extract_verify"))
        self.extract_btn.setMinimumHeight(46)
        self.extract_btn.setStyleSheet(
            "QPushButton{background:#007aff;color:white;"
            "font-size:16px;font-weight:700;border-radius:8px;border:none;}"
            "QPushButton:hover{background:#0051d5;}"
            "QPushButton:disabled{background:#e5e5ea;color:#aeaeb2;}")
        self.extract_btn.clicked.connect(self._start)
        self.extract_btn.setEnabled(False)
        extract_row.addWidget(self.extract_btn, 1)

        self.reset_btn = QPushButton(
            qta.icon('fa5s.undo', color='#ff3b30'), tr("reset_extract_tab"))
        self.reset_btn.setFixedHeight(46)
        self.reset_btn.setMinimumWidth(100)
        self.reset_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;"
            "border-radius:8px;padding:5px 12px;color:#ff3b30;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#ffe5e5;}")
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        extract_row.addWidget(self.reset_btn, 0)
        main_layout.addLayout(extract_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setMinimumHeight(18)
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)

        # Results
        self.rg = QGroupBox(tr("verification_results"))
        rl = QVBoxLayout(self.rg)
        rl.setContentsMargins(10, 14, 10, 10)

        self.result_status = QLabel(tr("no_extraction"))
        self.result_status.setStyleSheet(
            "font-size:16px;padding:10px;color:#86868b;"
            "border:1px solid #d2d2d7;border-radius:8px;background:#f9f9fb;")
        self.result_status.setAlignment(Qt.AlignCenter)
        rl.addWidget(self.result_status)

        det = QHBoxLayout()
        det.setSpacing(15)
        info = QVBoxLayout()
        info.setSpacing(4)

        self._default_lbl_style = "font-family:monospace;font-size:13px;color:#1d1d1f;"
        lbl_style = self._default_lbl_style
        lbl_dim = "font-family:monospace;font-size:13px;color:#86868b;"

        self.author_label = QLabel(f"{tr('author')}: —")
        self.author_label.setStyleSheet("font-size:15px;font-weight:700;color:#007aff;")
        info.addWidget(self.author_label)

        self.uuid_label = QLabel(f"{tr('uuid_video')} —")
        self.uuid_label.setStyleSheet(lbl_style)
        info.addWidget(self.uuid_label)

        self.uuid_json_label = QLabel(f"{tr('uuid_key')} —")
        self.uuid_json_label.setStyleSheet(lbl_dim)
        info.addWidget(self.uuid_json_label)

        self.uuid_match_label = QLabel(f"{tr('uuid_match')} —")
        self.uuid_match_label.setStyleSheet(lbl_style)
        info.addWidget(self.uuid_match_label)

        self.ts_label = QLabel(f"{tr('time_video')} —")
        self.ts_label.setStyleSheet(lbl_style)
        info.addWidget(self.ts_label)

        self.ts_json_label = QLabel(f"{tr('time_key')} —")
        self.ts_json_label.setStyleSheet(lbl_dim)
        info.addWidget(self.ts_json_label)

        self.ts_match_label = QLabel(f"{tr('time_match')} —")
        self.ts_match_label.setStyleSheet(lbl_style)
        info.addWidget(self.ts_match_label)

        self.crc_label = QLabel(f"{tr('crc')} —")
        self.crc_label.setStyleSheet(lbl_style)
        info.addWidget(self.crc_label)

        self.ecc_label = QLabel(f"{tr('ecc')} —")
        self.ecc_label.setStyleSheet(lbl_style)
        info.addWidget(self.ecc_label)

        self.conf_label = QLabel(f"{tr('confidence')} —")
        self.conf_label.setStyleSheet(lbl_style)
        info.addWidget(self.conf_label)

        self.sync_label = QLabel(f"{tr('sync')} —")
        self.sync_label.setStyleSheet(lbl_style)
        info.addWidget(self.sync_label)

        info.addStretch()
        det.addLayout(info, 3)

        # Data visualization
        data_container = QVBoxLayout()
        data_container.setSpacing(0)
        data_frame = QFrame()
        data_frame.setFixedSize(190, 210)
        data_frame.setStyleSheet(
            "QFrame{background:#f9f9fb;border:2px solid #d2d2d7;border-radius:10px;}")
        data_inner = QVBoxLayout(data_frame)
        data_inner.setContentsMargins(10, 8, 10, 8)
        data_inner.setSpacing(6)

        self.data_title = QLabel(tr("extracted_data"))
        self.data_title.setAlignment(Qt.AlignCenter)
        self.data_title.setStyleSheet(
            "color:#86868b;font-size:11px;font-weight:600;border:none;")
        data_inner.addWidget(self.data_title)

        self.data_label = QLabel(tr("no_data"))
        self.data_label.setAlignment(Qt.AlignCenter)
        self.data_label.setFixedSize(160, 160)
        self.data_label.setStyleSheet(
            "border:1px dashed #d2d2d7;border-radius:5px;"
            "background:#ffffff;color:#aeaeb2;font-size:12px;")
        data_inner.addWidget(self.data_label, 0, Qt.AlignCenter)

        data_container.addWidget(data_frame, 0, Qt.AlignTop)
        data_container.addStretch()
        det.addLayout(data_container)
        rl.addLayout(det)
        main_layout.addWidget(self.rg)

        main_scroll.setWidget(main_inner)
        main_c = QWidget()
        mc_l = QVBoxLayout(main_c)
        mc_l.setContentsMargins(0, 0, 0, 0)
        mc_l.addWidget(main_scroll)
        self.sub_tabs.addTab(main_c,
                             qta.icon('fa5s.search', color='#007aff'), tr("extraction"))

        # Instructions
        instr_widget = QWidget()
        instr_layout = QVBoxLayout(instr_widget)
        instr_scroll = QScrollArea()
        instr_scroll.setWidgetResizable(True)
        instr_content = QWidget()
        icl = QVBoxLayout(instr_content)
        self.instr_label = QLabel(tr("extract_instructions_html"))
        self.instr_label.setWordWrap(True)
        self.instr_label.setStyleSheet("font-size:12px;padding:10px;")
        self.instr_label.setAlignment(Qt.AlignTop)
        self.instr_label.setTextFormat(Qt.RichText)
        icl.addWidget(self.instr_label)
        icl.addStretch()
        instr_scroll.setWidget(instr_content)
        instr_layout.addWidget(instr_scroll)
        self.sub_tabs.addTab(instr_widget,
                             qta.icon('fa5s.info-circle', color='#ff9500'), tr("instructions"))

        layout.addWidget(self.sub_tabs)

    def retranslate_ui(self):
        self.vg.setTitle(tr("watermarked_video"))
        self.video_edit.setPlaceholderText(tr("select_watermarked_video"))
        self.vb.setText(tr("browse"))
        self.kg.setTitle(tr("key_file"))
        self.key_edit.setPlaceholderText(tr("select_key_file"))
        self.kb.setText(tr("browse"))
        self.extract_btn.setText(tr("extract_verify"))
        self.rg.setTitle(tr("verification_results"))
        self.result_status.setText(tr("no_extraction"))
        self.data_title.setText(tr("extracted_data"))
        if not self.data_label.pixmap():
            self.data_label.setText(tr("no_data"))
        self.sub_tabs.setTabText(0, tr("extraction"))
        self.sub_tabs.setTabText(1, tr("instructions"))
        self.instr_label.setText(tr("extract_instructions_html"))
        self.reset_btn.setText(tr("reset_extract_tab"))

    def _browse_video(self):
        p, _ = QFileDialog.getOpenFileName(
            self, tr("select_video_title"), "", VIDEO_FILTER)
        if p:
            self.video_path = p
            self.video_edit.setText(p)
            self._check()

    def _browse_key(self):
        p, _ = QFileDialog.getOpenFileName(
            self, tr("select_key_title"), "", "JSON (*.json)")
        if p:
            self.keyfile_path = p
            self.key_edit.setText(p)
            self._check()

    def _check(self):
        self.extract_btn.setEnabled(
            bool(self.video_path) and bool(self.keyfile_path))

    def _start(self):
        if not self.video_path:
            QMessageBox.information(self, tr("not_ready"), tr("no_video_selected"))
            return
        if not self.keyfile_path:
            QMessageBox.information(self, tr("not_ready"), tr("no_key_selected"))
            return
        self.extract_requested.emit(self.video_path, self.keyfile_path)

    def set_progress(self, p, m):
        self.progress.setVisible(True)
        self.progress.setValue(p)

    def display_results(self, r):
        self.progress.setVisible(False)

        status = r.get("status", "UNKNOWN")
        pi = r.get("payload_info", {})
        ja = r.get("json_author", "")
        ju = r.get("json_uuid", "")
        um = r.get("uuid_match", False)
        tm = r.get("ts_match", False)
        jts = r.get("json_ts_str", "N/A")

        status_map = {
            "VERIFIED": ("#34c759", "#e8f8ee", tr("status_verified")),
            "TIMESTAMP_MISMATCH": ("#ff9500", "#fff5e6", tr("status_ts_mismatch")),
            "MISMATCH": ("#ff9500", "#fff5e6", tr("status_uuid_mismatch")),
            "DAMAGED": ("#ff9500", "#fff5e6", tr("status_damaged")),
            "NOT_FOUND": ("#ff3b30", "#ffe5e5", tr("status_not_found")),
        }
        c, bg, text = status_map.get(
            status, ("#ff3b30", "#ffe5e5", tr("status_not_found")))
        self.result_status.setText(text)
        self.result_status.setStyleSheet(
            f"font-size:16px;color:{c};padding:12px;"
            f"border:2px solid {c};border-radius:8px;"
            f"background:{bg};font-weight:700;")

        self.author_label.setText(
            f"{tr('author')}: {ja}" if ja else f" {tr('author')}: {tr('auto_uuid')}")

        eu = pi.get('uuid_hex', 'N/A')
        self.uuid_label.setText(f"{tr('uuid_video')} {eu}")
        self.uuid_json_label.setText(f"{tr('uuid_key')} {ju or 'N/A'}")

        if um:
            self.uuid_match_label.setText(f"{tr('uuid_match')} {tr('yes')}")
            self.uuid_match_label.setStyleSheet(
                "font-family:monospace;font-size:14px;color:#34c759;font-weight:700;")
        else:
            self.uuid_match_label.setText(f"{tr('uuid_match')} {tr('no')}")
            self.uuid_match_label.setStyleSheet(
                "font-family:monospace;font-size:14px;color:#ff3b30;font-weight:700;")

        ets = pi.get('timestamp_str', 'N/A')
        self.ts_label.setText(f"{tr('time_video')} {ets}")
        self.ts_json_label.setText(f"{tr('time_key')} {jts}")

        if tm:
            self.ts_match_label.setText(f"{tr('time_match')} {tr('yes')}")
            self.ts_match_label.setStyleSheet("font-family:monospace;font-size:13px;color:#34c759;")
        else:
            self.ts_match_label.setText(f"{tr('time_match')} {tr('no_key_modified')}")
            self.ts_match_label.setStyleSheet(
                "font-family:monospace;font-size:13px;color:#ff3b30;font-weight:700;")

        crc_ok = r.get("crc_valid", False)
        crc_icon = "<span style='color:#34c759;font-weight:bold;'>✔</span>" if crc_ok else "<span style='color:#ff3b30;font-weight:bold;'>✗</span>"
        self.crc_label.setText(f"{tr('crc')} {crc_icon}")
        self.crc_label.setTextFormat(Qt.RichText)
        self.crc_label.setStyleSheet(
            f"font-family:monospace;font-size:13px;color:{'#34c759' if crc_ok else '#ff3b30'};")

        ecc_ok = r.get("ecc_success", False)
        ecc_t = tr('ecc_ok') if ecc_ok else tr('ecc_failed')
        ecc_icon = "<span style='color:#34c759;font-weight:bold;'>✔</span>" if ecc_ok else "<span style='color:#ff3b30;font-weight:bold;'>✗</span>"
        self.ecc_label.setText(f"{tr('ecc')} {ecc_icon} {ecc_t}")
        self.ecc_label.setTextFormat(Qt.RichText)
        self.ecc_label.setStyleSheet(
            f"font-family:monospace;font-size:13px;color:{'#34c759' if ecc_ok else '#ff3b30'};")

        conf = r.get("confidence", 0)
        cc = "#34c759" if conf > 0.8 else "#ff9500" if conf > 0.5 else "#ff3b30"
        self.conf_label.setText(f"{tr('confidence')} {conf:.4f}")
        self.conf_label.setStyleSheet(f"font-family:monospace;font-size:13px;color:{cc};")

        sync = pi.get("sync_valid", False)
        sync_icon = "<span style='color:#34c759;font-weight:bold;'>✔</span>" if sync else "<span style='color:#ff3b30;font-weight:bold;'>✗</span>"
        self.sync_label.setText(f"{tr('sync')} {sync_icon}")
        self.sync_label.setTextFormat(Qt.RichText)

        data_vis = r.get("data_visual")
        if data_vis is not None:
            d = np.ascontiguousarray(data_vis.astype(np.uint8))
            h_img, w_img = d.shape[:2]
            qi = QImage(d.data, w_img, h_img, w_img, QImage.Format_Grayscale8).copy()
            pm = QPixmap.fromImage(qi).scaled(
                150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.data_label.setPixmap(pm)
            self.data_label.setText("")
            self.data_label.setStyleSheet(
                "border:2px solid #34c759;border-radius:5px;background:#ffffff;")
        else:
            self.data_label.setText(tr("no_data"))
            self.data_label.setStyleSheet(
                "border:1px dashed #d2d2d7;border-radius:5px;"
                "background:#ffffff;color:#aeaeb2;font-size:12px;")

    def reset_tab(self):
        """Reset all fields in extract tab."""
        self.video_path = ""
        self.keyfile_path = ""
        self.video_edit.clear()
        self.key_edit.clear()
        self.result_status.setText(tr("no_extraction"))
        self.result_status.setStyleSheet(
            "font-size:16px;padding:10px;color:#86868b;"
            "border:1px solid #d2d2d7;border-radius:8px;background:#f9f9fb;")
        self.extract_btn.setEnabled(False)
        self.progress.setVisible(False)
        self.data_label.clear()
        self.data_label.setText(tr("no_data"))
        self.data_label.setStyleSheet(
            "border:1px dashed #d2d2d7;border-radius:5px;"
            "background:#ffffff;color:#aeaeb2;font-size:12px;")

        # Reset all info labels to default style and text
        default_style = self._default_lbl_style
        dim_style = "font-family:monospace;font-size:13px;color:#86868b;"

        self.author_label.setText(f"{tr('author')}: —")
        self.author_label.setStyleSheet("font-size:15px;font-weight:700;color:#007aff;")

        self.uuid_label.setText(f"{tr('uuid_video')} —")
        self.uuid_label.setStyleSheet(default_style)

        self.uuid_json_label.setText(f"{tr('uuid_key')} —")
        self.uuid_json_label.setStyleSheet(dim_style)

        self.uuid_match_label.setText(f"{tr('uuid_match')} —")
        self.uuid_match_label.setStyleSheet(default_style)

        self.ts_label.setText(f"{tr('time_video')} —")
        self.ts_label.setStyleSheet(default_style)

        self.ts_json_label.setText(f"{tr('time_key')} —")
        self.ts_json_label.setStyleSheet(dim_style)

        self.ts_match_label.setText(f"{tr('time_match')} —")
        self.ts_match_label.setStyleSheet(default_style)

        self.crc_label.setText(f"{tr('crc')} —")
        self.crc_label.setStyleSheet(default_style)
        self.crc_label.setTextFormat(Qt.PlainText)

        self.ecc_label.setText(f"{tr('ecc')} —")
        self.ecc_label.setStyleSheet(default_style)
        self.ecc_label.setTextFormat(Qt.PlainText)

        self.conf_label.setText(f"{tr('confidence')} —")
        self.conf_label.setStyleSheet(default_style)

        self.sync_label.setText(f"{tr('sync')} —")
        self.sync_label.setStyleSheet(default_style)
        self.sync_label.setTextFormat(Qt.PlainText)

    def set_enabled(self, e):
        self.extract_btn.setEnabled(e and bool(self.video_path) and bool(self.keyfile_path))