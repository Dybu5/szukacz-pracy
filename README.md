# Szukacz Pracy

🇵🇱 [Polska wersja](README.pl.md)

A small PWA that automatically searches for IT internships/jobs and evaluates each
listing against a candidate profile using the Claude API. Results are stored with
history and favorites, and the app is reachable from a phone over Tailscale so the
search can be run and browsed without a computer.

## Features

- Pulls job listings from two sources: Adzuna and Jooble
- Evaluates and categorizes each listing with AI ("informatyka" / "pokrewna" - IT vs.
  related technical fields), matched against a candidate profile
- PostgreSQL database (hosted on Neon) with search history, so nothing gets lost between runs
- Favorites (star a listing), sorting (date/company/title), and text search
- Installable as a PWA (manifest, dark mobile-first UI)
- Reachable remotely over Tailscale, not just on localhost

## Tech stack

- Python, Flask
- PostgreSQL (Neon), psycopg2
- Claude API (Anthropic) - evaluation and categorization of listings
- Adzuna API, Jooble API - job sources
- HTML/CSS/vanilla JS (no frontend framework)
- PWA (manifest.json)
- Tailscale - remote access

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

Then start the server:

```bash
python server.py
```

The app will be available at `http://localhost:5000` (and on your network/Tailscale
address).

## Why this exists

This project started as a way to learn how to work with an AI assistant on a real,
end-to-end application - not just snippets, but something with a database, a backend,
a frontend, and integrations with a few external APIs.
