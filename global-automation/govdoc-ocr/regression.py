"""Small, reviewable JSONL corpus contract for OCR corrections/regressions."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class RegressionCase:
    case_id: str
    source: str
    expected_text: str
    notes: str = ""

def load_corpus(path: str | Path) -> list[RegressionCase]:
    cases: list[RegressionCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = json.loads(line)
        cases.append(RegressionCase(**item))
    return cases

def save_case(path: str | Path, case: RegressionCase) -> None:
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(case), ensure_ascii=False, sort_keys=True) + "\n")

def exact_match(actual: str, expected: str) -> bool:
    return actual.strip() == expected.strip()
