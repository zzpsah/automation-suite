from govdoc_ocr.backend_policy import choose_backend
from govdoc_ocr.benchmarks import benchmark, cer, wer
from govdoc_ocr.regression import RegressionCase, exact_match
from govdoc_ocr.regions import OCRRegion, normalize_region
from govdoc_ocr.layout import detect_columns, group_lines, layout_summary, order_reading, rows, table_candidates


def test_region_schema_is_normalized():
    region = normalize_region({"text": "आदेश", "bbox": [1, 2, 30, 40], "confidence": .9})
    assert isinstance(region, OCRRegion)
    assert region.to_dict()["bbox"] == [1, 2, 30, 40]
    assert region.to_dict()["text"] == "आदेश"


def test_invalid_region_geometry_is_rejected():
    try: normalize_region({"text": "x", "bbox": [4, 3, 2, 1]})
    except ValueError: return
    raise AssertionError("invalid bbox must be rejected")


def test_backend_policy_is_deterministic():
    assert choose_backend().backend == "tesseract"
    assert choose_backend(available=("tesseract", "paddleocr"), quality_score=.1).backend == "paddleocr"


def test_backend_result_regions_are_serializable():
    result = OCRRegion("region-1", (0, 1, 20, 30), "परीक्षा", .95, source="tesseract")
    assert result.to_dict() == {"id":"region-1","bbox":[0,1,20,30],"text":"परीक्षा","confidence":.95,"block_type":None,"source":"tesseract"}


def test_layout_order_and_table_evidence():
    regions = [
        {"id":"b","bbox":[120,100,200,130],"text":"उत्तर"},
        {"id":"a","bbox":[10,100,100,130],"text":"प्रश्न"},
        {"id":"c","bbox":[10,150,100,180],"text":"अगली पंक्ति"},
    ]
    ordered = order_reading(regions)
    assert [r["id"] for r in ordered] == ["a", "b", "c"]
    assert len(rows(regions)) == 2
    assert len(table_candidates(regions)) == 1


def test_two_column_reading_order_is_deterministic():
    regions = [
        {"id":"r1","bbox":[10,20,90,40],"text":"बायाँ 1"},
        {"id":"r2","bbox":[250,20,330,40],"text":"दायाँ 1"},
        {"id":"r3","bbox":[10,60,90,80],"text":"बायाँ 2"},
        {"id":"r4","bbox":[250,60,330,80],"text":"दायाँ 2"},
    ]
    columns = detect_columns(regions)
    assert [[r["id"] for r in c] for c in columns] == [["r1", "r3"], ["r2", "r4"]]
    assert [r["id"] for r in order_reading(regions)] == ["r1", "r3", "r2", "r4"]


def test_group_lines_uses_vertical_geometry():
    regions = [
        {"id":"b","bbox":[100,11,150,31],"text":"B"},
        {"id":"a","bbox":[10,10,60,30],"text":"A"},
        {"id":"c","bbox":[10,50,60,70],"text":"C"},
    ]
    assert [[r["id"] for r in line] for line in group_lines(regions)] == [["a", "b"], ["c"]]


def test_layout_summary_contains_only_geometry_signals():
    regions = [
        {"id":"a","bbox":[10,10,90,30],"text":"शीर्षक"},
        {"id":"b","bbox":[10,45,90,65],"text":"पाठ"},
    ]
    summary = layout_summary(regions, page_width=100, page_height=100)
    assert summary["region_count"] == 2
    assert summary["line_count"] == 2
    assert summary["column_count"] == 1
    assert summary["reading_order"] == ["a", "b"]
    assert summary["signals"] == {"multi_column": False, "geometry_based": True}


def test_metrics_and_corpus_contract():
    assert cer("abc", "abc") == 0
    assert wer("one two", "one two") == 0
    assert benchmark("abc", "abc")["exact_match"] is True
    case = RegressionCase("x", "sample.pdf", "hello")
    assert exact_match("hello\n", case.expected_text)
