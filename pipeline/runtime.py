"""Structured logging and bounded retries; credentials and response bodies are never logged."""
import json
import random
import time
from datetime import UTC, datetime


def log(event, **fields):
    print(json.dumps({"timestamp": datetime.now(UTC).isoformat(), "event": event, **fields}), flush=True)


def retry(operation, retryable, attempts=4, sleep=time.sleep):
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            if not retryable(exc) or attempt == attempts:
                raise
            delay = min(30, 2 ** (attempt - 1)) + random.random()
            log("retry", attempt=attempt, error_type=type(exc).__name__, delay_seconds=round(delay, 2))
            sleep(delay)
