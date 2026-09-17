from ocr.capability_report import capability_matrix, run_self_test


def test_global_ocr_capability_self_test():
    report = run_self_test()
    assert report["passed"] is True
    assert all(report["checks"].values())


def test_capability_matrix_marks_untrained_scope_honestly():
    matrix = {item.name: item.status for item in capability_matrix()}
    assert matrix["General Indian government coverage"] == "limited"
    assert matrix["ML/VLM fine-tuned government understanding"] == "not yet"
