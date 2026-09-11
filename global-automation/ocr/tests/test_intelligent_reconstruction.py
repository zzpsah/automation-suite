from ocr.document_structure import StructureBlock
from ocr.intelligent_reconstruction import reconstruct_document, reconstruct_markdown
from ocr.structure_graph import StructureEdge, StructureGraph, StructureNode


def test_reconstructs_only_explicit_continuation_chain_and_preserves_source_ids():
    a = StructureBlock("p1-b1", "body", "पहला भाग", 1, .9, x=0, y=0, width=100, height=20)
    b = StructureBlock("p2-b1", "body", "दूसरा भाग", 2, .9, x=0, y=0, width=100, height=20)
    graph = StructureGraph(
        nodes=(StructureNode(a.block_id, "block", 1, a.block_id, "body", .9), StructureNode(b.block_id, "block", 2, b.block_id, "body", .9)),
        edges=(StructureEdge(a.block_id, b.block_id, "continuation", .8, "explicit"),),
    )
    doc = reconstruct_document([a, b], structure_graph=graph)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].source_block_ids == ("p1-b1", "p2-b1")
    assert doc.blocks[0].text == "पहला भाग\nदूसरा भाग"


def test_headers_and_footers_are_excluded_from_markdown():
    header = StructureBlock("p1-h", "header", "Department Header", 1, .9)
    body = StructureBlock("p1-b", "body", "Main order", 1, .9)
    footer = StructureBlock("p1-f", "footer", "Page 1", 1, .9)
    output = reconstruct_markdown(reconstruct_document([header, body, footer]))
    assert output == "Main order"
    assert "Page 1" not in output
