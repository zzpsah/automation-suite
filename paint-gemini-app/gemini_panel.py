"""
gemini_panel.py — Dockable sidebar that chats with Google Gemini
(gemini-2.5-flash) and can optionally attach the current canvas as a PNG.
"""
import os
from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                              QPushButton, QCheckBox, QLabel, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class GeminiWorker(QThread):
    finished_ok = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, api_key: str, prompt: str, image_bytes, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.prompt = prompt
        self.image_bytes = image_bytes

    def run(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            self.failed.emit(
                "The 'google-genai' package is not installed.\nRun: pip install google-genai")
            return
        try:
            client = genai.Client(api_key=self.api_key)
            contents = []
            if self.image_bytes is not None:
                contents.append(types.Part.from_bytes(data=self.image_bytes, mime_type="image/png"))
            contents.append(self.prompt)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
            )
            text = response.text if response.text else "(No text in response)"
            self.finished_ok.emit(text)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class GeminiPanel(QDockWidget):
    def __init__(self, canvas_provider, parent=None):
        """canvas_provider: zero-arg callable returning current canvas as PNG bytes."""
        super().__init__("Gemini AI Assistant", parent)
        self.canvas_provider = canvas_provider
        self.worker = None

        container = QWidget()
        layout = QVBoxLayout(container)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        env_key = os.environ.get("GEMINI_API_KEY", "")
        if env_key:
            self.api_key_edit.setText(env_key)
            self.api_key_edit.setPlaceholderText("Using GEMINI_API_KEY from environment")
        else:
            self.api_key_edit.setPlaceholderText("Enter Gemini API key")
        key_row.addWidget(self.api_key_edit)
        layout.addLayout(key_row)

        self.send_canvas_checkbox = QCheckBox("Send canvas image with message")
        self.send_canvas_checkbox.setChecked(True)
        layout.addWidget(self.send_canvas_checkbox)

        self.chat_list = QListWidget()
        self.chat_list.setWordWrap(True)
        layout.addWidget(self.chat_list, stretch=1)

        input_row = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Ask Gemini about your drawing...")
        self.input_edit.returnPressed.connect(self.send_message)
        input_row.addWidget(self.input_edit)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        self.setWidget(container)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

    def _append_message(self, sender: str, text: str):
        item = QListWidgetItem(f"{sender}: {text}")
        if sender == "You":
            item.setForeground(Qt.GlobalColor.darkBlue)
        elif sender == "System":
            item.setForeground(Qt.GlobalColor.darkRed)
        else:
            item.setForeground(Qt.GlobalColor.darkGreen)
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def send_message(self):
        prompt = self.input_edit.text().strip()
        if not prompt:
            return
        api_key = self.api_key_edit.text().strip() or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            self._append_message("System", "Please enter a Gemini API key or set GEMINI_API_KEY.")
            return

        self._append_message("You", prompt)
        self.input_edit.clear()

        image_bytes = None
        if self.send_canvas_checkbox.isChecked():
            image_bytes = self.canvas_provider()

        self.send_button.setEnabled(False)
        self._append_message("Gemini", "Thinking...")
        self.worker = GeminiWorker(api_key, prompt, image_bytes)
        self.worker.finished_ok.connect(self._on_response)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _remove_last_message(self):
        count = self.chat_list.count()
        if count > 0:
            self.chat_list.takeItem(count - 1)

    def _on_response(self, text: str):
        self._remove_last_message()
        self._append_message("Gemini", text)
        self.send_button.setEnabled(True)

    def _on_error(self, error: str):
        self._remove_last_message()
        self._append_message("System", f"Error: {error}")
        self.send_button.setEnabled(True)
