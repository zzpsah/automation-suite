"""Create a proposed language-pack revision from reviewed candidates.

Promotion is deliberately explicit: only approved candidates are copied into a
new pack. This module never changes the active pack in place.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .candidate_policy import validate_candidate


def promote(pack_path: str, candidates_path: str, output_path: str) -> dict:
    pack = json.loads(Path(pack_path).read_text(encoding="utf-8"))
    candidates = json.loads(Path(candidates_path).read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        raise ValueError("Candidates must be a JSON list")

    aliases = dict(pack.get("aliases", {}))
    applied = []
    rejected = []
    for item in candidates:
        if item.get("review_status") != "approved":
            continue
        observed = str(item.get("observed", "")).strip()
        correction = str(item.get("correction", "")).strip()
        frequency = int(item.get("frequency", 0) or 0)
        ok, reason = validate_candidate(observed, correction, frequency)
        if not ok:
            rejected.append({"observed": observed, "correction": correction, "reason": reason})
            continue
        aliases[observed] = correction
        applied.append({"observed": observed, "correction": correction, "frequency": frequency})

    old_version = str(pack["version"])
    parts = old_version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"Pack version must be semver-like: {old_version}")
    parts[-1] = str(int(parts[-1]) + 1)
    pack["version"] = ".".join(parts)
    pack["aliases"] = aliases
    pack.setdefault("improvement", {})["previous_version"] = old_version
    pack["improvement"]["promoted_candidates"] = len(applied)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"from": old_version, "to": pack["version"], "applied": len(applied), "rejected": rejected}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pack")
    parser.add_argument("candidates")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(promote(args.pack, args.candidates, args.output), ensure_ascii=False))
