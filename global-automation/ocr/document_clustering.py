"""Conservative candidate clustering over cross-document evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from .cross_document import CrossDocumentGraph, CrossDocumentRelation


@dataclass(frozen=True)
class CandidateCluster:
    cluster_id: str
    document_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    relation_types: tuple[str, ...]
    evidence_count: int
    confidence: float
    reason: str


@dataclass(frozen=True)
class CandidateClusterResult:
    clusters: tuple[CandidateCluster, ...]


def _relation_id(relation: CrossDocumentRelation) -> str:
    return "|".join((
        relation.source_document_id,
        relation.target_document_id,
        relation.relation_type,
        relation.source_entity_id,
        relation.target_entity_id,
    ))


def _qualifies(relations: list[CrossDocumentRelation]) -> bool:
    types = {relation.relation_type for relation in relations}
    # A shared authority/contact alone is too broad for a default cluster.
    # Require a direct reference, or two independent evidence types.
    return "shared_reference" in types or len(types) >= 2


def build_candidate_clusters(
    graph: CrossDocumentGraph,
    *,
    min_confidence: float = 0.0,
) -> CandidateClusterResult:
    """Build deterministic connected candidate clusters from cross-document edges.

    Clusters are evidence groups, not assertions that documents belong to the same
    legal case. By default, authority/contact-only edges do not create a cluster;
    a direct shared reference or multiple independent evidence types are required.
    """
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")

    relations = sorted(
        (relation for relation in graph.relations if relation.confidence >= min_confidence),
        key=_relation_id,
    )
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        parent[max(left_root, right_root)] = min(left_root, right_root)

    for relation in relations:
        union(relation.source_document_id, relation.target_document_id)

    grouped: dict[str, list[CrossDocumentRelation]] = {}
    for relation in relations:
        if not _qualifies([relation]):
            continue
        root = find(relation.source_document_id)
        grouped.setdefault(root, []).append(relation)

    # Rebuild groups after filtering: a valid multi-edge path can qualify even
    # when an individual edge is only supporting evidence.
    valid: dict[str, list[CrossDocumentRelation]] = {}
    for relation in relations:
        root = find(relation.source_document_id)
        valid.setdefault(root, []).append(relation)

    clusters: list[CandidateCluster] = []
    for root, group in sorted(valid.items()):
        if not _qualifies(group):
            continue
        documents = sorted({d for relation in group for d in (relation.source_document_id, relation.target_document_id)})
        relation_ids = tuple(sorted(_relation_id(relation) for relation in group))
        relation_types = tuple(sorted({relation.relation_type for relation in group}))
        confidence = round(sum(relation.confidence for relation in group) / len(group), 6)
        cluster_id = "cluster:" + ":".join(documents)
        clusters.append(CandidateCluster(
            cluster_id=cluster_id,
            document_ids=tuple(documents),
            relation_ids=relation_ids,
            relation_types=relation_types,
            evidence_count=len(group),
            confidence=confidence,
            reason="candidate cluster supported by cross-document evidence",
        ))

    clusters.sort(key=lambda cluster: cluster.cluster_id)
    return CandidateClusterResult(tuple(clusters))


def candidate_clusters_to_dict(result: CandidateClusterResult) -> dict:
    return {"clusters": [asdict(cluster) for cluster in result.clusters]}
