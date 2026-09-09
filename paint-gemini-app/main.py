"""Photo Prep Studio — focused passport/signature image preparation utility."""
import io
import os
import sys

from PIL import Image
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QTransform
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QMessageBox, QScrollArea,
    QStatusBar, QToolBar,
)

from adjustments_dialog import AdjustmentsDialog
from bg_remover import BackgroundRemovalWorker
from canvas import Canvas, pil_to_qimage, qimage_to_pil
from photo_prep_panel import PhotoPrepPanel


APP_STYLE = """
QMainWindow { background: #eef1f5; }
QMenuBar { background: #ffffff; border-bottom: 1px solid #d9dee7; padding: 3px; }
QMenuBar::item { padding: 6px 10px; border-radius: 5px; }
QMenuBar::item:selected { background: #eef3ff; }
QMenu { background: #ffffff; border: 1px solid #d9dee7; padding: 5px; }
QToolBar { background: #ffffff; border: none; border-bottom: 1px solid #d9dee7; spacing: 5px; padding: 7px 10px; }
QToolButton { padding: 7px 12px; border: 1px solid transparent; border-radius: 7px; background: transparent; }
QToolButton:hover { background: #f0f4fa; border-color: #d7deea; }
QToolButton:checked { background: #e7efff; color: #174ea6; border-color: #b9cef7; }
QScrollArea { background: #353a43; border: none; }
QStatusBar { background: #ffffff; border-top: 1px solid #d9dee7; color: #5f6875; }
QDockWidget { color: #202631; font-weight: 600; }
QDockWidget::title { background: #ffffff; padding: 8px 12px; border-bottom: 1px solid #d9dee7; }
#panelRoot { background: #f7f8fb; }
#panelTitle { font-size: 22px; font-weight: 800; color: #171c24; letter-spacing: 1px; }
#panelSubtitle { color: #697386; font-size: 12px; }
#sectionCard { background: #ffffff; border: 1px solid #e0e4eb; border-radius: 10px; }
#sectionTitle { font-size: 14px; font-weight: 700; color: #202631; }
#stepBadge { background: #2463eb; color: white; border-radius: 12px; font-weight: 800; }
QLabel { color: #4b5565; }
QComboBox, QSpinBox, QDoubleSpinBox { min-height: 32px; padding: 2px 8px; background: #ffffff; border: 1px solid #ccd3df; border-radius: 7px; color: #202631; }
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #2463eb; }
QSlider::groove:horizontal { height: 5px; background: #dce2ec; border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #2463eb; border-radius: 8px; }
QPushButton { min-height: 34px; border-radius: 7px; font-weight: 600; padding: 2px 10px; }
#primaryButton { background: #2463eb; color: white; border: 1px solid #2463eb; }
#primaryButton:hover { background: #1d55cf; }
#primaryButton:disabled { background: #aab8d4; border-color: #aab8d4; }
#secondaryButton, #smallButton { background: #ffffff; color: #303846; border: 1px solid #ccd3df; }
#secondaryButton:hover, #smallButton:hover { background: #f1f4f8; }
#secondaryButton:disabled { color: #9aa3af; background: #f4f5f7; }
#hintLabel { color: #737d8d; font-size: 11px; }
#outputSummary { background: #f2f6ff; color: #224b9c; border: 1px solid #d7e3ff; border-radius: 7px; padding: 8px; font-weight: 600; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Prep Studio — Untitled")
        self.resize(1450, 900)
        self.setMinimumSize(1050, 700)

        self.canvas = Canvas(1000, 700)
        self.canvas.tool = "select"

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.scroll)

        self.current_file = None
        self.bg_worker = None
        self._prepare_dimensions = None
        self._rotation_base = None
        self._rotation_angle = 0.0

        self._build_toolbar()
        self._build_menu()
        self._build_statusbar()
        self._build_photo_prep_dock()

        self.canvas.status_message.connect(self.statusBar().showMessage)
        self.canvas.modified.connect(self._on_modified)

    def _build_toolbar(self):
        bar = QToolBar("Main")
        bar.setMovable(False)
        bar.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)

        open_action = QAction("Open photo", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_file)
        bar.addAction(open_action)

        bar.addSeparator()
        select_action = QAction("Select / crop", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(self._set_select_tool)
        bar.addAction(select_action)

        crop_action = QAction("Crop", self)
        crop_action.triggered.connect(self.crop_selection)
        bar.addAction(crop_action)

        bar.addSeparator()
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.canvas.undo)
        bar.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.canvas.redo)
        bar.addAction(redo_action)

        bar.addSeparator()
        fit_action = QAction("Fit view", self)
        fit_action.triggered.connect(self.fit_view)
        bar.addAction(fit_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.photo_export_dialog)
        bar.addAction(export_action)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        self._add_action(file_menu, "Open photo…", "Ctrl+O", self.open_file)
        self._add_action(file_menu, "Save as…", "Ctrl+Shift+S", self.save_file_as)
        self._add_action(file_menu, "Export prepared JPEG…", "Ctrl+Alt+S", self.photo_export_dialog)
        file_menu.addSeparator()
        self._add_action(file_menu, "Exit", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("Edit")
        self._add_action(edit_menu, "Undo", "Ctrl+Z", self.canvas.undo)
        self._add_action(edit_menu, "Redo", "Ctrl+Y", self.canvas.redo)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Adjust brightness / contrast…", "Ctrl+M", self.open_adjustments)
        self._add_action(edit_menu, "Auto enhance", "Ctrl+E", self.canvas.auto_enhance)

        image_menu = menubar.addMenu("Image")
        self._add_action(image_menu, "Rotate 90° left", None, lambda: self.rotate_90(-90))
        self._add_action(image_menu, "Rotate 90° right", None, lambda: self.rotate_90(90))
        self._add_action(image_menu, "Flip horizontal", None, lambda: self.canvas.flip(True))
        self._add_action(image_menu, "Flip vertical", None, lambda: self.canvas.flip(False))
        image_menu.addSeparator()
        self._add_action(image_menu, "Crop selection", None, self.crop_selection)
        self._add_action(image_menu, "White background", None, self.flatten_to_white)

        view_menu = menubar.addMenu("View")
        self._add_action(view_menu, "Zoom in", "Ctrl+=", lambda: self.canvas.set_zoom(self.canvas.zoom * 1.25))
        self._add_action(view_menu, "Zoom out", "Ctrl+-", lambda: self.canvas.set_zoom(self.canvas.zoom / 1.25))
        self._add_action(view_menu, "Fit view", "Ctrl+0", self.fit_view)

    def _build_statusbar(self):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Open a photo. Straighten it, select the crop, then prepare and export.")

    def _build_photo_prep_dock(self):
        self.photo_panel = PhotoPrepPanel(self)
        self.photo_panel.crop_requested.connect(self.crop_selection)
        self.photo_panel.prepare_requested.connect(self.prepare_selection)
        self.photo_panel.white_bg_requested.connect(self.flatten_to_white)
        self.photo_panel.export_requested.connect(self.export_prepared)
        self.photo_panel.rotation_preview_requested.connect(self.preview_rotation)
        self.photo_panel.rotation_commit_requested.connect(self.commit_rotation)
        self.photo_panel.rotation_reset_requested.connect(self.reset_rotation_preview)
        self.photo_panel.rotate90_requested.connect(self.rotate_90)
        self.photo_panel.flip_requested.connect(self.canvas.flip)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.photo_panel)

    def _add_action(self, menu, text, shortcut, slot):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open photo", "", "Images (*.jpg *.jpeg *.png *.bmp *.webp)"
        )
        if not path:
            return
        try:
            self.canvas.load_file(path)
            self.current_file = path
            self.setWindowTitle(f"Photo Prep Studio — {os.path.basename(path)}")
            self._rotation_base = None
            self.photo_panel.reset_angle_controls()
            self._set_select_tool()
            self.fit_view()
            self._refresh_selection_state()
        except Exception as exc:
            QMessageBox.critical(self, "Open failed", str(exc))

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save image", "prepared-photo.png", "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
        )
        if not path:
            return
        try:
            self.commit_rotation()
            self.canvas.save_file(path)
            self.current_file = path
            self.statusBar().showMessage(f"Saved: {path}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def _set_select_tool(self):
        self.commit_rotation()
        self.canvas.tool = "select"
        self.statusBar().showMessage("Drag on the image to mark the crop area.")

    def _selection_available(self):
        rect = self.canvas.selection_rect
        return rect is not None and rect.isValid() and rect.width() > 2 and rect.height() > 2

    def _refresh_selection_state(self):
        if hasattr(self, "photo_panel"):
            self.photo_panel.set_selection_available(self._selection_available())

    def _selected_region(self):
        if not self._selection_available():
            return None
        rect = self.canvas.selection_rect.intersected(self.canvas.image.rect())
        return self.canvas.rendered_image().copy(rect)

    def crop_selection(self):
        self.commit_rotation()
        if not self._selection_available():
            QMessageBox.information(self, "Crop", "Drag a selection rectangle on the photo first.")
            return
        self.canvas.crop_to_selection()
        self._refresh_selection_state()
        self.fit_view()

    def preview_rotation(self, angle: float):
        if abs(angle) < 0.0001 and self._rotation_base is None:
            return
        if self._rotation_base is None:
            self.canvas.commit_floating()
            self._rotation_base = self.canvas.image.copy()
            self._rotation_angle = 0.0
            self.canvas.selection_rect = None
            self._refresh_selection_state()

        transform = QTransform()
        transform.rotate(angle)
        self.canvas.image = self._rotation_base.transformed(
            transform, Qt.TransformationMode.SmoothTransformation
        )
        self._rotation_angle = angle
        self.canvas._resize_widget_to_image()
        self.canvas.update()
        self.statusBar().showMessage(f"Straighten preview: {angle:+.1f}° — press Apply angle when aligned")

    def commit_rotation(self):
        if self._rotation_base is None:
            return
        if abs(self._rotation_angle) > 0.0001:
            self.canvas.history.append(self._rotation_base.copy())
            if len(self.canvas.history) > 40:
                self.canvas.history.pop(0)
            self.canvas.redo_stack.clear()
            self.canvas.modified.emit()
        else:
            self.canvas.image = self._rotation_base.copy()
            self.canvas._resize_widget_to_image()
            self.canvas.update()
        self._rotation_base = None
        self._rotation_angle = 0.0
        self.photo_panel.reset_angle_controls()
        self.statusBar().showMessage("Rotation applied. Now drag to crop.", 4000)

    def reset_rotation_preview(self):
        if self._rotation_base is not None:
            self.canvas.image = self._rotation_base.copy()
            self.canvas._resize_widget_to_image()
            self.canvas.update()
        self._rotation_base = None
        self._rotation_angle = 0.0
        self.statusBar().showMessage("Straightening reset", 3000)

    def rotate_90(self, degrees: int):
        self.commit_rotation()
        self.canvas.rotate(degrees)
        self.photo_panel.reset_angle_controls()
        self.fit_view()

    def prepare_selection(self, width: int, height: int):
        self.commit_rotation()
        if self.bg_worker is not None and self.bg_worker.isRunning():
            return
        region = self._selected_region()
        if region is None or region.isNull():
            QMessageBox.information(self, "Selection required", "Drag a crop selection around the subject first.")
            return
        self._prepare_dimensions = (width, height)
        self.statusBar().showMessage("Removing background locally…")
        self.bg_worker = BackgroundRemovalWorker(region)
        self.bg_worker.finished_ok.connect(self._on_prepare_bg_removed)
        self.bg_worker.failed.connect(self._on_bg_failed)
        self.bg_worker.start()

    def _on_prepare_bg_removed(self, result):
        width, height = self._prepare_dimensions
        self.canvas.push_undo()
        rgba = qimage_to_pil(result).convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        white.alpha_composite(rgba)
        prepared = white.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
        self.canvas.image = pil_to_qimage(prepared.convert("RGBA"))
        self.canvas.selection_rect = None
        self.canvas.floating_image = None
        self.canvas.floating_origin = None
        self.canvas._resize_widget_to_image()
        self.canvas.update()
        self.canvas.modified.emit()
        self._refresh_selection_state()
        self.fit_view()
        self.statusBar().showMessage(f"Prepared: {width} × {height}px on pure white", 5000)

    def _on_bg_failed(self, error: str):
        QMessageBox.warning(self, "Background removal failed", error)
        self.statusBar().showMessage("Background removal failed", 3000)

    def flatten_to_white(self):
        self.commit_rotation()
        self.canvas.push_undo()
        rgba = qimage_to_pil(self.canvas.rendered_image()).convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        white.alpha_composite(rgba)
        self.canvas.image = pil_to_qimage(white)
        self.canvas.floating_image = None
        self.canvas.floating_origin = None
        self.canvas.update()
        self.canvas.modified.emit()
        self.statusBar().showMessage("Background flattened to pure white", 3000)

    def photo_export_dialog(self):
        self.commit_rotation()
        self.photo_panel._choose_export()

    def export_prepared(self, path: str, width: int, height: int, target_kb: int):
        try:
            self.commit_rotation()
            rgba = qimage_to_pil(self.canvas.rendered_image()).convert("RGBA")
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            white.alpha_composite(rgba)
            rgb = white.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            target_bytes = target_kb * 1024
            best = None
            best_quality = 10
            lo, hi = 10, 95
            while lo <= hi:
                quality = (lo + hi) // 2
                buf = io.BytesIO()
                rgb.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
                data = buf.getvalue()
                if len(data) <= target_bytes:
                    best = data
                    best_quality = quality
                    lo = quality + 1
                else:
                    hi = quality - 1
            if best is None:
                buf = io.BytesIO()
                rgb.save(buf, format="JPEG", quality=10, optimize=True, progressive=True)
                best = buf.getvalue()
            with open(path, "wb") as handle:
                handle.write(best)
            actual_kb = len(best) / 1024
            if len(best) <= target_bytes:
                QMessageBox.information(
                    self, "Export complete",
                    f"Saved successfully.\n\nDimensions: {width} × {height} px\nFile size: {actual_kb:.1f} KB\nJPEG quality: {best_quality}"
                )
            else:
                QMessageBox.warning(
                    self, "File size limit",
                    f"Saved at minimum JPEG quality, but the file is {actual_kb:.1f} KB. Increase the target above {target_kb} KB."
                )
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def fit_view(self):
        if self.canvas.image.width() <= 0 or self.canvas.image.height() <= 0:
            return
        viewport = self.scroll.viewport().size()
        margin = 70
        available_w = max(100, viewport.width() - margin)
        available_h = max(100, viewport.height() - margin)
        zoom = min(
            available_w / self.canvas.image.width(),
            available_h / self.canvas.image.height(),
            1.5,
        )
        self.canvas.set_zoom(max(0.1, zoom))

    def open_adjustments(self):
        self.commit_rotation()
        AdjustmentsDialog(self.canvas, self).exec()

    def _on_modified(self):
        if not self.windowTitle().endswith("*"):
            self.setWindowTitle(self.windowTitle() + " *")
        self._refresh_selection_state()

    def closeEvent(self, event):
        if self.bg_worker is not None and self.bg_worker.isRunning():
            self.bg_worker.terminate()
            self.bg_worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Prep Studio")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
