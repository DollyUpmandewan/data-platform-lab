import argparse
import json
import os
from datetime import date, timedelta
from pathlib import Path

from pipeline.runner import run
from pipeline.source import fetch, fixture
from pipeline.storage import AzureStore, LocalStore


def main():
    parser = argparse.ArgumentParser(description="Reliable daily weather ingestion and bounded backfills")
    default = (date.today() - timedelta(days=7)).isoformat()
    parser.add_argument("--start", default=default)
    parser.add_argument("--end")
    parser.add_argument("--storage", choices=["local", "azure"], default="local")
    parser.add_argument("--root", default="data")
    parser.add_argument("--container", default="weather")
    parser.add_argument("--fixture", action="store_true", help="Synthetic offline data, isolated namespace")
    parser.add_argument("--report", default="reports/latest-run.json")
    args = parser.parse_args()
    store = LocalStore(args.root) if args.storage == "local" else AzureStore(
        args.container, os.environ.get("AZURE_STORAGE_ACCOUNT_URL"))
    report = run(store, args.start, args.end or args.start, fixture if args.fixture else fetch,
                 "synthetic" if args.fixture else "open-meteo")
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
