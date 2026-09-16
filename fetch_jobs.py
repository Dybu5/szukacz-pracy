import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_jobs(what="python", where="Rzeszów", limit=20):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    url = "https://api.adzuna.com/v1/api/jobs/pl/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": limit,
        "what": what,
        "where": where,
        "content-type": "application/json",
    }
    response = requests.get(url, params=params)
    return response.json()["results"]

if __name__ == "__main__":
    jobs = get_jobs()
    for job in jobs:
        print(job["title"], "-", job["company"]["display_name"])