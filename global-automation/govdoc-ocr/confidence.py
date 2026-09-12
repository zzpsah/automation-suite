"""Transparent confidence aggregation; never treats confidence as approval."""
from __future__ import annotations
from statistics import mean


def aggregate_confidence(regions: list[dict]) -> dict:
    values = [float(r["confidence"]) for r in regions if r.get("confidence") is not None]
    return {
        "region_count": len(regions),
        "scored_region_count": len(values),
        "mean": mean(values) if values else None,
        "minimum": min(values) if values else None,
        "signals": {"has_confidence": bool(values), "low_confidence": bool(values) and mean(values) < 0.70},
        "approval": False,
    }
