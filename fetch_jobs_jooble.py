import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def get_jobs_jooble(keywords="staż junior trainee praktykant", location="Rzeszów", limit=30):
    api_key = os.getenv("JOOBLE_API_KEY")

    url = f"https://pl.jooble.org/api/{api_key}"
    body = {"keywords": keywords, "location": location}

    try:
        response = requests.post(url, json=body, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        # Klucz Jooble jest częścią URL-a, a komunikat wyjątku z requests zawiera
        # pełny URL - podajemy tylko typ błędu i kod HTTP.
        status = getattr(e.response, "status_code", None)
        raise RuntimeError(f"Jooble API: {type(e).__name__} (HTTP {status})") from None

    oferty_jooble = response.json().get("jobs", [])[:limit]

    # Ujednolicenie do kształtu zwracanego przez get_jobs() z fetch_jobs.py
    return [
        {
            "title": oferta.get("title"),
            "company": {"display_name": oferta.get("company") or "?"},
            "redirect_url": oferta.get("link"),
            "description": oferta.get("snippet", ""),
            "source": "jooble",
        }
        for oferta in oferty_jooble
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for job in get_jobs_jooble():
        print(job["title"], "-", job["company"]["display_name"])
