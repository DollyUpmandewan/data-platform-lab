import copy
import json
from unittest.mock import Mock

import pytest
import requests

from pipeline.quality import validate
from pipeline.runner import run
from pipeline.runtime import retry
from pipeline.source import fetch, fixture
from pipeline.storage import AzureStore, LocalStore

DAY = "2025-01-01"


@pytest.mark.parametrize("fault,check", [
    ("null", "nulls"), ("duplicate", "duplicates"), ("drift", "schema_drift"),
    ("empty", "row_count_anomaly"), ("stale", "freshness"),
    ("type", "schema_validation"), ("unequal", "schema_validation"),
    ("range", "value_ranges"),
])
def test_quality_faults(fault, check):
    payload = copy.deepcopy(fixture(DAY))
    daily = payload["daily"]
    if fault == "null":
        daily["temperature_2m_max"] = [None]
    elif fault == "duplicate":
        for values in daily.values():
            values.extend(values[:])
    elif fault == "drift":
        daily["unexpected"] = [1]
    elif fault == "empty":
        daily = {key: [] for key in daily}
        payload["daily"] = daily
    elif fault == "stale":
        daily["time"] = ["2024-12-31"]
    elif fault == "type":
        daily["temperature_2m_max"] = ["hot"]
    elif fault == "unequal":
        daily["time"] = []
    elif fault == "range":
        daily["precipitation_sum"] = [-1]
    _, checks = validate(payload, DAY)
    assert any(c["name"] == check and not c["passed"] for c in checks)


def test_backfill_and_repeat_publication(tmp_path):
    store = LocalStore(tmp_path)
    first = run(store, DAY, "2025-01-03", fixture, "synthetic")
    second = run(store, DAY, "2025-01-03", fixture, "synthetic")
    assert first["passed"] and second["passed"]
    assert len(list(tmp_path.glob("manifests/synthetic/*.json"))) == 3
    manifest = json.loads((tmp_path / f"manifests/synthetic/date={DAY}.json").read_text())
    assert manifest["run_id"] == second["run_id"]
    assert manifest["rows"] == 1
    assert (tmp_path / manifest["data_key"]).exists()


def test_quarantine_preserves_previous_manifest(tmp_path):
    store = LocalStore(tmp_path)
    run(store, DAY, DAY, fixture)
    path = tmp_path / f"manifests/open-meteo/date={DAY}.json"
    previous = path.read_bytes()
    result = run(store, DAY, DAY, lambda day: {"daily": {}})
    assert not result["passed"]
    assert path.read_bytes() == previous
    assert len(list(tmp_path.glob("quarantine/**/*.json"))) == 1


def test_failed_publish_recovery(tmp_path):
    store = LocalStore(tmp_path)
    real_put = store.put

    def fail(key, data):
        if key.startswith("manifests/"):
            raise OSError("injected outage")
        real_put(key, data)

    store.put = fail
    assert not run(store, DAY, DAY, fixture)["passed"]
    assert not list(tmp_path.glob("manifests/**/*.json"))
    store.put = real_put
    assert run(store, DAY, DAY, fixture)["passed"]


def test_partition_failure_does_not_stop_backfill(tmp_path):
    def source(day):
        if day == DAY:
            raise requests.Timeout()
        return fixture(day)
    report = run(LocalStore(tmp_path), DAY, "2025-01-02", source)
    assert [p["status"] for p in report["partitions"]] == ["failed", "passed"]


def test_retry_then_success():
    operation = Mock(side_effect=[requests.Timeout(), "ok"])
    sleep = Mock()
    assert retry(operation, lambda e: isinstance(e, requests.Timeout), sleep=sleep) == "ok"
    assert operation.call_count == 2
    sleep.assert_called_once()


def test_retry_exhaustion():
    operation = Mock(side_effect=requests.Timeout())
    with pytest.raises(requests.Timeout):
        retry(operation, lambda e: True, sleep=lambda _: None)
    assert operation.call_count == 4


def test_permanent_error_no_retry():
    operation = Mock(side_effect=ValueError())
    with pytest.raises(ValueError):
        retry(operation, lambda e: False)
    assert operation.call_count == 1


def test_http_request_contract(monkeypatch):
    response = Mock()
    response.json.return_value = fixture(DAY)
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)
    assert fetch(DAY) == fixture(DAY)
    assert get.call_args.kwargs["params"]["start_date"] == DAY
    assert get.call_args.kwargs["timeout"] == (10, 60)


def test_azure_upload_contract():
    store = AzureStore.__new__(AzureStore)
    store.container = Mock()
    store.put("a.json", b"{}")
    store.container.upload_blob.assert_called_once_with("a.json", b"{}", overwrite=True)


@pytest.mark.parametrize("start,end", [("2025-02-01", DAY), (DAY, "2027-01-01")])
def test_invalid_backfill(tmp_path, start, end):
    with pytest.raises(ValueError):
        run(LocalStore(tmp_path), start, end, fixture)
