from promptgate.dlp.sample_import import SampleImportAdapter


def test_sample_dlp_import():
    rules = SampleImportAdapter("policies/samples").load_rules()
    ids = {rule["id"] for rule in rules}
    assert "sample_employee_id" in ids
    assert "sample_case_number" in ids
    assert any(rule["type"] == "keyword" for rule in rules)
