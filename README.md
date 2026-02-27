# Data Platform Reliability Lab

Daily weather data for New Delhi, collected from Open-Meteo and checked before publication. The pipeline provides a consistent dataset for analysis, alongside a quality report for each collection run.

## Available data

| Field | Meaning |
|---|---|
| Location | New Delhi |
| Date | Observation date in UTC |
| Maximum temperature | Daily maximum air temperature at two metres, in degrees Celsius |
| Minimum temperature | Daily minimum air temperature at two metres, in degrees Celsius |
| Precipitation | Daily total precipitation, in millimetres |

Each published date contains one record. Historical collections cover inclusive date ranges of up to 366 days per run. The default collection date is seven days earlier, allowing time for historical data to become available.

## Quality assurance

Publication requires the expected date, complete required values, unique records, the expected fields and data types, one record per date, and valid weather ranges. A failed check prevents the affected date from being published. Previously published data remains available when a replacement attempt fails.

## Collection results

A run report shows the requested dates, the outcome for each date and the results of individual quality checks. A successful run means every requested date was published. A failed run can still contain successful dates; each date has its own outcome.

Historical dates can be collected again without adding duplicate records to the published dataset. Synthetic demonstration data is identified separately from public-source data.

## Documentation

- [Data flow and architecture](docs/architecture.md)
- [Service continuity and recovery](docs/recovery.md)
- [Quality and validation report](reports/TEST_REPORT.md)

## Platform and source

The project uses Python, Pandas, Azure Blob Storage, Docker and GitHub Actions. A local storage option supports demonstrations and development. Automated delivery workflows validate changes and package versioned container releases.

Weather data comes from the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) and its credited model providers. Data use is subject to the source's [terms and attribution requirements](https://open-meteo.com/en/terms).
