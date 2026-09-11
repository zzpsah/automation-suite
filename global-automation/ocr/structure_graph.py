"""Evidence-preserving multi-page document structure graph."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from difflib import SequenceMatcher
from typing import Iterable

from .document_structure import StructureBlock
from .section_intelligence import SectionBoundary

_TOKEN_RE = re.compile(r"[\w\u0900-\u097F]+", re.UNICODE)
_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "this", "that", "page", "of", "to",
    "में", "का", "के", "की", "और", "से", "को", "यह", "वह", "पर", "एक",
})


@dataclass(frozen=True)
class StructureNode:
    node_id: str
    node_type: str
    page_number: int
    block_id: str | None
    label: str
    confidence: float


@dataclass(frozen=True)
class StructureEdge:
    source_id: str
    target_id: str
    edge_type: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class StructureGraph:
    nodes: tuple[StructureNode, ...]
    edges: tuple[StructureEdge, ...]


def _tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(text)
        if len(token) >= 3 and token.casefold() not in _STOPWORDS
    }


def _similarity(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return 0.0
    jaccard = len(a & b) / len(a | b)
    sequence = SequenceMatcher(None, left.casefold(), right.casefold()).ratio()
    return max(jaccard, sequence)


def _meaningful(block: StructureBlock) -> bool:
    return bool(block.text.strip()) and block.block_type not in {"header", "footer"}


def build_structure_graph(
    blocks: Iterable[StructureBlock],
    boundaries: Iterable[SectionBoundary] = (),
    *,
    min_shared_tokens: int = 1,
    min_similarity: float = 0.35,
) -> StructureGraph:
    """Build a deterministic graph using only explicit blocks and boundaries.

    Cross-page relationships are intentionally conservative and only connect
    adjacent pages. The graph is derived intelligence; source OCR is untouched.
    """
    if min_shared_tokens < 1:
        raise ValueError("min_shared_tokens must be at least 1")
    if not 0.0 <= min_similarity <= 1.0:
        raise ValueError("min_similarity must be between 0 and 1")

    source_blocks = tuple(sorted(blocks, key=lambda b: (b.page_number, b.y, b.x, b.block_id)))
    boundary_items = tuple(sorted(boundaries, key=lambda b: (b.page_number, b.block_id, b.boundary_id)))

    nodes = [
        StructureNode(b.block_id, "block", b.page_number, b.block_id, b.block_type, round(b.confidence, 2))
        for b in source_blocks
    ]
    block_by_id = {b.block_id: b for b in source_blocks}

    edges: list[StructureEdge] = []
    page_groups: dict[int, list[StructureBlock]] = {}
    for block in source_blocks:
        page_groups.setdefault(block.page_number, []).append(block)

    for boundary in boundary_items:
        node_id = f"boundary:{boundary.boundary_id}"
        nodes.append(StructureNode(
            node_id, boundary.boundary_type, boundary.page_number,
            boundary.block_id, boundary.label, round(boundary.confidence, 2),
        ))
        if boundary.block_id in block_by_id:
            edges.append(StructureEdge(
                node_id, boundary.block_id, boundary.boundary_type,
                round(boundary.confidence, 2), "explicit boundary marker",
            ))

    pages = sorted(page_groups)
    for page_number in pages:
        next_page = page_number + 1
        if next_page not in page_groups:
            continue
        left = [b for b in page_groups[page_number] if _meaningful(b)]
        right = [b for b in page_groups[next_page] if _meaningful(b)]
        if not left or not right:
            continue
        previous = max(left, key=lambda b: (b.y + b.height, b.x, b.block_id))
        following = min(right, key=lambda b: (b.y, b.x, b.block_id))
        shared = _tokens(previous.text) & _tokens(following.text)
        similarity = _similarity(previous.text, following.text)
        if len(shared) >= min_shared_tokens and similarity >= min_similarity:
            confidence = round(min(0.95, 0.35 + 0.25 * min(len(shared), 3) + 0.4 * similarity), 2)
            edges.append(StructureEdge(
                previous.block_id,
                following.block_id,
                "continuation",
                confidence,
                f"adjacent pages; shared_tokens={len(shared)}; similarity={similarity:.2f}",
            ))
            if shared:
                edges.append(StructureEdge(
                    previous.block_id,
                    following.block_id,
                    "entity_continuity",
                    round(min(0.9, 0.3 + 0.2 * min(len(shared), 3) + 0.5 * similarity), 2),
                    f"shared_meaningful_tokens={len(shared)}",
                ))

    for boundary in boundary_items:
        if boundary.boundary_type in {"section", "annexure", "attachment"} and boundary.block_id in block_by_id:
            block = block_by_id[boundary.block_id]
            previous_page_blocks = [b for b in page_groups.get(block.page_number - 1, ()) if _meaningful(b)]
            if previous_page_blocks:
                previous = max(previous_page_blocks, key=lambda b: (b.y + b.height, b.x, b.block_id))
                edges.append(StructureEdge(
                    previous.block_id,
                    boundary.block_id,
                    f"{boundary.boundary_type}_continuation",
                    round(min(0.9, boundary.confidence), 2),
                    "explicit boundary follows previous page",
                ))

    nodes = sorted(nodes, key=lambda n: (n.page_number, n.node_type, n.node_id))
    edges = sorted(edges, key=lambda e: (e.source_id, e.target_id, e.edge_type, e.reason))
    return StructureGraph(tuple(nodes), tuple(edges))


def structure_graph_to_dict(graph: StructureGraph) -> dict:
    """Serialize graph objects to JSON-safe dictionaries."""
    return {
        "nodes": [asdict(node) for node in graph.nodes],
        "edges": [asdict(edge) for edge in graph.edges],
    }


__all__ = ["StructureNode", "StructureEdge", "StructureGraph", "build_structure_graph", "structure_graph_to_dict"]
