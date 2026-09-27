import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def get_jobs(
    what=None,
    where="Rzeszów",
    limit=30,
    what_or="staż junior trainee intern praktykant absolwent",
    what_exclude='senior lead principal manager "5 lat" "10 lat"',
    max_days_old=None,
):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    url = "https://api.adzuna.com/v1/api/jobs/pl/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": limit,
        "what_or": what_or,
        "what_exclude": what_exclude,
        "where": where,
        "content-type": "application/json",
    }
    if what:
        params["what"] = what
    if max_days_old is not None:
        params["max_days_old"] = max_days_old

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        # Komunikat wyjątku z requests zawiera pełny URL razem z app_key -
        # podajemy tylko typ błędu i kod HTTP, żeby klucz nie trafił do logów.
        status = getattr(e.response, "status_code", None)
        raise RuntimeError(f"Adzuna API: {type(e).__name__} (HTTP {status})") from None

    results = response.json()["results"]
    for job in results:
        job["source"] = "adzuna"
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for job in get_jobs():
        company = job.get("company", {}).get("display_name", "?")
        print(job["title"], "-", company)
