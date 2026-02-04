"""One daily observation at New Delhi; archive availability is handled by a seven-day lag."""
import requests

from pipeline.runtime import retry

URL = "https://archive-api.open-meteo.com/v1/archive"
FIELDS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"]


def fetch(day):
    def request():
        response = requests.get(URL, params={
            "latitude": 28.6139, "longitude": 77.2090,
            "start_date": day, "end_date": day, "daily": ",".join(FIELDS), "timezone": "UTC",
        }, timeout=(10, 60))
        response.raise_for_status()
        return response.json()

    def transient(exc):
        return isinstance(exc, (requests.Timeout, requests.ConnectionError)) or (
            isinstance(exc, requests.HTTPError) and exc.response.status_code in (408, 429, 500, 502, 503, 504)
        )

    return retry(request, transient)


def fixture(day):
    return {"daily": {"time": [day], "temperature_2m_max": [30.0],
                      "temperature_2m_min": [20.0], "precipitation_sum": [0.0]}}
