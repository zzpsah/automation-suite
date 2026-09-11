from hashlib import sha256

import pytest

from ocr.artifact_verification import ArtifactSpec, artifact_to_dict, verify_artifact


def test_verify_artifact(tmp_path):
    target = tmp_path / "model.bin"
    target.write_bytes(b"trusted-model")
    digest = sha256(b"trusted-model").hexdigest()
    spec = ArtifactSpec("ocr-model", "1.2.3", digest, len(b"trusted-model"))
    assert verify_artifact(target, spec)
    assert artifact_to_dict(spec)["version"] == "1.2.3"


def test_tamper_or_missing_fails(tmp_path):
    target = tmp_path / "model.bin"
    target.write_bytes(b"trusted-model")
    spec = ArtifactSpec("ocr-model", "1.2.3", sha256(b"trusted-model").hexdigest())
    target.write_bytes(b"tampered")
    assert not verify_artifact(target, spec)
    assert not verify_artifact(tmp_path / "missing.bin", spec)


def test_invalid_version_and_digest_fail_closed(tmp_path):
    with pytest.raises(ValueError):
        ArtifactSpec("ocr", "latest", "0" * 64)
        verify_artifact(tmp_path / "x", ArtifactSpec("ocr", "latest", "0" * 64))
    with pytest.raises(ValueError):
        verify_artifact(tmp_path / "x", ArtifactSpec("ocr", "1.0.0", "bad"))
