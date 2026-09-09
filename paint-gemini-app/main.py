"""Photo Prep Studio — lightweight PyQt6 photo/signature preparation tool."""
import io
import os
import sys

from PIL import Image
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QActionGroup, QColor, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QColorDialog, QFileDialog, QLabel, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSpinBox, QStatusBar, QToolBar,
)

from adjustments_dialog import AdjustmentsDialog
from bg_remover import BackgroundRemovalWorker
from canvas import Canvas, pil_to_qimage, qimage_to_pil
from photo_prep_panel import PhotoPrepPanel


class ColorSwatch(QPushButton):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.color = color
        self.setToolTip("Click to change color")
        self._update_style()

    def set_color(self, color: QColor):
        self.color = color
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(
            f"background-color: {self.color.name()}; border: 2px solid #333; border-radius: 4px;"
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Prep Studio — Untitled")
        self.resize(1400, 900)

        self.canvas = Canvas(1000, 700)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.scroll)

        self.current_file = None
        self.bg_worker = None
        self._prepare_dimensions = None

        self._build_toolbar()
        self._build_menu()
        self._build_statusbar()
        self._build_photo_prep_dock()

        self.canvas.status_message.connect(self.statusBar().showMessage)
        self.canvas.modified.connect(self._on_modified)

    def _build_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)

        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        tools = [
            ("brush", "Brush (B)"), ("pencil", "Pencil (P)"), ("eraser", "Eraser (E)"),
            ("line", "Line (L)"), ("rect", "Rectangle (R)"), ("ellipse", "Ellipse (O)"),
            ("select", "Select (S)"), ("crop", "Crop (C)"),
        ]
        self.tool_actions = {}
        for key, label in tools:
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, k=key: self._set_tool(k))
            self.tool_group.addAction(action)
            toolbar.addAction(action)
            self.tool_actions[key] = action
        self.tool_actions["select"].setChecked(True)
        self.canvas.tool = "select"

        toolbar.addSeparator()
        self.primary_swatch = ColorSwatch(self.canvas.primary_color)
        self.primary_swatch.clicked.connect(self._pick_primary_color)
        toolbar.addWidget(self.primary_swatch)
        self.secondary_swatch = ColorSwatch(self.canvas.secondary_color)
        self.secondary_swatch.clicked.connect(self._pick_secondary_color)
        toolbar.addWidget(self.secondary_swatch)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel(" Width: "))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 100)
        self.width_spin.setValue(self.canvas.pen_width)
        self.width_spin.valueChanged.connect(lambda value: setattr(self.canvas, "pen_width", value))
        toolbar.addWidget(self.width_spin)

        toolbar.addSeparator()
        quick = QAction("Crop + White BG", self)
        quick.setToolTip("Prepare the current selection using the side-panel dimensions")
        quick.triggered.connect(self._prepare_from_panel)
        toolbar.addAction(quick)

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        self._add_action(file_menu, "New", "Ctrl+N", self.new_file)
        self._add_action(file_menu, "Open...", "Ctrl+O", self.open_file)
        self._add_action(file_menu, "Save", "Ctrl+S", self.save_file)
        self._add_action(file_menu, "Save As...", "Ctrl+Shift+S", self.save_file_as)
        self._add_action(file_menu, "Export Prepared JPEG...", "Ctrl+Alt+S", self.photo_export_dialog)
        file_menu.addSeparator()
        self._add_action(file_menu, "Exit", "Ctrl+Q", self.close)

        edit_menu = menubar.addMenu("&Edit")
        self._add_action(edit_menu, "Undo", "Ctrl+Z", self.canvas.undo)
        self._add_action(edit_menu, "Redo", "Ctrl+Y", self.canvas.redo)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Cut", "Ctrl+X", self.cut)
        self._add_action(edit_menu, "Copy", "Ctrl+C", self.copy)
        self._add_action(edit_menu, "Paste", "Ctrl+V", self.paste)
        self._add_action(edit_menu, "Delete", "Del", self.canvas.delete_selection)

        image_menu = menubar.addMenu("&Image")
        self._add_action(image_menu, "Crop to Selection", "Ctrl+Shift+X", self.canvas.crop_to_selection)
        self._add_action(image_menu, "Crop + White Background", None, self._prepare_from_panel)
        self._add_action(image_menu, "Set Transparency to White", None, self.flatten_to_white)
        image_menu.addSeparator()
        self._add_action(image_menu, "Rotate 90° CW", None, lambda: self.canvas.rotate(90))
        self._add_action(image_menu, "Rotate 90° CCW", None, lambda: self.canvas.rotate(-90))
        self._add_action(image_menu, "Flip Horizontal", None, lambda: self.canvas.flip(True))
        self._add_action(image_menu, "Flip Vertical", None, lambda: self.canvas.flip(False))
        image_menu.addSeparator()
        self._add_action(image_menu, "Adjustments...", "Ctrl+M", self.open_adjustments)
        self._add_action(image_menu, "Auto-Enhance", "Ctrl+E", self.canvas.auto_enhance)

        view_menu = menubar.addMenu("&View")
        self._add_action(view_menu, "Zoom In", "Ctrl+=", lambda: self.canvas.set_zoom(self.canvas.zoom * 1.25))
        self._add_action(view_menu, "Zoom Out", "Ctrl+-", lambda: self.canvas.set_zoom(self.canvas.zoom / 1.25))
        self._add_action(view_menu, "Reset Zoom", "Ctrl+0", lambda: self.canvas.set_zoom(1.0))
        self._add_action(view_menu, "Toggle Photo Panel", None, self._toggle_photo_panel)

    def _build_statusbar(self):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Select the face/photo area, then use the Photo Preparation panel.")

    def _build_photo_prep_dock(self):
        self.photo_panel = PhotoPrepPanel(self)
        self.photo_panel.crop_requested.connect(self.canvas.crop_to_selection)
        self.photo_panel.prepare_requested.connect(self.prepare_selection)
        self.photo_panel.white_bg_requested.connect(self.flatten_to_white)
        self.photo_panel.export_requested.connect(self.export_prepared)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.photo_panel)

    def _toggle_photo_panel(self):
        self.photo_panel.setVisible(not self.photo_panel.isVisible())

    def _set_tool(self, tool: str):
        self.canvas.tool = tool
        self.statusBar().showMessage(f"Tool: {tool}")

    def _pick_primary_color(self):
        color = QColorDialog.getColor(self.canvas.primary_color, self, "Select Primary Color")
        if color.isValid():
            self.canvas.primary_color = color
            self.primary_swatch.set_color(color)

    def _pick_secondary_color(self):
        color = QColorDialog.getColor(self.canvas.secondary_color, self, "Select Secondary Color")
        if color.isValid():
            self.canvas.secondary_color = color
            self.secondary_swatch.set_color(color)

    def _add_action(self, menu, text, shortcut, slot):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def new_file(self):
        self.canvas.new_canvas()
        self.current_file = None
        self.setWindowTitle("Photo Prep Studio — Untitled")
        self._refresh_selection_state()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            try:
                self.canvas.load_file(path)
                self.current_file = path
                self.setWindowTitle(f"Photo Prep Studio — {os.path.basename(path)}")
                self.tool_actions["select"].setChecked(True)
                self.canvas.tool = "select"
                self._refresh_selection_state()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def save_file(self):
        if self.current_file:
            try:
                self.canvas.save_file(self.current_file)
                self.statusBar().showMessage(f"Saved to {self.current_file}", 3000)
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if path:
            try:
                self.canvas.save_file(path)
                self.current_file = path
                self.setWindowTitle(f"Photo Prep Studio — {os.path.basename(path)}")
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def cut(self):
        img = self.canvas.cut_selection()
        if img is not None:
            QApplication.clipboard().setImage(img)
        self._refresh_selection_state()

    def copy(self):
        img = self.canvas.copy_selection()
        QApplication.clipboard().setImage(img if img is not None else self.canvas.image)

    def paste(self):
        img = QApplication.clipboard().image()
        if img.isNull():
            self.statusBar().showMessage("Clipboard has no image", 3000)
            return
        self.canvas.paste_image(img)
        self.tool_actions["select"].setChecked(True)
        self.canvas.tool = "select"
        self._refresh_selection_state()

    def open_adjustments(self):
        AdjustmentsDialog(self.canvas, self).exec()

    def _selection_available(self):
        rect = self.canvas.selection_rect
        return rect is not None and rect.isValid() and rect.width() > 1 and rect.height() > 1

    def _refresh_selection_state(self):
        if hasattr(self, "photo_panel"):
            self.photo_panel.set_selection_available(self._selection_available())

    def _selected_region(self):
        if not self._selection_available():
            return None
        rect = self.canvas.selection_rect.intersected(self.canvas.image.rect())
        return self.canvas.rendered_image().copy(rect)

    def _prepare_from_panel(self):
        self.prepare_selection(self.photo_panel.width_px.value(), self.photo_panel.height_px.value())

    def prepare_selection(self, width: int, height: int):
        if self.bg_worker is not None and self.bg_worker.isRunning():
            return
        region = self._selected_region()
        if region is None or region.isNull():
            QMessageBox.information(self, "Selection Required", "Use the Select tool and draw a rectangle around the photo first.")
            return
        self._prepare_dimensions = (width, height)
        self.statusBar().showMessage("Removing background and preparing white-background image…")
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
        self.statusBar().showMessage(f"Prepared image: {width} × {height}px, white background", 5000)

    def _on_bg_failed(self, error: str):
        QMessageBox.warning(self, "Background Removal Failed", error)
        self.statusBar().showMessage("Background removal failed", 3000)

    def flatten_to_white(self):
        self.canvas.push_undo()
        rgba = qimage_to_pil(self.canvas.rendered_image()).convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        white.alpha_composite(rgba)
        self.canvas.image = pil_to_qimage(white)
        self.canvas.floating_image = None
        self.canvas.floating_origin = None
        self.canvas.update()
        self.canvas.modified.emit()

    def photo_export_dialog(self):
        self.photo_panel._choose_export()

    def export_prepared(self, path: str, width: int, height: int, target_kb: int):
        try:
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
                self.statusBar().showMessage(
                    f"Exported {width}×{height}px — {actual_kb:.1f} KB (quality {best_quality})", 6000
                )
            else:
                QMessageBox.warning(
                    self, "File Size Limit",
                    f"Saved at minimum JPEG quality, but the file is {actual_kb:.1f} KB, "
                    f"above the requested {target_kb} KB. Increase the KB limit."
                )
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _on_modified(self):
        title = self.windowTitle()
        if not title.endswith("*"):
            self.setWindowTitle(title + " *")
        self._refresh_selection_state()

    def keyPressEvent(self, event):
        key_map = {
            Qt.Key.Key_B: "brush", Qt.Key.Key_P: "pencil", Qt.Key.Key_E: "eraser",
            Qt.Key.Key_L: "line", Qt.Key.Key_R: "rect", Qt.Key.Key_O: "ellipse",
            Qt.Key.Key_S: "select", Qt.Key.Key_C: "crop",
        }
        if event.key() in key_map and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            key = key_map[event.key()]
            self.tool_actions[key].setChecked(True)
            self.canvas.tool = key
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.bg_worker is not None and self.bg_worker.isRunning():
            self.bg_worker.terminate()
            self.bg_worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Prep Studio")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
