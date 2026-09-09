"""
main.py — PyPaint AI: an MS Paint clone with local AI background removal
(rembg) and an integrated Google Gemini assistant panel.

Run with:  python main.py
"""
import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QFileDialog, QMessageBox,
    QColorDialog, QSpinBox, QLabel, QStatusBar, QScrollArea, QPushButton,
)
from PyQt6.QtGui import QAction, QKeySequence, QColor, QImage, QActionGroup
from PyQt6.QtCore import Qt, QSize

from canvas import Canvas
from bg_remover import BackgroundRemovalWorker
from gemini_panel import GeminiPanel
from adjustments_dialog import AdjustmentsDialog


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
            f"background-color: {self.color.name()}; border: 2px solid #333333; border-radius: 4px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyPaint AI — Untitled")
        self.resize(1400, 900)

        self.canvas = Canvas(1000, 700)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setWidgetResizable(False)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.scroll)

        self.current_file = None
        self.bg_worker = None

        self._build_toolbar()
        self._build_menu()
        self._build_statusbar()
        self._build_gemini_dock()

        self.canvas.status_message.connect(self.statusBar().showMessage)
        self.canvas.modified.connect(self._on_modified)

    # ------------------------------------------------------------ toolbar
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
        self.tool_actions["brush"].setChecked(True)

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
        self.width_spin.valueChanged.connect(self._set_pen_width)
        toolbar.addWidget(self.width_spin)

        toolbar.addSeparator()
        remove_bg_action = QAction("Remove BG", self)
        remove_bg_action.setToolTip("Remove Background (rembg)")
        remove_bg_action.triggered.connect(self.remove_background)
        toolbar.addAction(remove_bg_action)

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

    def _set_pen_width(self, value):
        self.canvas.pen_width = value

    # ------------------------------------------------------------ menu
    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        self._add_action(file_menu, "New", "Ctrl+N", self.new_file)
        self._add_action(file_menu, "Open...", "Ctrl+O", self.open_file)
        self._add_action(file_menu, "Save", "Ctrl+S", self.save_file)
        self._add_action(file_menu, "Save As...", "Ctrl+Shift+S", self.save_file_as)
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
        self._add_action(image_menu, "Rotate 90° CW", None, lambda: self.canvas.rotate(90))
        self._add_action(image_menu, "Rotate 90° CCW", None, lambda: self.canvas.rotate(-90))
        self._add_action(image_menu, "Flip Horizontal", None, lambda: self.canvas.flip(True))
        self._add_action(image_menu, "Flip Vertical", None, lambda: self.canvas.flip(False))
        image_menu.addSeparator()
        self._add_action(image_menu, "Crop to Selection", "Ctrl+Shift+X", self.canvas.crop_to_selection)
        image_menu.addSeparator()
        self._add_action(image_menu, "Adjustments...", "Ctrl+M", self.open_adjustments)
        self._add_action(image_menu, "Auto-Enhance", "Ctrl+E", self.canvas.auto_enhance)
        image_menu.addSeparator()
        self._add_action(image_menu, "Remove Background", None, self.remove_background)

        view_menu = menubar.addMenu("&View")
        self._add_action(view_menu, "Zoom In", "Ctrl+=", lambda: self.canvas.set_zoom(self.canvas.zoom * 1.25))
        self._add_action(view_menu, "Zoom Out", "Ctrl+-", lambda: self.canvas.set_zoom(self.canvas.zoom / 1.25))
        self._add_action(view_menu, "Reset Zoom", "Ctrl+0", lambda: self.canvas.set_zoom(1.0))
        self._add_action(view_menu, "Toggle AI Panel", None, self._toggle_gemini_panel)

    def _add_action(self, menu, text, shortcut, slot):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    # ------------------------------------------------------------ status bar
    def _build_statusbar(self):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------ gemini dock
    def _build_gemini_dock(self):
        self.gemini_dock = GeminiPanel(self.canvas.to_png_bytes, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.gemini_dock)

    def _toggle_gemini_panel(self):
        self.gemini_dock.setVisible(not self.gemini_dock.isVisible())

    # ------------------------------------------------------------ file actions
    def new_file(self):
        self.canvas.new_canvas()
        self.current_file = None
        self.setWindowTitle("PyPaint AI — Untitled")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "",
                                               "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            try:
                self.canvas.load_file(path)
                self.current_file = path
                self.setWindowTitle(f"PyPaint AI — {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_file(self):
        if self.current_file:
            try:
                self.canvas.save_file(self.current_file)
                self.statusBar().showMessage(f"Saved to {self.current_file}", 3000)
                self.setWindowTitle(self.windowTitle().rstrip(" *"))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "",
                                               "PNG Image (*.png);;JPEG Image (*.jpg)")
        if path:
            try:
                self.canvas.save_file(path)
                self.current_file = path
                self.setWindowTitle(f"PyPaint AI — {os.path.basename(path)}")
                self.statusBar().showMessage(f"Saved to {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------ clipboard
    def cut(self):
        img = self.canvas.cut_selection()
        if img is not None:
            QApplication.clipboard().setImage(img)

    def copy(self):
        img = self.canvas.copy_selection()
        QApplication.clipboard().setImage(img if img is not None else self.canvas.image)

    def paste(self):
        clipboard = QApplication.clipboard()
        img = clipboard.image()
        if img.isNull():
            self.statusBar().showMessage("Clipboard has no image", 3000)
            return
        self.canvas.paste_image(img)
        self.tool_actions["select"].setChecked(True)
        self.canvas.tool = "select"

    # ------------------------------------------------------------ adjustments
    def open_adjustments(self):
        dlg = AdjustmentsDialog(self.canvas, self)
        dlg.exec()

    # ------------------------------------------------------------ background removal
    def remove_background(self):
        if self.bg_worker is not None and self.bg_worker.isRunning():
            return
        region, _ = self.canvas.get_active_region_for_ai()
        self.statusBar().showMessage("Removing background... this may take a moment (first run downloads the model)")
        self.bg_worker = BackgroundRemovalWorker(region)
        self.bg_worker.finished_ok.connect(self._on_bg_removed)
        self.bg_worker.failed.connect(self._on_bg_failed)
        self.bg_worker.start()

    def _on_bg_removed(self, result_image: QImage):
        self.canvas.apply_removed_background(result_image)
        self.statusBar().showMessage("Background removed", 3000)

    def _on_bg_failed(self, error: str):
        QMessageBox.warning(self, "Background Removal Failed", error)
        self.statusBar().showMessage("Background removal failed", 3000)

    # ------------------------------------------------------------ misc
    def _on_modified(self):
        title = self.windowTitle()
        if not title.endswith("*"):
            self.setWindowTitle(title + " *")

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
    app.setApplicationName("PyPaint AI")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
