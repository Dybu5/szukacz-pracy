# Szukacz Pracy

🇵🇱 [Polska wersja](README.pl.md)

A small PWA that automatically searches for IT internships/jobs and evaluates each
listing against a candidate profile using the Claude API. Results are stored with
history and favorites, and the app is reachable from a phone over Tailscale so the
search can be run and browsed without a computer.

## Features

- Pulls job listings from two sources: Adzuna and Jooble
- Evaluates and categorizes each listing with AI ("informatyka" / "pokrewna" - IT vs.
  related technical fields), matched against a candidate profile, using structured
  outputs (guaranteed valid JSON, no fence-stripping/parsing errors)
- The search window since the last run grows automatically (e.g. after 3 days offline
  it looks back 3+ days) instead of always re-checking only the last 24h
- PostgreSQL database (hosted on Neon, via a pooled connection) with search history, so
  nothing gets lost between runs
- Favorites (star a listing), a status per listing (new/applied/interview/rejected) and
  free-text notes, sorting (date/company/title), and text search
- Installable as a PWA (manifest, dark mobile-first UI)
- Reachable remotely over Tailscale, not just on localhost
- Optional daily background search via Windows Task Scheduler with a desktop
  notification (`scheduled_search.py`)
- One-click, offer-tailored CV generation: the AI rewrites the summary and reorders
  real skills/achievements to fit a specific listing (never invents experience), and
  the result is rendered as an ATS-friendly, single-column PDF
- Automated tests (`pytest`) running on every push via GitHub Actions

## Tech stack

- Python, Flask (served by gunicorn in production)
- PostgreSQL (Neon), psycopg2 with a connection pool
- Claude API (official `anthropic` SDK, structured outputs) - evaluation and
  categorization of listings
- Adzuna API, Jooble API - job sources
- HTML (Jinja2 templates) / CSS / vanilla JS (no frontend framework)
- xhtml2pdf (pure-Python HTML/CSS to PDF, no native/system dependencies) - CV generation
- PWA (manifest.json)
- Tailscale - remote access
- pytest + GitHub Actions - test suite and CI

## How to run

```bash
git clone https://github.com/Dybu5/szukacz-pracy.git
cd szukacz-pracy
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your own keys:

```
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
ANTHROPIC_API_KEY=
JOOBLE_API_KEY=
DATABASE_URL=
```

`DATABASE_URL` is a PostgreSQL connection string (for Neon, the pooled one with
`-pooler` in the host name).

Copy `profil_kandydata.example.txt` to `profil_kandydata.txt` and fill it in with your
own background/skills/preferences - this is what the AI matches listings against, and
it's gitignored since it's personal information.

For the CV generation feature, also copy `profil_kacpra.example.json` to
`profil_kacpra.json` and fill it in with your real, verifiable CV data (contact info,
skills, education, work history, projects) - never invented facts, since the AI only
rewrites and reorders what's actually there. This file is gitignored too.

Then start the server:

```bash
python server.py
```

The app will be available at `http://localhost:5000` (and on your network/Tailscale
address).

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

Tests mock every external call (Adzuna, Jooble, the database query builder) - they
don't need `.env`, `profil_kandydata.txt`, or a live database, and run the same way in
CI (`.github/workflows/tests.yml`) on every push.

## Scheduled daily search (optional)

`scheduled_search.py` runs the same search the "Szukaj" button triggers, then shows a
Windows toast notification with the results - useful for a daily background check
without opening the app. Register it with Windows Task Scheduler, e.g.:

```bash
schtasks /Create /SC DAILY /TN "SzukaczPracy" /ST 08:00 ^
  /TR "\"C:\path\to\venv\Scripts\pythonw.exe\" \"C:\path\to\scheduled_search.py\"" /F
```

Each run calls the Adzuna, Jooble, and Claude APIs, so it has the same cost as clicking
"Szukaj" once a day.

## Deployment

The app can run in the cloud instead of a local machine - the database is already
hosted on Neon, so the Flask app itself is the only thing that needs a host. A
`Procfile` and `render.yaml` are included for [Render](https://render.com):

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. On Render, create a new **Web Service** from this repository - it picks up
   `render.yaml` automatically.
3. In the service's **Environment** tab, set the same variables as `.env.example`
   (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ANTHROPIC_API_KEY`, `JOOBLE_API_KEY`,
   `DATABASE_URL`) - `render.yaml` declares them but Render always asks you to fill in
   the actual values in the dashboard, it never reads them from your local `.env`.
4. `profil_kandydata.txt` is gitignored, so it won't be in the deployed code either -
   upload it under Render's **Secret Files** (mounted at `profil_kandydata.txt` in the
   service's root) instead of committing it.
5. Deploy. Render builds with `pip install -r requirements.txt` and starts the app with
   gunicorn (`Procfile` / `render.yaml`'s `startCommand`), not the Flask dev server.

Any other host that runs a `Procfile`-style app (Fly.io, Railway, ...) works the same
way - the only two things every host needs are the environment variables above and the
`profil_kandydata.txt` file delivered some way other than git.

## Why this exists

This project started as a way to learn how to work with an AI assistant on a real,
end-to-end application - not just snippets, but something with a database, a backend,
a frontend, and integrations with a few external APIs.
