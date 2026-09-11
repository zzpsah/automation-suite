from ocr.cross_document import build_cross_document_graph, cross_document_graph_to_dict
from ocr.document_understanding import DocumentUnderstandingGraph, UnderstandingEntity


def graph(doc, entities):
    return DocumentUnderstandingGraph(tuple(entities), ())


def entity(kind, value, block):
    return UnderstandingEntity(f"{kind}:{block}:1", kind, value, 1, block, 0.9)


def test_shared_reference_creates_cross_document_relation():
    result = build_cross_document_graph({
        "doc-a": graph("doc-a", [entity("reference", "REF/123", "p1-b1")]),
        "doc-b": graph("doc-b", [entity("reference", " ref/123 ", "p2-b1")]),
    })
    assert len(result.relations) == 1
    relation = result.relations[0]
    assert relation.relation_type == "shared_reference"
    assert relation.source_document_id == "doc-a"
    assert relation.target_document_id == "doc-b"
    assert relation.source_entity_id.endswith("p1-b1:1")
    assert relation.target_entity_id.endswith("p2-b1:1")


def test_shared_authority_and_email_are_supported():
    result = build_cross_document_graph({
        "a": graph("a", [entity("authority", "District Education Officer", "p1-b1"), entity("email", "office@example.gov", "p1-b2")]),
        "b": graph("b", [entity("authority", " district   education officer ", "p1-b1"), entity("email", "OFFICE@example.gov", "p1-b2")]),
    })
    assert {r.relation_type for r in result.relations} == {"shared_authority", "shared_contact"}


def test_unrelated_values_and_same_document_do_not_link():
    result = build_cross_document_graph({
        "a": graph("a", [entity("reference", "REF/1", "p1-b1"), entity("reference", "REF/1", "p1-b2")]),
        "b": graph("b", [entity("reference", "REF/2", "p1-b1")]),
    })
    assert result.relations == ()


def test_output_is_deterministic_and_json_safe():
    documents = {
        "z": graph("z", [entity("reference", "ABC-7", "p2-b1")]),
        "a": graph("a", [entity("reference", "abc-7", "p1-b1")]),
    }
    first = build_cross_document_graph(documents)
    second = build_cross_document_graph(dict(reversed(list(documents.items()))))
    assert first == second
    payload = cross_document_graph_to_dict(first)
    assert payload["relations"][0]["reason"] == "exact normalized reference match"
