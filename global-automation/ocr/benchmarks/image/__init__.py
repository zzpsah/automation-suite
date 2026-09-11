"""Image-processing benchmark API."""

from .degradations import DegradationSpec, apply_degradation
from .metrics import image_metrics, metric_delta
from .runner import run_case, run_manifest

__all__ = [
    "DegradationSpec",
    "apply_degradation",
    "image_metrics",
    "metric_delta",
    "run_case",
    "run_manifest",
]
