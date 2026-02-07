import pandas as pd

from pipeline.source import FIELDS

EXPECTED = {"time", *FIELDS}


def validate(payload, day):
    checks = []

    def record(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    daily = payload.get("daily") if isinstance(payload, dict) else None
    schema_ok = isinstance(daily, dict) and set(daily) == EXPECTED
    record("schema_drift", schema_ok, "Daily fields must match the version-1 contract exactly")
    if not schema_ok:
        return None, checks
    try:
        if not all(isinstance(value, list) for value in daily.values()):
            raise ValueError("Expected arrays")
        frame = pd.DataFrame(daily)
    except (ValueError, TypeError):
        record("schema_validation", False, "Daily fields must be equal-length arrays")
        return None, checks
    record("nulls", not frame.isna().any().any(), "No required value may be null")
    numeric = all(frame[field].map(lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)).all()
                  for field in FIELDS)
    dates = pd.to_datetime(frame["time"], format="%Y-%m-%d", errors="coerce")
    record("schema_validation", numeric and dates.notna().all(), "ISO dates and numeric weather values")
    record("duplicates", not frame["time"].duplicated().any(), "Natural key: location + date")
    record("row_count_anomaly", len(frame) == 1, f"Expected 1 daily row; observed {len(frame)}")
    record("freshness", len(frame) > 0 and frame["time"].eq(day).all(),
           "Every observation must match the requested partition date")
    if numeric:
        record("value_ranges", ((frame[FIELDS[0]] >= frame[FIELDS[1]]) &
                                (frame[FIELDS[2]] >= 0) &
                                frame[FIELDS].apply(lambda s: s.between(-100, 1000)).all(axis=1)).all(),
               "Finite plausible values; maximum >= minimum; precipitation >= 0")
    return frame, checks
