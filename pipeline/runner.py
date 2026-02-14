import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from pipeline.quality import validate
from pipeline.runtime import log
from pipeline.source import fetch


def encode(value):
    return json.dumps(value, indent=2, allow_nan=False).encode()


def run(store, start, end, source=fetch, source_name="open-meteo"):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or (last - first).days > 365:
        raise ValueError("Choose an ordered date range of at most 366 days")
    run_id = uuid4().hex
    results = []
    for offset in range((last - first).days + 1):
        day = (first + timedelta(days=offset)).isoformat()
        prefix = f"runs/{run_id}/date={day}"
        result = {"date": day, "status": "failed", "checks": []}
        log("partition_started", run_id=run_id, date=day)
        try:
            payload = source(day)
            raw = encode(payload)
            store.put(f"{prefix}/raw.json", raw)
            frame, checks = validate(payload, day)
            result["checks"] = checks
            if not all(check["passed"] for check in checks):
                store.put(f"quarantine/{run_id}/date={day}.json", raw)
                raise ValueError("DataQualityFailure")
            frame = frame.rename(columns={"time": "date"})
            frame.insert(0, "location", "new-delhi")
            content = frame.to_json(orient="records", lines=True).encode()
            # Immutable run-scoped output; manifest is the only publication point.
            key = f"{prefix}/validated.jsonl"
            store.put(key, content)
            manifest = {"schema_version": 1, "run_id": run_id, "date": day, "rows": len(frame),
                        "source": source_name, "data_key": key, "raw_key": f"{prefix}/raw.json",
                        "sha256": hashlib.sha256(content).hexdigest(),
                        "published_at": datetime.now(UTC).isoformat()}
            store.put(f"manifests/{source_name}/date={day}.json", encode(manifest))
            result.update(status="passed", manifest=manifest)
        except Exception as exc:
            result["error_type"] = type(exc).__name__
            log("partition_failed", run_id=run_id, date=day, error_type=type(exc).__name__)
        results.append(result)
        log("partition_finished", run_id=run_id, date=day, status=result["status"])
    report = {"run_id": run_id, "source": source_name,
              "passed": all(r["status"] == "passed" for r in results), "partitions": results}
    store.put(f"reports/{run_id}.json", encode(report))
    return report
