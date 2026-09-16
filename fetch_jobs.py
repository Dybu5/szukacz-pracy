import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

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
    response = requests.get(url, params=params)
    return response.json()["results"]

if __name__ == "__main__":
    jobs = get_jobs()
    for job in jobs:
        company = job.get("company", {}).get("display_name", "?")
        print(job["title"], "-", company)