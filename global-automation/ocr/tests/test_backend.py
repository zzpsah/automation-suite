from ocr.backend import TesseractBackend, get_backend


def test_default_backend_is_tesseract():
    backend = get_backend()
    assert isinstance(backend, TesseractBackend)
    assert backend.name == "tesseract"


def test_unknown_backend_is_rejected():
    try:
        get_backend("unknown")
    except ValueError as exc:
        assert "Unsupported OCR backend" in str(exc)
    else:
        raise AssertionError("Unknown backend must be rejected")
