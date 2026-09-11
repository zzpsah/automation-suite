from ocr.document_structure import build_document_structure, build_page_structure, structure_to_dict
from ocr.region_alignment import OCRSpan


def s(text, x, y, width=40, height=10):
    return OCRSpan(text, "test", x, y, width, height)


def test_page_structure_creates_explicit_blocks():
    blocks, info = build_page_structure(1, [s("Office", 10, 10), s("Order", 10, 35)], page_height=100)
    assert blocks
    assert blocks[0].block_id == "p1-b1"
    assert info["page_number"] == 1


def test_document_structure_preserves_page_order():
    structure = build_document_structure({
        2: [s("Page two", 10, 10)],
        1: [s("Page one", 10, 10)],
    })
    assert structure.reading_order == ("p1-b1", "p2-b1")
    assert structure.pages[0]["page_number"] == 1
    assert structure_to_dict(structure)["table_count"] == 0
