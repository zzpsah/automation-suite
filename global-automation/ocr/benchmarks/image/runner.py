"""Run image preprocessing benchmark cases without storing source pixels."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from ocr.preprocessing.image import analyze_image, prepare_variants

from .metrics import image_metrics, metric_delta


def run_case(image_path: str, *, strategy: str = "auto") -> dict[str, Any]:
    """Benchmark one image and return JSON-serializable diagnostics."""
    source = Path(image_path)
    if not source.is_file():
        raise FileNotFoundError(source)

    before = analyze_image(str(source))
    with TemporaryDirectory(prefix="ocr-image-benchmark-") as work:
        variants = prepare_variants(str(source), work, strategy=strategy)
        with Image.open(source) as original:
            source_metrics = image_metrics(original)
        variant_results = []
        for variant in variants:
            with Image.open(variant) as processed:
                after = image_metrics(processed)
            variant_results.append({
                "path": Path(variant).name,
                "metrics": after,
                "delta": metric_delta(source_metrics, after),
            })

    return {
        "case": source.name,
        "input_profile": before,
        "variants": variant_results,
    }


def run_manifest(manifest_path: str) -> list[dict[str, Any]]:
    """Run all cases in a JSONL manifest.

    Each non-empty line must contain ``{"image": "path", "strategy": "auto"}``.
    """
    results = []
    for line_number, line in enumerate(Path(manifest_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        if "image" not in case:
            raise ValueError(f"manifest line {line_number}: missing image")
        results.append(run_case(case["image"], strategy=case.get("strategy", "auto")))
    return results
