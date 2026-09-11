from ocr.cross_document import CrossDocumentGraph, CrossDocumentRelation
from ocr.document_clustering import build_candidate_clusters, candidate_clusters_to_dict


def relation(source, target, kind, confidence, source_entity, target_entity):
    return CrossDocumentRelation(source, target, kind, confidence, source_entity, target_entity, "test evidence")


def test_shared_reference_forms_candidate_cluster():
    graph = CrossDocumentGraph((
        relation("a", "b", "shared_reference", 0.96, "r1", "r2"),
        relation("b", "c", "shared_authority", 0.90, "a1", "a2"),
    ))
    result = build_candidate_clusters(graph)
    assert len(result.clusters) == 1
    cluster = result.clusters[0]
    assert cluster.document_ids == ("a", "b", "c")
    assert "shared_reference" in cluster.relation_types
    assert cluster.evidence_count == 2


def test_authority_only_does_not_form_cluster():
    graph = CrossDocumentGraph((
        relation("a", "b", "shared_authority", 0.90, "a1", "a2"),
    ))
    assert build_candidate_clusters(graph).clusters == ()


def test_two_independent_supporting_types_form_cluster():
    graph = CrossDocumentGraph((
        relation("a", "b", "shared_authority", 0.90, "a1", "a2"),
        relation("a", "b", "shared_contact", 0.94, "e1", "e2"),
    ))
    result = build_candidate_clusters(graph)
    assert len(result.clusters) == 1
    assert result.clusters[0].relation_types == ("shared_authority", "shared_contact")


def test_unrelated_documents_remain_separate():
    graph = CrossDocumentGraph((
        relation("a", "b", "shared_reference", 0.96, "r1", "r2"),
        relation("c", "d", "shared_reference", 0.96, "r3", "r4"),
    ))
    result = build_candidate_clusters(graph)
    assert [cluster.document_ids for cluster in result.clusters] == [("a", "b"), ("c", "d")]


def test_result_is_deterministic_and_json_safe():
    graph = CrossDocumentGraph((
        relation("b", "a", "shared_reference", 0.96, "r2", "r1"),
    ))
    first = candidate_clusters_to_dict(build_candidate_clusters(graph))
    second = candidate_clusters_to_dict(build_candidate_clusters(graph))
    assert first == second
    assert isinstance(first["clusters"][0]["document_ids"], tuple)
