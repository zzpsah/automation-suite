"""
canvas.py — The drawing surface for PyPaint AI.

Handles: freehand/pencil/eraser drawing, shape tools (line/rect/ellipse),
rectangular selection with move support, floating pasted/AI-processed
images, undo/redo history, crop, rotate/flip, PIL-based adjustments,
and clipboard paste.
"""
import io
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QTransform
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, pyqtSignal
from PIL import Image, ImageEnhance, ImageOps

MAX_HISTORY = 40
IMG_FORMAT = QImage.Format.Format_ARGB32_Premultiplied


def qimage_to_pil(qimage: QImage) -> Image.Image:
    """Convert a QImage (any format) to an RGBA PIL Image."""
    qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = qimage.width(), qimage.height()
    ptr = qimage.constBits()
    ptr.setsize(h * qimage.bytesPerLine())
    buf = bytes(ptr)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", qimage.bytesPerLine(), 1)
    return img.copy()


def pil_to_qimage(pil_img: Image.Image) -> QImage:
    """Convert a PIL Image to a QImage in the canvas's native premultiplied format."""
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
    return qimage.convertToFormat(IMG_FORMAT)


class Canvas(QWidget):
    status_message = pyqtSignal(str)
    modified = pyqtSignal()

    def __init__(self, width=1000, height=700, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(50, 50)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.image = QImage(width, height, IMG_FORMAT)
        self.image.fill(QColor(255, 255, 255, 255))

        self.history = []
        self.redo_stack = []

        self.tool = "brush"
        self.primary_color = QColor(0, 0, 0)
        self.secondary_color = QColor(255, 255, 255)
        self.pen_width = 4

        self._drawing = False
        self._draw_color = self.primary_color
        self._last_point = QPoint()
        self._start_point = QPoint()
        self._temp_image = None

        self.selection_rect = None
        self.floating_image = None
        self.floating_origin = None
        self._selecting = False
        self._moving_floating = False
        self._move_offset = QPoint()

        self.zoom = 1.0
        self.setFixedSize(self.image.size())

    def widget_to_image_pt(self, pos: QPoint) -> QPoint:
        return QPoint(int(pos.x() / self.zoom), int(pos.y() / self.zoom))

    def set_zoom(self, zoom: float):
        self.zoom = max(0.1, min(zoom, 8.0))
        self.setFixedSize(int(self.image.width() * self.zoom), int(self.image.height() * self.zoom))
        self.update()

    def _resize_widget_to_image(self):
        self.setFixedSize(int(self.image.width() * self.zoom), int(self.image.height() * self.zoom))

    def push_undo(self):
        self.history.append(self.image.copy())
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
        self.redo_stack.clear()

    def undo(self):
        self.commit_floating()
        if not self.history:
            self.status_message.emit("Nothing to undo")
            return
        self.redo_stack.append(self.image.copy())
        self.image = self.history.pop()
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def redo(self):
        if not self.redo_stack:
            self.status_message.emit("Nothing to redo")
            return
        self.history.append(self.image.copy())
        self.image = self.redo_stack.pop()
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def new_canvas(self, width=1000, height=700):
        self.push_undo()
        self.image = QImage(width, height, IMG_FORMAT)
        self.image.fill(QColor(255, 255, 255, 255))
        self.selection_rect = None
        self.floating_image = None
        self.floating_origin = None
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def load_file(self, path: str):
        img = QImage(path)
        if img.isNull():
            raise ValueError(f"Could not load image: {path}")
        self.push_undo()
        self.image = img.convertToFormat(IMG_FORMAT)
        self.selection_rect = None
        self.floating_image = None
        self.floating_origin = None
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def save_file(self, path: str):
        self.commit_floating()
        img = self.image
        if path.lower().endswith((".jpg", ".jpeg")):
            flat = QImage(img.size(), QImage.Format.Format_RGB32)
            flat.fill(Qt.GlobalColor.white)
            p = QPainter(flat)
            p.drawImage(0, 0, img)
            p.end()
            img = flat
        if not img.save(path):
            raise IOError(f"Failed to save image to {path}")

    def to_png_bytes(self) -> bytes:
        img = self.rendered_image()
        pil = qimage_to_pil(img)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return buf.getvalue()

    def rendered_image(self) -> QImage:
        result = self.image.copy()
        if self.floating_image is not None and self.floating_origin is not None:
            p = QPainter(result)
            p.drawImage(self.floating_origin, self.floating_image)
            p.end()
        return result

    def paste_image(self, qimg: QImage):
        self.push_undo()
        self.commit_floating()
        qimg = qimg.convertToFormat(IMG_FORMAT)
        self.floating_image = qimg
        x = max(0, (self.image.width() - qimg.width()) // 2)
        y = max(0, (self.image.height() - qimg.height()) // 2)
        self.floating_origin = QPoint(x, y)
        self.selection_rect = QRect(self.floating_origin, qimg.size())
        self.tool = "select"
        self.update()
        self.modified.emit()

    def copy_selection(self):
        if self.floating_image is not None:
            return self.floating_image.copy()
        if self.selection_rect is not None and self.selection_rect.isValid():
            return self.image.copy(self.selection_rect.intersected(self.image.rect()))
        return None

    def cut_selection(self):
        img = self.copy_selection()
        if img is None:
            return None
        self.push_undo()
        if self.floating_image is not None:
            self.floating_image = None
            self.floating_origin = None
        elif self.selection_rect is not None:
            p = QPainter(self.image)
            p.fillRect(self.selection_rect, self.secondary_color)
            p.end()
        self.selection_rect = None
        self.update()
        self.modified.emit()
        return img

    def commit_floating(self):
        if self.floating_image is not None and self.floating_origin is not None:
            p = QPainter(self.image)
            p.drawImage(self.floating_origin, self.floating_image)
            p.end()
        self.floating_image = None
        self.floating_origin = None

    def delete_selection(self):
        if self.floating_image is not None:
            self.push_undo()
            self.floating_image = None
            self.floating_origin = None
            self.selection_rect = None
            self.update()
            self.modified.emit()
        elif self.selection_rect is not None:
            self.push_undo()
            p = QPainter(self.image)
            p.fillRect(self.selection_rect, self.secondary_color)
            p.end()
            self.selection_rect = None
            self.update()
            self.modified.emit()

    def get_active_region_for_ai(self):
        if self.floating_image is not None:
            return self.floating_image.copy(), True
        if self.selection_rect is not None and self.selection_rect.isValid():
            return self.image.copy(self.selection_rect.intersected(self.image.rect())), False
        return self.image.copy(), False

    def apply_removed_background(self, result_qimage: QImage):
        self.push_undo()
        origin = self.floating_origin if self.floating_origin is not None else (
            self.selection_rect.topLeft() if self.selection_rect is not None else QPoint(0, 0))
        self.commit_floating()
        self.floating_image = result_qimage.convertToFormat(IMG_FORMAT)
        self.floating_origin = origin
        self.selection_rect = QRect(origin, self.floating_image.size())
        self.update()
        self.modified.emit()

    def rotate(self, degrees: float):
        self.push_undo()
        self.commit_floating()
        t = QTransform()
        t.rotate(degrees)
        self.image = self.image.transformed(t, Qt.TransformationMode.SmoothTransformation)
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def flip(self, horizontal: bool):
        self.push_undo()
        self.commit_floating()
        self.image = self.image.mirrored(horizontal, not horizontal)
        self.update()
        self.modified.emit()

    def crop_to_selection(self):
        if self.selection_rect is None or not self.selection_rect.isValid():
            self.status_message.emit("Make a selection first")
            return
        self.commit_floating()
        self.push_undo()
        self.image = self.image.copy(self.selection_rect.intersected(self.image.rect()))
        self.selection_rect = None
        self._resize_widget_to_image()
        self.update()
        self.modified.emit()

    def apply_adjustments(self, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0, commit=True):
        target = self.floating_image if self.floating_image is not None else self.image
        pil = qimage_to_pil(target)
        rgb = pil.convert("RGB")
        alpha = pil.split()[-1]
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
        rgba = rgb.convert("RGBA")
        rgba.putalpha(alpha)
        result = pil_to_qimage(rgba)
        if commit:
            self.push_undo()
            if self.floating_image is not None:
                self.floating_image = result
            else:
                self.image = result
            self.update()
            self.modified.emit()
        return result

    def auto_enhance(self):
        self.push_undo()
        target = self.floating_image if self.floating_image is not None else self.image
        pil = qimage_to_pil(target)
        rgb = pil.convert("RGB")
        alpha = pil.split()[-1]
        rgb = ImageOps.autocontrast(rgb, cutoff=1)
        rgb = ImageEnhance.Color(rgb).enhance(1.15)
        rgb = ImageEnhance.Sharpness(rgb).enhance(1.2)
        rgba = rgb.convert("RGBA")
        rgba.putalpha(alpha)
        result = pil_to_qimage(rgba)
        if self.floating_image is not None:
            self.floating_image = result
        else:
            self.image = result
        self.update()
        self.modified.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        target_rect = self.rect()
        painter.drawImage(target_rect, self.image)

        if self._temp_image is not None:
            painter.drawImage(target_rect, self._temp_image)

        if self.floating_image is not None and self.floating_origin is not None:
            dest = QRectF(self.floating_origin.x() * self.zoom, self.floating_origin.y() * self.zoom,
                           self.floating_image.width() * self.zoom, self.floating_image.height() * self.zoom)
            painter.drawImage(dest, self.floating_image)
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(dest)
        elif self.selection_rect is not None:
            r = QRectF(self.selection_rect.x() * self.zoom, self.selection_rect.y() * self.zoom,
                       self.selection_rect.width() * self.zoom, self.selection_rect.height() * self.zoom)
            pen = QPen(QColor(0, 120, 215), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(r)
        painter.end()

    def mousePressEvent(self, event):
        self.setFocus()
        pos = self.widget_to_image_pt(event.position().toPoint())
        button = event.button()
        color = self.primary_color if button == Qt.MouseButton.LeftButton else self.secondary_color

        if self.tool in ("select", "crop"):
            if self.floating_image is not None and self.floating_origin is not None:
                fr = QRect(self.floating_origin, self.floating_image.size())
                if fr.contains(pos):
                    self._moving_floating = True
                    self._move_offset = pos - self.floating_origin
                    return
                else:
                    self.commit_floating()
            self._selecting = True
            self._start_point = pos
            self.selection_rect = QRect(pos, pos)
            self.update()
            return

        if self.floating_image is not None:
            self.commit_floating()

        self.push_undo()
        self._drawing = True
        self._last_point = pos
        self._start_point = pos
        self._draw_color = color

        if self.tool in ("brush", "pencil", "eraser"):
            self._stroke_point(pos, pos, color)
        elif self.tool in ("line", "rect", "ellipse"):
            self._temp_image = QImage(self.image.size(), IMG_FORMAT)
            self._temp_image.fill(Qt.GlobalColor.transparent)

    def mouseMoveEvent(self, event):
        pos = self.widget_to_image_pt(event.position().toPoint())
        self.status_message.emit(f"x: {pos.x()}, y: {pos.y()}")

        if self._moving_floating and self.floating_image is not None:
            self.floating_origin = pos - self._move_offset
            self.selection_rect = QRect(self.floating_origin, self.floating_image.size())
            self.update()
            return

        if self._selecting:
            self.selection_rect = QRect(self._start_point, pos).normalized()
            self.update()
            return

        if not self._drawing:
            return

        if self.tool in ("brush", "pencil", "eraser"):
            self._stroke_point(self._last_point, pos, self._draw_color)
            self._last_point = pos
        elif self.tool in ("line", "rect", "ellipse"):
            self._temp_image.fill(Qt.GlobalColor.transparent)
            p = QPainter(self._temp_image)
            pen = QPen(self._draw_color, self.pen_width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self.tool == "line":
                p.drawLine(self._start_point, pos)
            elif self.tool == "rect":
                p.drawRect(QRect(self._start_point, pos))
            elif self.tool == "ellipse":
                p.drawEllipse(QRect(self._start_point, pos))
            p.end()
            self.update()

    def mouseReleaseEvent(self, event):
        if self._moving_floating:
            self._moving_floating = False
            self.modified.emit()
            return

        if self._selecting:
            self._selecting = False
            self.modified.emit()
            return

        if not self._drawing:
            return
        self._drawing = False

        if self.tool in ("line", "rect", "ellipse") and self._temp_image is not None:
            p = QPainter(self.image)
            p.drawImage(0, 0, self._temp_image)
            p.end()
            self._temp_image = None
        self.update()
        self.modified.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selection()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.tool == "crop":
            self.crop_to_selection()
        else:
            super().keyPressEvent(event)

    def _stroke_point(self, p1: QPoint, p2: QPoint, color: QColor):
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.tool == "eraser":
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            pen = QPen(Qt.GlobalColor.transparent, self.pen_width * 2,
                       Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        else:
            width = self.pen_width if self.tool == "brush" else max(1, self.pen_width // 3)
            pen = QPen(color, width, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.end()
        self.update()
