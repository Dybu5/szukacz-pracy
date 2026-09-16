import os
import requests
from dotenv import load_dotenv

load_dotenv()  # wczytuje klucze z pliku .env

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

url = "https://api.adzuna.com/v1/api/jobs/pl/search/1"
params = {
    "app_id": APP_ID,
    "app_key": APP_KEY,
    "results_per_page": 10,
    "what": "python",
    "where": "Rzeszów",
    "content-type": "application/json",
}

response = requests.get(url, params=params)
data = response.json()

for job in data["results"]:
    print(job["title"], "-", job["company"]["display_name"])
