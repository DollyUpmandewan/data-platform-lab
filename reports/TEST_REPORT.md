# Quality and validation report

Report date: 22 October 2026.

The validation results cover daily weather collection, data-quality assessment, historical reprocessing and recovery from simulated failures.

## Recorded results

| Assessment | Result |
|---|---|
| Automated validation suite | 19 tests passed |
| Code-quality checks | Passed |
| Demonstration collection | All three requested dates passed |
| Public-source collection, 1–3 January 2025 | All three requested dates passed |
| Repeat historical collection | One published reference retained per date |
| Invalid replacement data | Withheld from publication; previous accepted version preserved |
| Simulated publication interruption | Reprocessing recovered the affected date |
| Partial historical-range failure | Unaffected dates continued successfully |

The public-source collection used Open-Meteo responses and local storage. The Azure upload interface was assessed with a simulated client.

## Data-quality coverage

| Check | Condition assessed |
|---|---|
| Freshness | Observation date differs from the requested date |
| Missing values | A required weather value is absent |
| Duplicates | More than one record has the same date |
| Schema drift | An unexpected daily field appears |
| Schema validation | Numeric values have incorrect types or field arrays have unequal lengths |
| Row count | A daily partition is empty or contains excess records |
| Weather ranges | Precipitation is negative |

## Recovery coverage

The validation suite assessed temporary failure followed by success, retry exhaustion and immediate rejection of permanent errors. It also assessed recovery after a publication failure, preservation of a previous accepted version and independent outcomes across a historical date range.

## Supporting records

[Public-source collection results](live-run.json) and [demonstration results](offline-run.json) contain the date-level quality outcomes. Automated test results are recorded in the JUnit report, with statement coverage recorded separately. The measured statement coverage was 76%.

These results describe the recorded validation run. The automated delivery workflows retain subsequent test and quality reports with their corresponding executions.
