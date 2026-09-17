import json
from pathlib import Path

from ocr.training.candidate_miner import mine_token_corrections
from ocr.training.collector import collect_records
from ocr.training.train_pipeline import run


def test_candidate_miner_requires_repeat_evidence():
    records = [
        {"raw_text": "विधालय", "corrected_text": "विद्यालय"},
        {"raw_text": "विधालय", "corrected_text": "विद्यालय"},
        {"raw_text": "विधालय", "corrected_text": "विद्यालय"},
    ]
    assert mine_token_corrections(records) == [{"raw": "विधालय", "corrected": "विद्यालय", "count": 3}]


def test_pipeline_does_not_modify_runtime_files(tmp_path: Path):
    source = tmp_path / "reviewed.jsonl"
    source.write_text(json.dumps({"id": "1", "raw_text": "विधालय", "corrected_text": "विद्यालय"}, ensure_ascii=False) + "\n", encoding="utf-8")
    result = run([str(source)], str(tmp_path / "artifacts"))
    assert result["runtime_files_modified"] is False
    assert (tmp_path / "artifacts" / "training_report.json").exists()


def test_collector_skips_empty_corrections(tmp_path: Path):
    source = tmp_path / "x.jsonl"
    source.write_text('{"id":"1","raw_text":"x","corrected_text":""}\n', encoding="utf-8")
    assert collect_records([str(source)]) == []
