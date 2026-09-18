from __future__ import annotations

import json
from pathlib import Path

from audit import append_event
from browseract_adapter import BrowserAct
from checkpoint import Checkpoint, save_checkpoint
from models import ProfileSnapshot


def _prompt_index(browser: BrowserAct, prompt: str) -> int:
    # Always refresh state immediately before asking for the current index.
    print("\n--- CURRENT BROWSER STATE ---")
    print(browser.state())
    raw = input(f"\n{prompt} (current state index, or q to stop safely): ").strip()
    if raw.lower() in {"q", "quit", "stop"}:
        raise KeyboardInterrupt("Operator stopped discovery")
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError("Enter a numeric BrowserAct state index") from exc


def _click_current(browser: BrowserAct, prompt: str) -> None:
    index = _prompt_index(browser, prompt)
    browser.click(index)
    browser.wait_stable()


def _write_snapshot(base: Path, snapshot: ProfileSnapshot) -> Path:
    path = base / f"{snapshot.profile_type}.json"
    path.write_text(
        json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def discover_one(
    browser: BrowserAct,
    student_label: str,
    runtime_dir: Path,
) -> None:
    evidence_dir = runtime_dir / "evidence" / student_label
    checkpoint_path = runtime_dir / "checkpoints" / f"{student_label}.json"
    audit_path = runtime_dir / "audit" / "events.jsonl"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    cp = Checkpoint(student_label=student_label, last_completed_step="AUTHENTICATED_PAGE")
    save_checkpoint(checkpoint_path, cp)
    append_event(audit_path, "discovery_started", student_label=student_label)

    # Capture authenticated starting evidence. No mutation.
    start = browser.capture()
    (evidence_dir / "authenticated-start.json").write_text(
        json.dumps(start, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _click_current(
        browser,
        "Choose the CURRENT index that opens the ONE test student's profile",
    )
    cp.last_completed_step = "STUDENT_OPENED"
    save_checkpoint(checkpoint_path, cp)
    append_event(audit_path, "test_student_opened", student_label=student_label)

    for profile_type, display in (
        ("general", "General Profile (GP)"),
        ("education", "Education Profile (EP)"),
        ("facility", "Facility Profile (FP)"),
    ):
        _click_current(
            browser,
            f"Choose the CURRENT index that opens {display}",
        )
        evidence = browser.capture()
        snapshot = ProfileSnapshot.create(
            profile_type=profile_type,
            student_label=student_label,
            page_state=evidence["state"],
            page_markdown=evidence["markdown"],
        )
        path = _write_snapshot(evidence_dir, snapshot)

        setattr(cp, f"{profile_type}_status", "CAPTURED")
        cp.last_completed_step = f"{profile_type.upper()}_CAPTURED"
        save_checkpoint(checkpoint_path, cp)
        append_event(
            audit_path,
            "profile_captured",
            student_label=student_label,
            profile_type=profile_type,
            evidence_file=str(path),
        )

    cp.last_completed_step = "DISCOVERY_COMPLETE"
    save_checkpoint(checkpoint_path, cp)
    append_event(audit_path, "discovery_complete", student_label=student_label)

    print(f"\nRead-only discovery complete for {student_label}.")
    print(f"Evidence: {evidence_dir}")
    print(f"Checkpoint: {checkpoint_path}")
