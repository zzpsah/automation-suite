"""Conservative visual intelligence for government-document artifacts.

This layer labels OCR regions that may contain handwriting, signatures, stamps,
seals, or other non-body marks. It is deliberately heuristic: it never treats
a visual label as proof of authorship, approval, authenticity, or validity.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .region_alignment import OCRSpan


@dataclass(frozen=True)
class VisualArtifact:
    artifact_type: str
    x: float
    y: float
    width: float
    height: float
    confidence: float
    reason: str


def _ink_density(span: OCRSpan) -> float:
    # Geometry-only proxy. Actual pixels are intentionally handled by a future
    # optional vision backend; this function remains deterministic and safe.
    area = max(1.0, span.width * span.height)
    return min(1.0, max(0.0, len(span.text.strip()) / area * 12.0))


def detect_visual_artifacts(spans: list[OCRSpan], *, page_width: float | None = None, page_height: float | None = None) -> list[VisualArtifact]:
    """Identify conservative artifact candidates from OCR geometry/text.

    The current baseline uses geometry and textual signals only. It should be
    treated as a routing signal, not a vision verdict.
    """
    if not spans:
        return []
    typical_height = median(max(1.0, s.height) for s in spans)
    artifacts: list[VisualArtifact] = []
    for span in sorted(spans, key=lambda s: (s.y, s.x, s.text)):
        text = span.text.strip()
        lower = text.casefold()
        short = len(text) <= 28
        edge = bool(page_width and (span.x < page_width * .08 or span.right > page_width * .92))
        bottom = bool(page_height and span.bottom > page_height * .78)
        compact = span.width < typical_height * 7
        if short and compact and (bottom or edge) and any(k in lower for k in ("sign", "हस्ताक्षर", "हस्ता", "sd", "ह०", "s/d")):
            artifacts.append(VisualArtifact("signature", span.x, span.y, span.width, span.height, 0.65, "signature-like label in a compact page-edge region"))
        elif short and compact and any(k in lower for k in ("stamp", "seal", "मुहर", "मोहर", "सील")):
            artifacts.append(VisualArtifact("stamp_or_seal", span.x, span.y, span.width, span.height, 0.70, "stamp/seal terminology detected"))
        elif short and compact and any(k in lower for k in ("दिनांक", "date", "हस्ताक्षर")) and _ink_density(span) < 0.05:
            artifacts.append(VisualArtifact("annotation_area", span.x, span.y, span.width, span.height, 0.45, "compact annotation-like region"))
    return artifacts


def summarize_visual_intelligence(spans: list[OCRSpan], *, page_width: float | None = None, page_height: float | None = None) -> dict:
    artifacts = detect_visual_artifacts(spans, page_width=page_width, page_height=page_height)
    counts: dict[str, int] = {}
    for artifact in artifacts:
        counts[artifact.artifact_type] = counts.get(artifact.artifact_type, 0) + 1
    return {
        "artifact_count": len(artifacts),
        "artifact_types": counts,
        "artifacts": [a.__dict__ for a in artifacts],
        "review_required": any(a.confidence < 0.60 for a in artifacts),
    }


__all__ = ["VisualArtifact", "detect_visual_artifacts", "summarize_visual_intelligence"]
