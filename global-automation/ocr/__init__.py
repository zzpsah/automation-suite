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
from .reading_order import ReadingOrderBlock, optimize_reading_order
from .section_intelligence import SectionBoundary, detect_section_boundaries, section_boundaries_to_dict
from .table_schema import StructuredTableCell, StructuredTable, build_table, table_to_dict
from .structure_graph import StructureNode, StructureEdge, StructureGraph, build_structure_graph, structure_graph_to_dict
from .document_understanding import UnderstandingEntity, UnderstandingRelation, DocumentUnderstandingGraph, build_understanding_graph, understanding_graph_to_dict
from .intelligent_reconstruction import ReconstructedBlock, ReconstructedDocument, reconstruct_document, reconstruct_markdown, reconstructed_to_dict
from .cross_document import CrossDocumentRelation, CrossDocumentGraph, build_cross_document_graph, cross_document_graph_to_dict
from .document_clustering import CandidateCluster, CandidateClusterResult, build_candidate_clusters, candidate_clusters_to_dict
from .search_index import SearchDocument, SearchEntity, SearchHit, DocumentSearchIndex, build_search_index, normalize_query, search_to_dict
from .search_filters import SearchFilter, filter_hits, filter_to_dict
from .search_contract import SearchStore, search_with_filter
from .reference_timeline import TimelineEvent, ReferenceTimeline, build_reference_timeline, reference_timeline_to_dict
from .persistent_search import SQLiteSearchStore
from .evidence_relations import EvidenceRelation, extract_evidence_relations, evidence_relations_to_dict
from .runtime_health import HealthCheck, RuntimeHealth, check_runtime, runtime_health_to_dict

__all__ = [
    "extract_document_text", "extract_embedded_pdf_text", "ocr_image", "ocr_image_detailed", "render_pdf",
    "process_file", "process_image", "process_pdf", "SarkariMetadata", "extract_metadata", "normalize_sarkari_text",
    "choose_backend", "choose_from_benchmarks", "FieldConfidence", "score_field", "score_fields",
    "OCRSpan", "align_regions", "RegionDisagreement", "compare_regions", "ReconstructionLine", "group_lines", "reconstruct_text",
    "LayoutBlock", "TableCell", "analyze_layout", "detect_columns", "detect_table", "infer_block_type", "VisualArtifact", "detect_visual_artifacts", "summarize_visual_intelligence",
    "PageStructure", "analyze_pages", "DocumentStructure", "StructureBlock", "build_document_structure", "build_page_structure", "structure_to_dict",
    "ReadingOrderBlock", "optimize_reading_order", "SectionBoundary", "detect_section_boundaries", "section_boundaries_to_dict",
    "StructuredTableCell", "StructuredTable", "build_table", "table_to_dict", "StructureNode", "StructureEdge", "StructureGraph", "build_structure_graph", "structure_graph_to_dict",
    "UnderstandingEntity", "UnderstandingRelation", "DocumentUnderstandingGraph", "build_understanding_graph", "understanding_graph_to_dict",
    "ReconstructedBlock", "ReconstructedDocument", "reconstruct_document", "reconstruct_markdown", "reconstructed_to_dict",
    "CrossDocumentRelation", "CrossDocumentGraph", "build_cross_document_graph", "cross_document_graph_to_dict",
    "CandidateCluster", "CandidateClusterResult", "build_candidate_clusters", "candidate_clusters_to_dict",
    "SearchDocument", "SearchEntity", "SearchHit", "DocumentSearchIndex", "build_search_index", "normalize_query", "search_to_dict",
    "SearchFilter", "filter_hits", "filter_to_dict", "SearchStore", "search_with_filter",
    "TimelineEvent", "ReferenceTimeline", "build_reference_timeline", "reference_timeline_to_dict", "SQLiteSearchStore",
    "EvidenceRelation", "extract_evidence_relations", "evidence_relations_to_dict",
    "HealthCheck", "RuntimeHealth", "check_runtime", "runtime_health_to_dict",
]
