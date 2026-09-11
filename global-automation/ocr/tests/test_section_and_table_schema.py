from ocr.document_structure import StructureBlock
from ocr.layout_intelligence import TableCell
from ocr.section_intelligence import detect_section_boundaries
from ocr.table_schema import build_table, table_to_dict


def test_detects_explicit_annexure_marker():
    blocks = [StructureBlock("p2-b1", "heading_or_label", "Annexure A - Details", 2, 0.8)]
    found = detect_section_boundaries(blocks)
    assert found[0].boundary_type == "annexure"
    assert found[0].block_id == "p2-b1"


def test_ignores_unmarked_body():
    blocks = [StructureBlock("p1-b1", "body", "This is ordinary content.", 1, 0.8)]
    assert detect_section_boundaries(blocks) == ()


def test_table_schema_preserves_only_detected_cells():
    table = build_table([
        TableCell(1, 1, "Name", 10, 10, 40, 10),
        TableCell(1, 2, "Value", 60, 10, 40, 10),
        TableCell(2, 1, "A", 10, 25, 40, 10),
    ])
    data = table_to_dict(table)
    assert data["row_count"] == 2
    assert data["column_count"] == 2
    assert len(data["cells"]) == 3
    assert data["cells"][2]["column_span"] == 1
