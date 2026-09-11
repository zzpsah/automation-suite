#!/usr/bin/env python3
"""Production entrypoint: existing pipeline + shared GovDOC OCR Engine."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.document import document_processor
from scripts.document.govdoc_ocr_adapter import install

install(document_processor)
sys.exit(document_processor.main())
