# Szukacz Pracy

🇬🇧 [English version](README.md)

Mała aplikacja PWA, która automatycznie szuka staży/pracy w IT i ocenia każdą ofertę pod
kątem profilu kandydata przy pomocy Claude API. Wyniki zapisywane są z historią i
ulubionymi, a apka jest dostępna z telefonu przez Tailscale, więc szukanie i przeglądanie
wyników działa bez komputera.

## Funkcje

- Pobieranie ofert z dwóch źródeł: Adzuna i Jooble
- Ocena i kategoryzacja ofert przez AI ("informatyka" / "pokrewna"), dopasowana do
  profilu kandydata, przez structured outputs (gwarantowany poprawny JSON, bez zdejmowania
  znaczników markdown i błędów parsowania)
- Okno wyszukiwania od ostatniego przebiegu rośnie automatycznie (np. po 3 dniach
  przerwy szuka wstecz 3+ dni), zamiast zawsze sprawdzać tylko ostatnie 24h
- Baza danych PostgreSQL (hostowana na Neon, przez pulę połączeń) z historią
  wyszukiwań, więc nic nie ginie między przebiegami
- Ulubione (gwiazdka na ofercie), status oferty (nowa/aplikowałem/rozmowa/odrzucona) i
  własne notatki, sortowanie (data/firma/tytuł) i wyszukiwanie tekstowe
- Instalowalna jako PWA (manifest, ciemny interfejs mobile-first)
- Dostęp zdalny przez Tailscale, nie tylko lokalnie
- Opcjonalne codzienne wyszukiwanie w tle przez Harmonogram zadań Windows z
  powiadomieniem systemowym (`scheduled_search.py`)
- Generowanie CV dopasowanego do konkretnej oferty jednym kliknięciem: AI przepisuje
  podsumowanie i porządkuje prawdziwe umiejętności/osiągnięcia pod kątem oferty (nigdy
  nie wymyśla doświadczenia), a wynik trafia do PDF w jednej kolumnie, czytelnego dla
  systemów ATS
- Automatyczne testy (`pytest`) uruchamiane przy każdym pushu przez GitHub Actions

## Stack technologiczny

- Python, Flask (w produkcji serwowane przez gunicorn)
- PostgreSQL (Neon), psycopg2 z pulą połączeń
- Claude API (oficjalne SDK `anthropic`, structured outputs) - ocena i kategoryzacja ofert
- Adzuna API, Jooble API - źródła ofert
- HTML (szablony Jinja2) / CSS / vanilla JS (bez frameworka frontendowego)
- xhtml2pdf (czysto-pythonowy render HTML/CSS do PDF, bez natywnych zależności systemowych) - generowanie CV
- PWA (manifest.json)
- Tailscale - dostęp zdalny
- pytest + GitHub Actions - testy i CI

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
DATABASE_URL=
```

`DATABASE_URL` to connection string do PostgreSQL (w Neon ten z poolerem, czyli z
`-pooler` w nazwie hosta).

Skopiuj `profil_kandydata.example.txt` do `profil_kandydata.txt` i uzupełnij własnym
doświadczeniem/umiejętnościami/preferencjami - to z tym AI porównuje oferty, a plik jest
w `.gitignore`, bo zawiera dane osobowe.

Do generowania CV skopiuj też `profil_kacpra.example.json` do `profil_kacpra.json` i
uzupełnij prawdziwymi, weryfikowalnymi danymi z CV (kontakt, umiejętności, edukacja,
doświadczenie, projekty) - nigdy wymyślonymi faktami, bo AI tylko przeredagowuje i
porządkuje to, co tam faktycznie jest. Ten plik też jest w `.gitignore`.

Następnie odpal serwer:

```bash
python server.py
```

Aplikacja będzie dostępna pod `http://localhost:5000` (oraz pod adresem w sieci
lokalnej/Tailscale).

## Testowanie

```bash
pip install -r requirements-dev.txt
pytest
```

Testy mockują wszystkie zewnętrzne wywołania (Adzuna, Jooble, budowanie zapytań do
bazy) - nie potrzebują `.env`, `profil_kandydata.txt` ani żywej bazy danych, i działają
tak samo w CI (`.github/workflows/tests.yml`) przy każdym pushu.

## Codzienne wyszukiwanie w tle (opcjonalne)

`scheduled_search.py` wykonuje to samo wyszukiwanie co przycisk "Szukaj", po czym
pokazuje powiadomienie systemowe Windows z wynikiem - przydatne do codziennego
sprawdzania w tle bez otwierania apki. Rejestracja przez Harmonogram zadań Windows, np.:

```bash
schtasks /Create /SC DAILY /TN "SzukaczPracy" /ST 08:00 ^
  /TR "\"C:\sciezka\do\venv\Scripts\pythonw.exe\" \"C:\sciezka\do\scheduled_search.py\"" /F
```

Każde uruchomienie woła Adzunę, Jooble i Claude API, więc kosztuje tyle samo co jedno
kliknięcie "Szukaj" dziennie.

## Wdrożenie w chmurze

Apka może działać w chmurze zamiast na lokalnym komputerze - baza jest już hostowana na
Neon, więc jedyne co potrzebuje hostingu to sama aplikacja Flask. W repo są `Procfile` i
`render.yaml` pod [Render](https://render.com):

1. Wypchnij repo na GitHub (masz to już zrobione, skoro czytasz to na GitHubie).
2. Na Render stwórz nowy **Web Service** z tego repozytorium - `render.yaml` zostanie
   wykryty automatycznie.
3. W zakładce **Environment** ustaw te same zmienne co w `.env.example`
   (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ANTHROPIC_API_KEY`, `JOOBLE_API_KEY`,
   `DATABASE_URL`) - `render.yaml` je deklaruje, ale Render zawsze prosi o wpisanie
   prawdziwych wartości w panelu, nigdy nie czyta ich z Twojego lokalnego `.env`.
4. `profil_kandydata.txt` jest w `.gitignore`, więc też nie trafi do wdrożonego kodu -
   wgraj go przez **Secret Files** w Render (zamontowany jako `profil_kandydata.txt` w
   katalogu głównym usługi), zamiast commitować.
5. Wdróż. Render buduje przez `pip install -r requirements.txt` i uruchamia gunicornem
   (`Procfile` / `startCommand` w `render.yaml`), nie serwerem deweloperskim Flaska.

Każdy inny hosting działający na `Procfile` (Fly.io, Railway, ...) działa tak samo -
jedyne dwie rzeczy potrzebne wszędzie to zmienne środowiskowe powyżej i dostarczenie
pliku `profil_kandydata.txt` inną drogą niż git.

## Dlaczego ten projekt

Projekt powstał jako nauka współpracy z asystentem AI przy budowie realnej, kompletnej
aplikacji - nie samych fragmentów kodu, a czegoś z bazą danych, backendem, frontendem
i integracjami z kilkoma zewnętrznymi API.
