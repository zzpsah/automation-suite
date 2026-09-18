import importlib.util
import unittest
from pathlib import Path


class GuiImportTests(unittest.TestCase):
    def test_gui_module_is_importable(self):
        path = Path(__file__).resolve().parents[1] / "gui.py"
        spec = importlib.util.spec_from_file_location("udise_student_profile_gui", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)


if __name__ == "__main__":
    unittest.main()
