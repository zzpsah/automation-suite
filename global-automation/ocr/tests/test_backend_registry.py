from ocr.backend_registry import capabilities, list_backends, resolve_backend


def test_registry_is_deterministic():
    assert [item.name for item in list_backends()] == ["tesseract"]


def test_tesseract_advertises_hindi_and_english():
    caps = capabilities("tesseract")
    assert "hin+eng" in caps.languages
    assert "eng" in caps.languages
    assert "hin" in caps.languages


def test_resolver_honors_compatible_preference():
    assert resolve_backend(language="hin+eng", preferred="tesseract").name == "tesseract"


def test_unknown_backend_fails_closed():
    try:
        capabilities("unknown")
    except ValueError as exc:
        assert "Unsupported OCR backend" in str(exc)
    else:
        raise AssertionError("unknown backend must fail")
