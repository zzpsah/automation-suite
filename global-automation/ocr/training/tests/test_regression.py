from ocr.training.regression import run


def test_training_corpus_regression():
    report = run("global-automation/ocr/tests/training_corpus.jsonl")
    assert report["passed"], report["failures"]
