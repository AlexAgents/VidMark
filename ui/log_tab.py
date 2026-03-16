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
Log Tab
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QApplication, QFileDialog
)
import qtawesome as qta
from datetime import datetime
from i18n import tr


class LogTab(QWidget):
    from PyQt5.QtCore import pyqtSignal
    clear_requested = pyqtSignal()
    status_message = pyqtSignal(str)  # For status bar feedback

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        btn_layout = QHBoxLayout()
        btn_style = (
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;border-radius:6px;"
            "padding:6px 14px;font-weight:500;}"
            "QPushButton:hover{background:#f0f0f5;}"
            "QPushButton:disabled{background:#f5f5f7;color:#aeaeb2;border-color:#e5e5ea;}")

        self.copy_btn = QPushButton(
            qta.icon('fa5s.copy', color='#007aff'), tr("copy_clipboard"))
        self.copy_btn.setStyleSheet(btn_style)
        self.copy_btn.clicked.connect(self._copy_log)
        self.copy_btn.setEnabled(False)
        btn_layout.addWidget(self.copy_btn)

        self.export_btn = QPushButton(
            qta.icon('fa5s.file-export', color='#ff9500'),
            tr("export_file"))
        self.export_btn.setStyleSheet(btn_style)
        self.export_btn.clicked.connect(self._export_log)
        self.export_btn.setEnabled(False)
        btn_layout.addWidget(self.export_btn)

        self.clear_btn = QPushButton(
            qta.icon('fa5s.trash', color='#ff3b30'), tr("clear"))
        self.clear_btn.setStyleSheet(btn_style)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.clear_btn.setEnabled(False)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "font-family:'SF Mono','Courier New',monospace;font-size:12px;"
            "background-color:#fafafa;color:#1d1d1f;"
            "border:1px solid #d2d2d7;border-radius:8px;"
            "padding:8px;")
        layout.addWidget(self.log_text)

    def retranslate_ui(self):
        self.copy_btn.setText(tr("copy_clipboard"))
        self.export_btn.setText(tr("export_file"))
        self.clear_btn.setText(tr("clear"))

    def _update_buttons(self):
        has_content = bool(self.log_text.toPlainText().strip())
        self.copy_btn.setEnabled(has_content)
        self.export_btn.setEnabled(has_content)
        self.clear_btn.setEnabled(has_content)

    def append_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Colorize special prefixes (simple and robust)
        if message.startswith("[ERROR]"):
            html = f"<span style='color:#ff3b30; font-weight:700;'>[{timestamp}] {message}</span>"
            self.log_text.append(html)
        elif message.startswith("[TIP]"):
            html = f"<span style='color:#34c759; font-weight:700;'>[{timestamp}] {message}</span>"
            self.log_text.append(html)
        else:
            self.log_text.append(f"[{timestamp}] {message}")

        self._update_buttons()

    def _copy_log(self):
        text = self.log_text.toPlainText()
        if not text.strip():
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.status_message.emit(tr("status_copied"))

    def _export_log(self):
        text = self.log_text.toPlainText()
        if not text.strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("export_log_title"), "watermark_log.txt",
            "Text Files (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.status_message.emit(tr("status_exported", path=path))

    def _on_clear_clicked(self):
        """Emit signal so main_window can show confirmation with 'don't show again'."""
        self.clear_requested.emit()

    def force_clear(self):
        """Clear log without confirmation (called after confirmation passes)."""
        self.log_text.clear()
        self._update_buttons()