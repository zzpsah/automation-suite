from ocr.document_structure import StructureBlock
from ocr.document_understanding import build_understanding_graph, understanding_graph_to_dict


def test_extracts_reference_date_and_authority_without_mutating_source():
    block = StructureBlock("p1-b1", "body", "District Education Officer, Ref: ABC/123 dated 12/09/2026", 1, 0.9, x=10, y=10, width=500, height=30)
    graph = build_understanding_graph([block])
    assert {e.entity_type for e in graph.entities} >= {"reference", "date", "authority"}
    assert block.text == "District Education Officer, Ref: ABC/123 dated 12/09/2026"


def test_relates_entities_across_structure_continuity():
    from ocr.structure_graph import StructureEdge, StructureGraph, StructureNode
    first = StructureBlock("p1-b1", "body", "Ref: ABC/123", 1, 0.9, x=0, y=0, width=100, height=20)
    second = StructureBlock("p2-b1", "body", "Ref: ABC/123", 2, 0.9, x=0, y=0, width=100, height=20)
    structure = StructureGraph(
        nodes=(StructureNode("p1-b1", "block", 1, "p1-b1", "body", .9), StructureNode("p2-b1", "block", 2, "p2-b1", "body", .9)),
        edges=(StructureEdge("p1-b1", "p2-b1", "entity_continuity", .8, "shared_meaningful_tokens=1"),),
    )
    graph = build_understanding_graph([first, second], structure)
    assert any(r.relation_type == "entity_continuity" for r in graph.relations)
    payload = understanding_graph_to_dict(graph)
    assert payload["entities"] and payload["relations"]
