"""
bg_remover.py — Runs `rembg` (local U2-Net model) on a background thread so
the UI never freezes while the model loads/runs.
"""
import io
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from PIL import Image


class BackgroundRemovalWorker(QThread):
    finished_ok = pyqtSignal(QImage)
    failed = pyqtSignal(str)

    def __init__(self, qimage: QImage, parent=None):
        super().__init__(parent)
        self.qimage = qimage.copy()

    def run(self):
        try:
            from rembg import remove
        except ImportError:
            self.failed.emit(
                "The 'rembg' package is not installed.\nRun: pip install rembg onnxruntime")
            return
        try:
            pil_in = self._qimage_to_pil(self.qimage)
            buf = io.BytesIO()
            pil_in.save(buf, format="PNG")
            out_bytes = remove(buf.getvalue())
            pil_out = Image.open(io.BytesIO(out_bytes)).convert("RGBA")
            result = self._pil_to_qimage(pil_out)
            self.finished_ok.emit(result)
        except Exception as e:  # noqa: BLE001 - surface any failure to the UI
            self.failed.emit(str(e))

    @staticmethod
    def _qimage_to_pil(qimage: QImage) -> Image.Image:
        qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        ptr.setsize(h * qimage.bytesPerLine())
        buf = bytes(ptr)
        img = Image.frombuffer("RGBA", (w, h), buf, "raw", "RGBA", qimage.bytesPerLine(), 1)
        return img.copy()

    @staticmethod
    def _pil_to_qimage(pil_img: Image.Image) -> QImage:
        pil_img = pil_img.convert("RGBA")
        data = pil_img.tobytes("raw", "RGBA")
        qimage = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        return qimage.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
