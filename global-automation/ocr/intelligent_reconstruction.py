"""Evidence-preserving graph-aware document reconstruction."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .document_structure import StructureBlock
from .structure_graph import StructureGraph


@dataclass(frozen=True)
class ReconstructedBlock:
    block_id: str
    page_number: int
    block_type: str
    text: str
    source_block_ids: tuple[str, ...]
    section: str | None = None


@dataclass(frozen=True)
class ReconstructedDocument:
    blocks: tuple[ReconstructedBlock, ...]


def reconstruct_document(
    blocks: Iterable[StructureBlock],
    *,
    structure_graph: StructureGraph | None = None,
) -> ReconstructedDocument:
    """Merge only explicit continuation edges; preserve source IDs and text."""
    source = {b.block_id: b for b in blocks}
    ordered = list(blocks)
    if structure_graph:
        rank = {node_id: i for i, node_id in enumerate(structure_graph.nodes)}
        ordered.sort(key=lambda b: (b.page_number, rank.get(b.block_id, 10**9), b.y, b.x, b.block_id))
        continuation = {e.source_id: e.target_id for e in structure_graph.edges if e.edge_type == "continuation" and e.source_id in source and e.target_id in source}
    else:
        ordered.sort(key=lambda b: (b.page_number, b.y, b.x, b.block_id))
        continuation = {}

    consumed: set[str] = set()
    result: list[ReconstructedBlock] = []
    for block in ordered:
        if block.block_id in consumed:
            continue
        chain = [block]
        consumed.add(block.block_id)
        current = block.block_id
        while current in continuation and continuation[current] in source and continuation[current] not in consumed:
            nxt = source[continuation[current]]
            chain.append(nxt)
            consumed.add(nxt.block_id)
            current = nxt.block_id
        result.append(ReconstructedBlock(
            block_id=block.block_id,
            page_number=block.page_number,
            block_type=block.block_type,
            text="\n".join(item.text for item in chain),
            source_block_ids=tuple(item.block_id for item in chain),
        ))
    return ReconstructedDocument(tuple(result))


def reconstruct_markdown(document: ReconstructedDocument) -> str:
    """Render reconstructed blocks without changing their source wording."""
    output: list[str] = []
    for block in document.blocks:
        if block.block_type in {"header", "footer"}:
            continue
        if block.block_type in {"heading", "section", "annexure", "attachment"}:
            output.append(f"## {block.text}")
        elif block.block_type == "table":
            output.append(block.text)
        else:
            output.append(block.text)
    return "\n\n".join(part for part in output if part.strip())


def reconstructed_to_dict(document: ReconstructedDocument) -> dict:
    return {"blocks": [asdict(block) for block in document.blocks]}


__all__ = ["ReconstructedBlock", "ReconstructedDocument", "reconstruct_document", "reconstruct_markdown", "reconstructed_to_dict"]
