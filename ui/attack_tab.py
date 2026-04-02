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
Attack Testing Tab
"""
import os
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QScrollArea, QLineEdit, QFileDialog,
    QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import qtawesome as qta
from core.attacks import AttackSimulator
from i18n import tr


class AttackTab(QWidget):
    test_requested = pyqtSignal(list, bool, str)
    reset_requested = pyqtSignal()
    status_message = pyqtSignal(str)  # For status bar feedback

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.is_ready = False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        btn_layout = QHBoxLayout()
        btn_style = (
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;border-radius:6px;"
            "padding:6px 12px;font-weight:500;}"
            "QPushButton:hover{background:#e8e8ed;}")

        self.select_all_btn = QPushButton(
            qta.icon('fa5s.check-double', color='#34c759'), tr("select_all"))
        self.select_all_btn.setStyleSheet(btn_style)
        self.select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton(
            qta.icon('fa5s.times', color='#ff3b30'), tr("deselect_all"))
        self.deselect_all_btn.setStyleSheet(btn_style)
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()

        # Reset button — fixed size matching Run Attack Tests button height
        self.reset_btn = QPushButton(
            qta.icon('fa5s.undo', color='#ff3b30'), tr("reset_attack_tab"))
        self.reset_btn.setFixedHeight(42)
        self.reset_btn.setMinimumWidth(100)
        self.reset_btn.setStyleSheet(
            "QPushButton{background:#ffffff;border:1px solid #d2d2d7;"
            "border-radius:6px;padding:5px 12px;color:#ff3b30;font-weight:600;font-size:12px;}"
            "QPushButton:hover{background:#ffe5e5;}")
        self.reset_btn.clicked.connect(self.reset_requested.emit)
        btn_layout.addWidget(self.reset_btn)

        self.test_btn = QPushButton(
            qta.icon('fa5s.flask', color='#ffffff'), tr("run_attack_tests"))
        self.test_btn.setMinimumHeight(42)
        self.test_btn.setStyleSheet(
            "QPushButton{background:#ff9500;color:white;font-size:14px;font-weight:700;"
            "border-radius:8px;border:none;padding:6px 18px;}"
            "QPushButton:hover{background:#e68600;}"
            "QPushButton:disabled{background:#e5e5ea;color:#aeaeb2;}")
        self.test_btn.clicked.connect(self._start_test)
        self.test_btn.setEnabled(False)
        btn_layout.addWidget(self.test_btn)
        layout.addLayout(btn_layout)

        # Save options
        self.save_group = QGroupBox()
        self.save_group.setStyleSheet(
            "QGroupBox{border:none;background:transparent;padding:0;margin:0;}")
        save_layout = QVBoxLayout(self.save_group)
        save_layout.setContentsMargins(0, 0, 0, 0)
        save_layout.setSpacing(4)

        self.save_checkbox = QCheckBox(tr("save_extraction_results"))
        self.save_checkbox.setChecked(False)
        self.save_checkbox.toggled.connect(self._toggle_save_options)
        save_layout.addWidget(self.save_checkbox)

        self.save_options_widget = QWidget()
        so_layout = QHBoxLayout(self.save_options_widget)
        so_layout.setContentsMargins(24, 0, 0, 0)

        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText(tr("select_save_folder"))
        self.save_path_edit.setReadOnly(True)
        so_layout.addWidget(self.save_path_edit, 1)

        self.save_browse_btn = QPushButton(
            qta.icon('fa5s.folder-open', color='#ffffff'), tr("browse_folder"))
        self.save_browse_btn.setMinimumHeight(30)
        self.save_browse_btn.setStyleSheet(
            "QPushButton{background:#007aff;color:white;border:none;border-radius:6px;"
            "padding:5px 10px;font-weight:500;}"
            "QPushButton:hover{background:#0051d5;}")
        self.save_browse_btn.clicked.connect(self._browse_save_folder)
        so_layout.addWidget(self.save_browse_btn)

        self.save_options_widget.setVisible(False)
        save_layout.addWidget(self.save_options_widget)
        layout.addWidget(self.save_group)

        # Attack selection
        self.attacks_group = QGroupBox(tr("select_attacks"))
        ag_layout = QVBoxLayout(self.attacks_group)
        ag_layout.setContentsMargins(6, 14, 6, 6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        all_attacks = AttackSimulator.get_all_attacks()
        self.attack_checkboxes = {}
        self._category_labels = {}
        self._categories = {
            "cat_no_attack": ["No Attack"],
            "cat_compression": ["JPEG", "H.264", "H.265"],
            "cat_noise": ["Gaussian Noise", "Salt"],
            "cat_filtering": ["Median", "Gaussian Blur"],
            "cat_geometric": ["Rotation", "Scale", "Crop"],
            "cat_color": ["Brightness", "Contrast", "Histogram"],
        }


        for cat_key, keywords in self._categories.items():
            matching = [a for a in all_attacks if any(kw in a for kw in keywords)]
            if not matching:
                continue
            cat_label = QLabel(f" {tr(cat_key)}")
            cat_label.setStyleSheet(
                "color:#007aff;font-weight:700;font-size:12px;padding:4px 0 2px 0;")
            self._category_labels[cat_key] = cat_label
            scroll_layout.addWidget(cat_label)
            for attack_name in matching:
                cb = QCheckBox(attack_name)
                cb.setChecked(True)
                cb.setStyleSheet("QCheckBox{padding:2px 0;}")
                self.attack_checkboxes[attack_name] = cb
                scroll_layout.addWidget(cb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        ag_layout.addWidget(scroll)
        layout.addWidget(self.attacks_group)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(18)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.results_group = QGroupBox(tr("results"))
        results_layout = QVBoxLayout(self.results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        headers = [tr("attack"), "NC", "BER", tr("attack_psnr"), tr("status")]
        self.results_table.setHorizontalHeaderLabels(headers)
        hdr = self.results_table.horizontalHeader()
        hdr.setStretchLastSection(True)
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)
        hdr.setVisible(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.results_table)

        self.save_results_btn = QPushButton(
            qta.icon('fa5s.save', color='#007aff'), tr("save_attack_results"))
        self.save_results_btn.setStyleSheet(btn_style)
        self.save_results_btn.clicked.connect(self._save_results)
        results_layout.addWidget(self.save_results_btn)

        layout.addWidget(self.results_group, stretch=2)

    def retranslate_ui(self):
        self.select_all_btn.setText(tr("select_all"))
        self.deselect_all_btn.setText(tr("deselect_all"))
        self.test_btn.setText(tr("run_attack_tests"))
        self.save_checkbox.setText(tr("save_extraction_results"))
        self.save_path_edit.setPlaceholderText(tr("select_save_folder"))
        self.save_browse_btn.setText(tr("browse_folder"))
        self.attacks_group.setTitle(tr("select_attacks"))
        self.results_group.setTitle(tr("results"))
        self.results_table.setHorizontalHeaderLabels([
            tr("attack"), "NC", "BER", tr("attack_psnr"), tr("status")])
        self.save_results_btn.setText(tr("save_attack_results"))
        self.reset_btn.setText(tr("reset_attack_tab"))
        # Update category labels
        for cat_key, label in self._category_labels.items():
            label.setText(f" {tr(cat_key)}")

    def _save_results(self):
        if self.results_table.rowCount() == 0:
            QMessageBox.information(self, tr("not_ready"), tr("no_results_to_save"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_results_title"), "attack_results.csv",
            "CSV (*.csv);;Text (*.txt)")
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            headers = []
            for col in range(self.results_table.columnCount()):
                item = self.results_table.horizontalHeaderItem(col)
                headers.append(item.text() if item else f"Col{col}")
            writer.writerow(headers)
            for row in range(self.results_table.rowCount()):
                row_data = []
                for col in range(self.results_table.columnCount()):
                    item = self.results_table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)
        self.status_message.emit(tr("status_attacks_saved", path=path))

    def _toggle_save_options(self, checked):
        self.save_options_widget.setVisible(checked)

    def _browse_save_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, tr("select_folder_title"), "")
        if folder:
            self.save_path_edit.setText(folder)
            self.status_message.emit(tr("status_folder_selected", path=folder))

    def _select_all(self):
        for cb in self.attack_checkboxes.values():
            cb.setChecked(True)
        self.status_message.emit(tr("status_all_selected"))

    def _deselect_all(self):
        for cb in self.attack_checkboxes.values():
            cb.setChecked(False)
        self.status_message.emit(tr("status_all_deselected"))

    def _start_test(self):
        selected = [name for name, cb in self.attack_checkboxes.items() if cb.isChecked()]
        if not selected:
            QMessageBox.information(self, tr("not_ready"), tr("no_attacks_selected"))
            return
        if not self.is_ready:
            QMessageBox.information(self, tr("not_ready"), tr("embed_first"))
            return
        if self.save_checkbox.isChecked() and not self.save_path_edit.text():
            QMessageBox.information(self, tr("not_ready"), tr("no_save_folder"))
            return
        self.results_table.setRowCount(0)
        save = self.save_checkbox.isChecked()
        spath = self.save_path_edit.text() if save else ""
        self.test_requested.emit(selected, save, spath)

    def set_ready(self, ready):
        self.is_ready = ready
        self.test_btn.setEnabled(ready)

    def set_progress(self, percent, message):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)

    def reset_status(self):
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def reset_tab(self):
        self.results_table.setRowCount(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

    def add_result(self, attack, nc, ber, psnr, status):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(attack))
        self.results_table.setItem(row, 1, QTableWidgetItem(f"{nc:.4f}"))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{ber:.4f}"))
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{psnr:.2f}"))
        self.results_table.setItem(row, 4, QTableWidgetItem(status))
        if nc >= 0.85:
            color = QColor(52, 199, 89, 40)
        elif nc >= 0.70:
            color = QColor(255, 149, 0, 40)
        else:
            color = QColor(255, 59, 48, 40)
        for col in range(5):
            item = self.results_table.item(row, col)
            if item:
                item.setBackground(color)

    def set_enabled(self, enabled):
        self.test_btn.setEnabled(enabled and self.is_ready)