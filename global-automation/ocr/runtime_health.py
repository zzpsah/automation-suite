"""Read-only production readiness diagnostics for the standalone OCR runtime."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import os


@dataclass(frozen=True)
class HealthCheck:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class RuntimeHealth:
    ok: bool
    checks: tuple[HealthCheck, ...]


def _module_check(name: str, module: str, required: bool) -> HealthCheck:
    available = importlib.util.find_spec(module) is not None
    if available:
        return HealthCheck(name, True, f"{module} available")
    return HealthCheck(name, not required, f"{module} unavailable" + (" (optional)" if not required else ""))


def check_runtime(*, require_tesseract: bool = False, require_paddleocr: bool = False) -> RuntimeHealth:
    """Run side-effect-free checks; optional OCR backends remain optional by default."""
    checks = [
        _module_check("python", "sys", True),
        _module_check("pillow", "PIL", True),
        _module_check("pytesseract", "pytesseract", require_tesseract),
        _module_check("paddleocr", "paddleocr", require_paddleocr),
    ]
    temp_dir = os.getenv("TMPDIR") or os.getenv("TEMP") or os.getenv("TMP")
    checks.append(HealthCheck("temp_environment", True, temp_dir or "system default"))
    return RuntimeHealth(all(item.ok for item in checks), tuple(checks))


def runtime_health_to_dict(health: RuntimeHealth) -> dict:
    return {"ok": health.ok, "checks": [asdict(check) for check in health.checks]}


__all__ = ["HealthCheck", "RuntimeHealth", "check_runtime", "runtime_health_to_dict"]
