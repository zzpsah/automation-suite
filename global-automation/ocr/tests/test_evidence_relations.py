from ocr.evidence_relations import extract_evidence_relations
from ocr.document_structure import StructureBlock


def block(text, block_id="b1"):
    return StructureBlock(block_id, 1, "body", text, 10, 10, 100, 20, 0.9)


def test_extracts_only_explicit_relationship_markers():
    result = extract_evidence_relations((
        block("This letter is in continuation of REF-123."),
        block("This order supersedes REF-456.", "b2"),
    ))
    assert [(r.relation_type, r.target_reference) for r in result] == [
        ("continuation_of", "REF-123"),
        ("supersedes", "REF-456"),
    ]
    assert result[0].source_block_id == "b1"


def test_does_not_infer_from_plain_reference():
    assert extract_evidence_relations((block("Reference: REF-123"),)) == ()
