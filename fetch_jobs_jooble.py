import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def get_jobs_jooble(keywords="staż junior trainee praktykant", location="Rzeszów", limit=30):
    api_key = os.getenv("JOOBLE_API_KEY")

    url = f"https://pl.jooble.org/api/{api_key}"
    headers = {"Content-Type": "application/json"}
    body = {"keywords": keywords, "location": location}

    response = requests.post(url, headers=headers, json=body)
    data = response.json()

    oferty_jooble = data.get("jobs", [])[:limit]

    # Ujednolicenie do kształtu zwracanego przez get_jobs() z fetch_jobs.py
    jobs = []
    for oferta in oferty_jooble:
        jobs.append({
            "title": oferta.get("title"),
            "company": {"display_name": oferta.get("company") or "?"},
            "redirect_url": oferta.get("link"),
            "description": oferta.get("snippet", ""),
            "source": "jooble",
        })
    return jobs


if __name__ == "__main__":
    jobs = get_jobs_jooble()
    for job in jobs:
        print(job["title"], "-", job["company"]["display_name"])
