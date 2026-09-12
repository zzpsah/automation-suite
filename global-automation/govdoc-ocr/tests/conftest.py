"""Test compatibility bootstrap for the legacy hyphenated source tree.

The production import name is ``govdoc_ocr``. A small set of historical tests
still import modules by their old top-level names; alias those modules to the
package implementations before pytest imports test modules.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

import govdoc_ocr
from govdoc_ocr import backend, government_document, search
from govdoc_ocr.language_packs import bihar_office_resolver

sys.modules.setdefault("backend", backend)
sys.modules.setdefault("government_document", government_document)
sys.modules.setdefault("search", search)
sys.modules.setdefault("language_packs", govdoc_ocr.language_packs)
sys.modules.setdefault("language_packs.bihar_office_resolver", bihar_office_resolver)
