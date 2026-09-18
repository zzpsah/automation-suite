from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Checkpoint:
    student_label: str
    last_completed_step: str
    general_status: str = "PENDING"
    education_status: str = "PENDING"
    facility_status: str = "PENDING"
    issue_count: int = 0
    updated_at: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def load_checkpoint(path: Path, student_label: str) -> Checkpoint:
    if not path.exists():
        cp = Checkpoint(student_label=student_label, last_completed_step="START")
        cp.touch()
        return cp
    data = json.loads(path.read_text(encoding="utf-8"))
    return Checkpoint(**data)


def save_checkpoint(path: Path, checkpoint: Checkpoint) -> None:
    checkpoint.touch()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(asdict(checkpoint), indent=2), encoding="utf-8")
    tmp.replace(path)
