import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ocr.sarkari_normalizer import extract_metadata


def test_bihar_bseb_notice():
    text = '''बिहार विद्यालय परीक्षा समिति
पत्रांक: 123/2026
दिनांक: 25.06.2026
विषय: सत्र 2026-28 के लिए इंटरमीडिएट कक्षा में स्पॉट नामांकन हेतु तिथि विस्तारित करने के संबंध में सूचना
'''
    md = extract_metadata(text)
    assert md.authority == "बिहार विद्यालय परीक्षा समिति"
    assert md.reference_number == "123/2026"
    assert md.issue_date == "25.06.2026"
    assert md.subject.startswith("सत्र 2026-28")
    assert md.category == "admission"
    assert md.confidence == "HIGH"


def test_does_not_invent_missing_fields():
    md = extract_metadata("यह एक सामान्य सरकारी सूचना है।")
    assert md.reference_number is None
    assert md.issue_date is None
    assert md.authority is None


def test_training_corpus():
    corpus = Path(__file__).with_name("training_corpus.jsonl")
    for line in corpus.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        md = extract_metadata(case["text"])
        for field, expected in case["expected"].items():
            assert getattr(md, field) == expected, f"{case['name']}: {field}"
