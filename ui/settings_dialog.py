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
Settings Dialog
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
    QDialogButtonBox, QTabWidget, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt
from config import (
    WatermarkSettings, WAVELET_COMPATIBILITY,
    MIN_EXTRACT_FRAMES, MAX_EXTRACT_FRAMES,
    SETTINGS_PRESETS, StrengthPreset
)
from i18n import tr, get_language


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self._updating = False
        # Title without icon emoji
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(700)
        self.setMinimumHeight(560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._build()
        self._load_from_settings()
        self._update_compat()
        self._update_strength_visibility()
        self._update_quality_visibility()

    def _build(self):
        L = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { min-width: 120px; padding: 8px 24px; font-size: 12px; }")

        params_scroll = QScrollArea()
        params_scroll.setWidgetResizable(True)
        params_inner = QWidget()
        params_inner.setStyleSheet("QLabel { font-size: 12px; } QGroupBox { font-size: 12px; }")
        params_layout = QVBoxLayout(params_inner)

        # Preset
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel(tr("preset")))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(tr("custom"), "custom")
        for key, preset in SETTINGS_PRESETS.items():
            lang = get_language()
            name = preset.get(f"name_{lang}", preset.get("name_en", key))
            self.preset_combo.addItem(name, key)
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        preset_layout.addWidget(self.preset_combo, stretch=2)
        params_layout.addLayout(preset_layout)

        # Strength
        strength_group = QGroupBox(tr("embedding_strength"))
        strength_layout = QVBoxLayout(strength_group)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(tr("mode")))
        self.strength_combo = QComboBox()
        self.strength_combo.addItem(tr("invisible_desc"), StrengthPreset.INVISIBLE.value)
        self.strength_combo.addItem(tr("balanced_desc"), StrengthPreset.BALANCED.value)
        self.strength_combo.addItem(tr("robust_desc"), StrengthPreset.ROBUST.value)
        self.strength_combo.addItem(tr("custom_delta"), StrengthPreset.CUSTOM.value)
        self.strength_combo.currentIndexChanged.connect(self._on_strength_changed)
        mode_layout.addWidget(self.strength_combo, stretch=2)
        strength_layout.addLayout(mode_layout)

        self.delta_layout = QHBoxLayout()
        self.delta_label = QLabel(tr("delta_value"))
        self.delta_spin = QDoubleSpinBox()
        self.delta_spin.setRange(10.0, 500.0)
        self.delta_spin.setSingleStep(5.0)
        self.delta_spin.setDecimals(1)
        self.delta_spin.valueChanged.connect(self._on_param_changed)
        self.delta_layout.addWidget(self.delta_label)
        self.delta_layout.addWidget(self.delta_spin)
        strength_layout.addLayout(self.delta_layout)
        params_layout.addWidget(strength_group)

        # Quality
        quality_group = QGroupBox(tr("output_quality"))
        quality_layout = QVBoxLayout(quality_group)
        quality_mode_layout = QHBoxLayout()
        quality_mode_layout.addWidget(QLabel(tr("quality")))
        self.quality_combo = QComboBox()
        self.quality_combo.addItem(tr("lossless_crf0"), "lossless")
        self.quality_combo.addItem(tr("high_crf4"), "high")
        self.quality_combo.addItem(tr("standard_crf18"), "standard")
        self.quality_combo.addItem(tr("custom_crf"), "custom")
        self.quality_combo.currentIndexChanged.connect(self._on_quality_changed)
        quality_mode_layout.addWidget(self.quality_combo, stretch=2)
        quality_layout.addLayout(quality_mode_layout)

        self.crf_layout = QHBoxLayout()
        self.crf_label = QLabel(tr("crf_value"))
        self.crf_spin = QSpinBox()
        self.crf_spin.setRange(0, 51)
        self.crf_spin.valueChanged.connect(self._on_param_changed)
        self.crf_layout.addWidget(self.crf_label)
        self.crf_layout.addWidget(self.crf_spin)
        quality_layout.addLayout(self.crf_layout)

        self.crf_hint = QLabel(tr("crf_hint"))
        self.crf_hint.setStyleSheet("color:#86868b;font-size:11px;font-style:italic;")
        self.crf_hint.setWordWrap(True)
        quality_layout.addWidget(self.crf_hint)
        params_layout.addWidget(quality_group)

        # Wavelet
        g1 = QGroupBox(tr("wavelet_transform"))
        l1 = QVBoxLayout(g1)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel(tr("wavelet")))
        self.wc = QComboBox()
        self.wc.addItems(["haar", "db2", "db4", "db6", "bior4.4", "coif2"])
        self.wc.currentTextChanged.connect(self._on_param_changed)
        r1.addWidget(self.wc)
        l1.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel(tr("level")))
        self.lv = QSpinBox()
        self.lv.setRange(1, 3)
        self.lv.valueChanged.connect(self._on_param_changed)
        r2.addWidget(self.lv)
        l1.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel(tr("block")))
        self.bs = QComboBox()
        self.bs.addItems(["4", "8", "16"])
        self.bs.currentTextChanged.connect(self._on_param_changed)
        r3.addWidget(self.bs)
        l1.addLayout(r3)

        self.compat_label = QLabel("")
        self.compat_label.setWordWrap(True)
        self.compat_label.setTextFormat(Qt.RichText)
        self.compat_label.setStyleSheet("padding:8px;border-radius:6px;font-size:12px;")
        l1.addWidget(self.compat_label)
        params_layout.addWidget(g1)

        # Security
        g2 = QGroupBox(tr("security"))
        l2 = QVBoxLayout(g2)
        r4 = QHBoxLayout()
        r4.addWidget(QLabel(tr("key")))
        self.ke = QComboBox()
        self.ke.setEditable(True)
        self.ke.lineEdit().textEdited.connect(self._on_param_changed)
        r4.addWidget(self.ke)
        l2.addLayout(r4)
        params_layout.addWidget(g2)

        # ECC
        g3 = QGroupBox(tr("error_correction"))
        l3 = QVBoxLayout(g3)
        r6 = QHBoxLayout()
        r6.addWidget(QLabel(tr("rs_symbols")))
        self.rs = QSpinBox()
        self.rs.setRange(8, 64)
        self.rs.setSingleStep(4)
        self.rs.valueChanged.connect(self._on_param_changed)
        r6.addWidget(self.rs)
        l3.addLayout(r6)
        params_layout.addWidget(g3)

        # Extraction
        g4 = QGroupBox(tr("extraction"))
        l4 = QVBoxLayout(g4)
        r7 = QHBoxLayout()
        r7.addWidget(QLabel(tr("frames")))
        self.ef = QSpinBox()
        self.ef.setRange(MIN_EXTRACT_FRAMES, MAX_EXTRACT_FRAMES)
        self.ef.valueChanged.connect(self._on_param_changed)
        r7.addWidget(self.ef)
        l4.addLayout(r7)
        params_layout.addWidget(g4)

        params_layout.addStretch()
        params_scroll.setWidget(params_inner)

        pw = QWidget()
        pw_layout = QVBoxLayout(pw)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.addWidget(params_scroll)
        self.tabs.addTab(pw, tr("settings_tab_params"))

        # Instructions tab
        instr_widget = QWidget()
        instr_layout = QVBoxLayout(instr_widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        instr_label = QLabel(tr("settings_instructions_html"))
        instr_label.setWordWrap(True)
        instr_label.setStyleSheet("font-size:12px;padding:8px;")
        instr_label.setAlignment(Qt.AlignTop)
        instr_label.setTextFormat(Qt.RichText)
        scroll_layout.addWidget(instr_label)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        instr_layout.addWidget(scroll)
        self.tabs.addTab(instr_widget, tr("settings_tab_instructions"))

        L.addWidget(self.tabs)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.setCenterButtons(True)
        # Translate Cancel button
        cancel_btn = bb.button(QDialogButtonBox.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        L.addWidget(bb)

    def _set_widget_values_safely(self, fn):
        self._updating = True
        widgets = [self.preset_combo, self.strength_combo, self.delta_spin,
                   self.quality_combo, self.crf_spin,
                   self.wc, self.lv, self.bs, self.rs, self.ef]
        for w in widgets:
            w.blockSignals(True)
        try:
            fn()
        finally:
            for w in widgets:
                w.blockSignals(False)
            self._updating = False

    def _load_from_settings(self):
        def _load():
            self.wc.setCurrentText(self.settings.wavelet)
            self.lv.setValue(self.settings.dwt_level)
            self.bs.setCurrentText(str(self.settings.block_size))
            for i in range(self.strength_combo.count()):
                if self.strength_combo.itemData(i) == self.settings.strength_preset.value:
                    self.strength_combo.setCurrentIndex(i)
                    break
            self.delta_spin.setValue(self.settings.custom_delta)
            for i in range(self.quality_combo.count()):
                if self.quality_combo.itemData(i) == self.settings.output_quality:
                    self.quality_combo.setCurrentIndex(i)
                    break
            self.crf_spin.setValue(self.settings.custom_crf)
            self.ke.setEditText(str(self.settings.scramble_seed))
            self.rs.setValue(self.settings.rs_nsym)
            self.ef.setValue(self.settings.extract_frames)
            self.preset_combo.setCurrentIndex(0)
        self._set_widget_values_safely(_load)

    def _on_param_changed(self, _=None):
        if self._updating:
            return
        self._update_compat()
        self._set_custom_preset()

    def _set_custom_preset(self):
        if self._updating:
            return
        self._updating = True
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)
        self._updating = False

    def _on_strength_changed(self, _=None):
        if self._updating:
            return
        self._update_strength_visibility()
        self._on_param_changed()

    def _on_quality_changed(self, _=None):
        if self._updating:
            return
        self._update_quality_visibility()
        self._on_param_changed()

    def _update_strength_visibility(self):
        is_custom = (self.strength_combo.currentData() == StrengthPreset.CUSTOM.value)
        self.delta_label.setVisible(is_custom)
        self.delta_spin.setVisible(is_custom)

    def _update_quality_visibility(self):
        is_custom = (self.quality_combo.currentData() == "custom")
        self.crf_label.setVisible(is_custom)
        self.crf_spin.setVisible(is_custom)
        self.crf_hint.setVisible(is_custom)

    def _apply_preset(self, index):
        if self._updating:
            return
        key = self.preset_combo.currentData()
        if key == "custom" or key is None:
            return
        preset = SETTINGS_PRESETS.get(key)
        if not preset:
            return

        def _apply():
            self.wc.setCurrentText(preset.get("wavelet", "haar"))
            self.lv.setValue(preset.get("dwt_level", 1))
            self.bs.setCurrentText(str(preset.get("block_size", 8)))
            self.ke.setEditText(str(preset.get("scramble_seed", 42)))
            self.rs.setValue(preset.get("rs_nsym", 32))
            self.ef.setValue(preset.get("extract_frames", 15))
            sp = preset.get("strength_preset", "balanced")
            for i in range(self.strength_combo.count()):
                if self.strength_combo.itemData(i) == sp:
                    self.strength_combo.setCurrentIndex(i)
                    break
            self.delta_spin.setValue(preset.get("custom_delta", 35.0))
            oq = preset.get("output_quality", "standard")
            for i in range(self.quality_combo.count()):
                if self.quality_combo.itemData(i) == oq:
                    self.quality_combo.setCurrentIndex(i)
                    break
            self.crf_spin.setValue(preset.get("custom_crf", 18))
        self._set_widget_values_safely(_apply)
        self._update_strength_visibility()
        self._update_quality_visibility()
        self._update_compat()

    def _update_compat(self):
        wv = self.wc.currentText()
        lv = self.lv.value()
        wc = WAVELET_COMPATIBILITY.get(wv, {})
        levels = wc.get("levels", {})
        color = levels.get(lv, "poor")
        lang = get_language()
        note = wc.get(f"note_{lang}", wc.get("note_en", "Unknown"))
        min_delta = wc.get("recommended_delta_min", 35)

        color_map = {
            "excellent": ("#34c759", "#e8f8ee"),
            "doubtful": ("#ff9500", "#fff5e6"),
            "poor": ("#ff3b30", "#ffe5e5"),
        }
        fg, bg = color_map.get(color, color_map["poor"])
        if color == "excellent":
            status_text = tr("good_combination")
        elif color == "doubtful":
            status_text = tr("use_with_caution")
        else:
            status_text = tr("not_recommended_may_fail")

        self.compat_label.setText(
            f"<b>{wv} Level {lv}</b>: {note}<br>"
            f"{tr('min_recommended_delta')} {min_delta}<br>"
            f"{status_text}")
        self.compat_label.setStyleSheet(
            f"padding:8px;border-radius:6px;font-size:12px;"
            f"background:{bg};color:{fg};border:1px solid {fg};")

    def _ok(self):
        self.settings.wavelet = self.wc.currentText()
        self.settings.dwt_level = self.lv.value()
        self.settings.block_size = int(self.bs.currentText())
        sp_val = self.strength_combo.currentData()
        try:
            self.settings.strength_preset = StrengthPreset(sp_val)
        except ValueError:
            self.settings.strength_preset = StrengthPreset.BALANCED
        self.settings.custom_delta = self.delta_spin.value()
        self.settings.output_quality = self.quality_combo.currentData()
        self.settings.custom_crf = self.crf_spin.value()
        kt = self.ke.currentText().strip()
        try:
            self.settings.scramble_seed = int(kt)
        except ValueError:
            import hashlib
            self.settings.scramble_seed = int.from_bytes(
                hashlib.sha256(kt.encode()).digest()[:4], 'big')
        self.settings.rs_nsym = self.rs.value()
        self.settings.extract_frames = self.ef.value()
        self.accept()

    def get_settings(self):
        return self.settings