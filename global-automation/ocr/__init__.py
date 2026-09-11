"""Global Sarkari OCR package."""

from .ocr_engine import extract_document_text, extract_embedded_pdf_text, ocr_image, ocr_image_detailed, render_pdf
from .ocr_service import process_file, process_image, process_pdf
from .sarkari_normalizer import SarkariMetadata, extract_metadata, normalize_sarkari_text
from .backend_policy import choose_backend, choose_from_benchmarks
from .field_confidence import FieldConfidence, score_field, score_fields
from .region_alignment import OCRSpan, align_regions
from .region_consensus import RegionDisagreement, compare_regions
from .text_reconstruction import ReconstructionLine, group_lines, reconstruct_text
from .layout_intelligence import LayoutBlock, TableCell, analyze_layout, detect_columns, detect_table, infer_block_type
from .vision_intelligence import VisualArtifact, detect_visual_artifacts, summarize_visual_intelligence
from .multipage_intelligence import PageStructure, analyze_pages
from .document_structure import DocumentStructure, StructureBlock, build_document_structure, build_page_structure, structure_to_dict

__all__ = [
    "extract_document_text", "extract_embedded_pdf_text", "ocr_image", "ocr_image_detailed", "render_pdf",
    "process_file", "process_image", "process_pdf",
    "SarkariMetadata", "extract_metadata", "normalize_sarkari_text",
    "choose_backend", "choose_from_benchmarks",
    "FieldConfidence", "score_field", "score_fields",
    "OCRSpan", "align_regions", "RegionDisagreement", "compare_regions",
    "ReconstructionLine", "group_lines", "reconstruct_text",
    "LayoutBlock", "TableCell", "analyze_layout", "detect_columns", "detect_table", "infer_block_type",
    "VisualArtifact", "detect_visual_artifacts", "summarize_visual_intelligence",
    "PageStructure", "analyze_pages",
    "DocumentStructure", "StructureBlock", "build_document_structure", "build_page_structure", "structure_to_dict",
]
