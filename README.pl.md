# Szukacz Pracy

🇬🇧 [English version](README.md)

Mała aplikacja PWA, która automatycznie szuka staży/pracy w IT i ocenia każdą ofertę pod
kątem profilu kandydata przy pomocy Claude API. Wyniki zapisywane są z historią i
ulubionymi, a apka jest dostępna z telefonu przez Tailscale, więc szukanie i przeglądanie
wyników działa bez komputera.

## Funkcje

- Pobieranie ofert z dwóch źródeł: Adzuna i Jooble
- Ocena i kategoryzacja ofert przez AI ("informatyka" / "pokrewna"), dopasowana do
  profilu kandydata
- Baza danych PostgreSQL (hostowana na Neon) z historią wyszukiwań, więc nic nie ginie między przebiegami
- Ulubione (gwiazdka na ofercie), sortowanie (data/firma/tytuł) i wyszukiwanie tekstowe
- Instalowalna jako PWA (manifest, ciemny interfejs mobile-first)
- Dostęp zdalny przez Tailscale, nie tylko lokalnie

## Stack technologiczny

- Python, Flask
- PostgreSQL (Neon), psycopg2
- Claude API (Anthropic) - ocena i kategoryzacja ofert
- Adzuna API, Jooble API - źródła ofert
- HTML/CSS/vanilla JS (bez frameworka frontendowego)
- PWA (manifest.json)
- Tailscale - dostęp zdalny

## Jak uruchomić

```bash
git clone https://github.com/Dybu5/szukacz-pracy.git
cd szukacz-pracy
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Skopiuj `.env.example` do `.env` i uzupełnij własne klucze:

```
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
ANTHROPIC_API_KEY=
JOOBLE_API_KEY=
EMAIL_ADDRESS=
EMAIL_APP_PASSWORD=
DATABASE_URL=
```

`DATABASE_URL` to connection string do PostgreSQL (w Neon ten z poolerem, czyli z
`-pooler` w nazwie hosta).

Następnie odpal serwer:

```bash
python server.py
```

Aplikacja będzie dostępna pod `http://localhost:5000` (oraz pod adresem w sieci
lokalnej/Tailscale).

## Dlaczego ten projekt

Projekt powstał jako nauka współpracy z asystentem AI przy budowie realnej, kompletnej
aplikacji - nie samych fragmentów kodu, a czegoś z bazą danych, backendem, frontendem
i integracjami z kilkoma zewnętrznymi API.
