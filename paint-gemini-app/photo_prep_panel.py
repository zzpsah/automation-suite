from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDockWidget, QFileDialog, QFormLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)


PRESETS = {
    "Passport Photo — 35×45 mm (300 DPI)": (413, 531, 100),
    "Signature — 140×60 px": (140, 60, 50),
    "Custom": (413, 531, 100),
}


class PhotoPrepPanel(QDockWidget):
    prepare_requested = pyqtSignal(int, int)
    crop_requested = pyqtSignal()
    white_bg_requested = pyqtSignal()
    export_requested = pyqtSignal(str, int, int, int)

    def __init__(self, parent=None):
        super().__init__("Photo Preparation", parent)
        self.setObjectName("PhotoPrepPanel")
        root = QWidget()
        layout = QVBoxLayout(root)

        preset_box = QGroupBox("Output standard")
        form = QFormLayout(preset_box)

        self.preset = QComboBox()
        self.preset.addItems(PRESETS.keys())
        self.preset.currentTextChanged.connect(self._apply_preset)
        form.addRow("Preset", self.preset)

        self.width_px = QSpinBox()
        self.width_px.setRange(20, 5000)
        self.height_px = QSpinBox()
        self.height_px.setRange(20, 5000)
        self.target_kb = QSpinBox()
        self.target_kb.setRange(5, 5000)
        self.target_kb.setSuffix(" KB max")
        form.addRow("Width", self.width_px)
        form.addRow("Height", self.height_px)
        form.addRow("File size", self.target_kb)
        layout.addWidget(preset_box)

        selection_box = QGroupBox("Selection actions")
        selection_layout = QVBoxLayout(selection_box)
        self.selection_hint = QLabel("Draw a selection on the photo first.")
        self.selection_hint.setWordWrap(True)
        selection_layout.addWidget(self.selection_hint)

        self.crop_btn = QPushButton("Crop to Selection")
        self.crop_btn.setEnabled(False)
        self.crop_btn.clicked.connect(self.crop_requested)
        selection_layout.addWidget(self.crop_btn)

        self.prepare_btn = QPushButton("One Click: Crop + White Background")
        self.prepare_btn.setEnabled(False)
        self.prepare_btn.setToolTip(
            "Uses the selected rectangle, removes its background locally, fills it white, "
            "and resizes it to the configured dimensions."
        )
        self.prepare_btn.clicked.connect(self._emit_prepare)
        selection_layout.addWidget(self.prepare_btn)
        layout.addWidget(selection_box)

        output_box = QGroupBox("Output")
        output_layout = QVBoxLayout(output_box)
        self.white_btn = QPushButton("Set Existing Transparency to White")
        self.white_btn.clicked.connect(self.white_bg_requested)
        output_layout.addWidget(self.white_btn)

        self.export_btn = QPushButton("Export Prepared JPEG…")
        self.export_btn.clicked.connect(self._choose_export)
        output_layout.addWidget(self.export_btn)
        self.output_hint = QLabel(
            "JPEG export keeps the configured pixel dimensions and tries to stay under the KB limit."
        )
        self.output_hint.setWordWrap(True)
        output_layout.addWidget(self.output_hint)
        layout.addWidget(output_box)

        layout.addStretch(1)
        self.setWidget(root)
        self._apply_preset(self.preset.currentText())

    def _apply_preset(self, name: str):
        width, height, kb = PRESETS[name]
        self.width_px.setValue(width)
        self.height_px.setValue(height)
        self.target_kb.setValue(kb)

    def _emit_prepare(self):
        self.prepare_requested.emit(self.width_px.value(), self.height_px.value())

    def set_selection_available(self, available: bool):
        self.crop_btn.setEnabled(available)
        self.prepare_btn.setEnabled(available)
        self.selection_hint.setText(
            "Selection ready — choose Crop or the one-click white-background action."
            if available else "Draw a selection on the photo first."
        )

    def _choose_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Prepared Photo", "prepared-photo.jpg", "JPEG Image (*.jpg *.jpeg)"
        )
        if not path:
            return
        if not path.lower().endswith((".jpg", ".jpeg")):
            path += ".jpg"
        self.export_requested.emit(
            path, self.width_px.value(), self.height_px.value(), self.target_kb.value()
        )
