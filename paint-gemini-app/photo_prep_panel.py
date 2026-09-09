from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDockWidget, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

PRESETS = {
    "Passport 35 × 45 mm": (413, 531, 100),
    "Passport 2 × 2 inch": (600, 600, 200),
    "Application photo 200 × 230": (200, 230, 50),
    "Signature 140 × 60": (140, 60, 20),
    "Signature 200 × 80": (200, 80, 30),
    "Custom size": (413, 531, 100),
}


class Section(QFrame):
    def __init__(self, number: str, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("sectionCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        head = QHBoxLayout()
        badge = QLabel(number)
        badge.setObjectName("stepBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(25, 25)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        head.addWidget(badge)
        head.addWidget(title_label)
        head.addStretch(1)
        layout.addLayout(head)
        self.body = layout


class PhotoPrepPanel(QDockWidget):
    prepare_requested = pyqtSignal(int, int)
    crop_requested = pyqtSignal()
    white_bg_requested = pyqtSignal()
    export_requested = pyqtSignal(str, int, int, int)
    rotation_preview_requested = pyqtSignal(float)
    rotation_commit_requested = pyqtSignal()
    rotation_reset_requested = pyqtSignal()
    rotate90_requested = pyqtSignal(int)
    flip_requested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__("Photo controls", parent)
        self.setObjectName("PhotoPrepPanel")
        self.setMinimumWidth(340)
        self.setMaximumWidth(410)

        root = QWidget()
        root.setObjectName("panelRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("PHOTO PREP")
        title.setObjectName("panelTitle")
        subtitle = QLabel("Straighten, crop, clean background and export to an exact standard.")
        subtitle.setObjectName("panelSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        standard = Section("1", "Output standard")
        self.preset = QComboBox()
        self.preset.addItems(PRESETS.keys())
        self.preset.currentTextChanged.connect(self._apply_preset)
        standard.body.addWidget(self.preset)

        dims = QGridLayout()
        dims.setHorizontalSpacing(8)
        self.width_px = QSpinBox()
        self.width_px.setRange(20, 5000)
        self.height_px = QSpinBox()
        self.height_px.setRange(20, 5000)
        self.target_kb = QSpinBox()
        self.target_kb.setRange(5, 5000)
        self.target_kb.setSuffix(" KB")
        dims.addWidget(QLabel("Width (px)"), 0, 0)
        dims.addWidget(QLabel("Height (px)"), 0, 1)
        dims.addWidget(self.width_px, 1, 0)
        dims.addWidget(self.height_px, 1, 1)
        dims.addWidget(QLabel("Maximum file size"), 2, 0, 1, 2)
        dims.addWidget(self.target_kb, 3, 0, 1, 2)
        standard.body.addLayout(dims)
        layout.addWidget(standard)

        align = Section("2", "Straighten & crop")
        angle_row = QHBoxLayout()
        angle_row.addWidget(QLabel("Angle"))
        angle_row.addStretch(1)
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(-15.0, 15.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSingleStep(0.1)
        self.angle_spin.setSuffix("°")
        self.angle_spin.setFixedWidth(92)
        angle_row.addWidget(self.angle_spin)
        align.body.addLayout(angle_row)

        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-150, 150)
        self.angle_slider.setSingleStep(1)
        self.angle_slider.setPageStep(10)
        align.body.addWidget(self.angle_slider)
        fine = QHBoxLayout()
        fine.addWidget(QLabel("−15°"))
        fine.addStretch(1)
        zero_btn = QPushButton("0°")
        zero_btn.setObjectName("smallButton")
        zero_btn.clicked.connect(lambda: self._set_angle(0.0))
        fine.addWidget(zero_btn)
        fine.addStretch(1)
        fine.addWidget(QLabel("+15°"))
        align.body.addLayout(fine)

        self.angle_slider.valueChanged.connect(self._slider_changed)
        self.angle_spin.valueChanged.connect(self._spin_changed)

        rotation_actions = QHBoxLayout()
        apply_rotation = QPushButton("Apply angle")
        apply_rotation.setObjectName("secondaryButton")
        apply_rotation.clicked.connect(self.rotation_commit_requested)
        reset_rotation = QPushButton("Reset")
        reset_rotation.setObjectName("secondaryButton")
        reset_rotation.clicked.connect(self._reset_rotation)
        rotation_actions.addWidget(apply_rotation)
        rotation_actions.addWidget(reset_rotation)
        align.body.addLayout(rotation_actions)

        quarter = QHBoxLayout()
        left90 = QPushButton("↶ 90°")
        right90 = QPushButton("90° ↷")
        left90.setObjectName("smallButton")
        right90.setObjectName("smallButton")
        left90.clicked.connect(lambda: self.rotate90_requested.emit(-90))
        right90.clicked.connect(lambda: self.rotate90_requested.emit(90))
        quarter.addWidget(left90)
        quarter.addWidget(right90)
        align.body.addLayout(quarter)

        self.selection_hint = QLabel("Drag on the photo to create a crop selection.")
        self.selection_hint.setObjectName("hintLabel")
        self.selection_hint.setWordWrap(True)
        align.body.addWidget(self.selection_hint)
        self.crop_btn = QPushButton("Crop selection")
        self.crop_btn.setObjectName("secondaryButton")
        self.crop_btn.setEnabled(False)
        self.crop_btn.clicked.connect(self.crop_requested)
        align.body.addWidget(self.crop_btn)
        layout.addWidget(align)

        background = Section("3", "Background")
        bg_note = QLabel("Use local background removal, then place the subject on pure white.")
        bg_note.setObjectName("hintLabel")
        bg_note.setWordWrap(True)
        background.body.addWidget(bg_note)
        self.prepare_btn = QPushButton("Remove background + white")
        self.prepare_btn.setObjectName("primaryButton")
        self.prepare_btn.setEnabled(False)
        self.prepare_btn.clicked.connect(self._emit_prepare)
        background.body.addWidget(self.prepare_btn)
        self.white_btn = QPushButton("Fill transparency with white")
        self.white_btn.setObjectName("secondaryButton")
        self.white_btn.clicked.connect(self.white_bg_requested)
        background.body.addWidget(self.white_btn)
        layout.addWidget(background)

        output = Section("4", "Export")
        self.output_summary = QLabel()
        self.output_summary.setObjectName("outputSummary")
        self.output_summary.setWordWrap(True)
        output.body.addWidget(self.output_summary)
        self.export_btn = QPushButton("Export JPEG")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.clicked.connect(self._choose_export)
        output.body.addWidget(self.export_btn)
        layout.addWidget(output)

        self.width_px.valueChanged.connect(self._update_summary)
        self.height_px.valueChanged.connect(self._update_summary)
        self.target_kb.valueChanged.connect(self._update_summary)

        layout.addStretch(1)
        self.setWidget(root)
        self._apply_preset(self.preset.currentText())

    def _apply_preset(self, name: str):
        width, height, kb = PRESETS[name]
        self.width_px.setValue(width)
        self.height_px.setValue(height)
        self.target_kb.setValue(kb)
        self._update_summary()

    def _update_summary(self):
        self.output_summary.setText(
            f"{self.width_px.value()} × {self.height_px.value()} px  •  ≤ {self.target_kb.value()} KB  •  JPEG"
        )

    def _slider_changed(self, value: int):
        angle = value / 10.0
        self.angle_spin.blockSignals(True)
        self.angle_spin.setValue(angle)
        self.angle_spin.blockSignals(False)
        self.rotation_preview_requested.emit(angle)

    def _spin_changed(self, angle: float):
        self.angle_slider.blockSignals(True)
        self.angle_slider.setValue(round(angle * 10))
        self.angle_slider.blockSignals(False)
        self.rotation_preview_requested.emit(angle)

    def _set_angle(self, angle: float):
        self.angle_spin.setValue(angle)

    def _reset_rotation(self):
        self.rotation_reset_requested.emit()
        self.angle_slider.blockSignals(True)
        self.angle_spin.blockSignals(True)
        self.angle_slider.setValue(0)
        self.angle_spin.setValue(0.0)
        self.angle_slider.blockSignals(False)
        self.angle_spin.blockSignals(False)

    def reset_angle_controls(self):
        self.angle_slider.blockSignals(True)
        self.angle_spin.blockSignals(True)
        self.angle_slider.setValue(0)
        self.angle_spin.setValue(0.0)
        self.angle_slider.blockSignals(False)
        self.angle_spin.blockSignals(False)

    def _emit_prepare(self):
        self.prepare_requested.emit(self.width_px.value(), self.height_px.value())

    def set_selection_available(self, available: bool):
        self.crop_btn.setEnabled(available)
        self.prepare_btn.setEnabled(available)
        self.selection_hint.setText(
            "Selection ready. Fine-tune it on the image, then crop or prepare."
            if available else "Drag on the photo to create a crop selection."
        )

    def _choose_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export prepared photo", "prepared-photo.jpg", "JPEG Image (*.jpg *.jpeg)"
        )
        if not path:
            return
        if not path.lower().endswith((".jpg", ".jpeg")):
            path += ".jpg"
        self.export_requested.emit(path, self.width_px.value(), self.height_px.value(), self.target_kb.value())
