import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from compare import compare_value


class CompareTests(unittest.TestCase):
    def test_exact_match(self):
        row = compare_value(
            profile_type="general",
            field_key="father_name",
            label="Father Name",
            portal_value="IMAM HASAN",
            source_value="IMAM HASAN",
        )
        self.assertEqual(row.status, "MATCH")

    def test_minor_format_variation(self):
        row = compare_value(
            profile_type="general",
            field_key="student_name",
            label="Student Name",
            portal_value="TABBU-KHATOON",
            source_value="Tabbu Khatoon",
        )
        self.assertEqual(row.status, "MINOR_VARIATION")

    def test_missing_portal_value(self):
        row = compare_value(
            profile_type="education",
            field_key="stream",
            label="Stream",
            portal_value="",
            source_value="Science",
        )
        self.assertEqual(row.status, "MISSING_IN_PORTAL")
        self.assertEqual(row.proposed_value, "Science")


if __name__ == "__main__":
    unittest.main()
