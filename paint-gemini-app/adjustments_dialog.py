"""
adjustments_dialog.py — Live-preview dialog for Brightness / Contrast /
Saturation / Sharpness, backed by PIL ImageEnhance in canvas.py.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QSlider, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt


class AdjustmentsDialog(QDialog):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adjustments")
        self.canvas = canvas
        self.setMinimumWidth(340)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sliders = {}
        for name in ("Brightness", "Contrast", "Saturation", "Sharpness"):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 200)
            slider.setValue(100)
            slider.valueChanged.connect(self._preview)
            self.sliders[name] = slider
            form.addRow(QLabel(name), slider)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._cancel)
        apply_btn = QPushButton("Apply")
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self._apply)
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(apply_btn)
        layout.addLayout(btn_row)

        # Snapshot of whatever we're adjusting (floating selection or whole image)
        # so Cancel/Reset can restore it exactly.
        self._original_target = (canvas.floating_image.copy() if canvas.floating_image is not None
                                  else canvas.image.copy())

    def _values(self):
        return {k.lower(): v.value() / 100.0 for k, v in self.sliders.items()}

    def _preview(self):
        vals = self._values()
        preview = self.canvas.apply_adjustments(
            brightness=vals["brightness"], contrast=vals["contrast"],
            saturation=vals["saturation"], sharpness=vals["sharpness"], commit=False)
        if self.canvas.floating_image is not None:
            self.canvas.floating_image = preview
        else:
            self.canvas.image = preview
        self.canvas.update()

    def _restore_original(self):
        if self.canvas.floating_image is not None:
            self.canvas.floating_image = self._original_target.copy()
        else:
            self.canvas.image = self._original_target.copy()
        self.canvas.update()

    def _apply(self):
        # Restore the pristine original, push ONE undo step, then reapply
        # the currently selected slider values as the committed result.
        self._restore_original()
        self.canvas.push_undo()
        self._preview()
        self.canvas.modified.emit()
        self.accept()

    def _reset(self):
        for s in self.sliders.values():
            s.blockSignals(True)
            s.setValue(100)
            s.blockSignals(False)
        self._restore_original()

    def _cancel(self):
        self._restore_original()
        self.reject()
