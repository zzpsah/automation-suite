from ocr.runtime_health import check_runtime, runtime_health_to_dict


def test_runtime_health_is_read_only_and_json_safe():
    result = check_runtime()
    assert result.checks
    payload = runtime_health_to_dict(result)
    assert payload["ok"] is True
    assert all("name" in item and "ok" in item and "detail" in item for item in payload["checks"])
