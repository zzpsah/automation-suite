"""Future VLM adapter contract.

The class intentionally contains no provider SDK. A future local/open VLM can
implement this interface without changing consumer code.
"""
from ..backend import OCRResult


class VLMBackend:
    name = "vlm"

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError(
            "VLM backend is an extension point; register a pinned implementation "
            "only after contract tests and benchmark validation."
        )

    def extract_image(self, image_path: str, *, language: str = "hin+eng", psm: int = 6) -> OCRResult:
        raise NotImplementedError

__all__ = ["VLMBackend"]
