import os
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DOZWOLONE_SORT = ("data_znalezienia", "title", "company")
DOZWOLONE_STATUSY = ("nowa", "aplikowalem", "rozmowa", "odrzucona")
FORMAT_DATY = "%Y-%m-%d %H:%M:%S"

_pool = None


def _get_pool():
    # Leniwie tworzony pool połączeń (zamiast nowego połączenia TCP+SSL do Neon
    # przy każdym zapytaniu) - jedno realne połączenie starcza na wiele requestów.
    global _pool
    if _pool is None:
        _pool = pg_pool.ThreadedConnectionPool(1, 10, os.getenv("DATABASE_URL"))
    return _pool


@contextmanager
def get_cursor(dict_cursor=False):
    conn = _get_pool().getconn()
    try:
        cursor_factory = RealDictCursor if dict_cursor else None
        with conn, conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
    finally:
        _get_pool().putconn(conn)


def init_db():
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS oferty (
                id SERIAL PRIMARY KEY,
                title TEXT,
                company TEXT,
                powod TEXT,
                link TEXT UNIQUE,
                data_znalezienia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ulubione INTEGER DEFAULT 0,
                source TEXT DEFAULT 'adzuna',
                kategoria TEXT DEFAULT 'pokrewna',
                status TEXT DEFAULT 'nowa',
                notatka TEXT DEFAULT '',
                opis_oferty TEXT DEFAULT ''
            )
        """)
        # Postgres (w przeciwieństwie do SQLite) wspiera IF NOT EXISTS w ALTER TABLE,
        # więc migracja dla już istniejących tabel nie potrzebuje try/except.
        cur.execute("ALTER TABLE oferty ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'nowa'")
        cur.execute("ALTER TABLE oferty ADD COLUMN IF NOT EXISTS notatka TEXT DEFAULT ''")
        cur.execute("ALTER TABLE oferty ADD COLUMN IF NOT EXISTS opis_oferty TEXT DEFAULT ''")


def save_jobs(lista_ofert):
    with get_cursor() as cur:
        cur.executemany(
            """
            INSERT INTO oferty (title, company, powod, link, source, kategoria, opis_oferty)
            VALUES (%(title)s, %(company)s, %(powod)s, %(link)s, %(source)s, %(kategoria)s, %(opis_oferty)s)
            ON CONFLICT(link) DO UPDATE SET
                kategoria = excluded.kategoria,
                powod = excluded.powod,
                opis_oferty = excluded.opis_oferty
            """,
            lista_ofert,
        )


def get_last_search_time():
    with get_cursor() as cur:
        cur.execute("SELECT MAX(data_znalezienia) FROM oferty")
        wartosc = cur.fetchone()[0]
    return wartosc.strftime(FORMAT_DATY) if wartosc is not None else None


def _build_history_query(sort_by="data_znalezienia", search=None, only_favorites=False):
    """Buduje zapytanie SQL i argumenty dla get_history(). Wydzielone jako czysta
    funkcja (bez połączenia z bazą), żeby dało się ją przetestować w pytest bez Neon."""
    if sort_by not in DOZWOLONE_SORT:
        sort_by = "data_znalezienia"
    kierunek = "DESC" if sort_by == "data_znalezienia" else "ASC"

    query = "SELECT * FROM oferty WHERE 1=1"
    args = []

    if search:
        query += " AND (title ILIKE %s OR company ILIKE %s)"
        wzorzec = f"%{search}%"
        args.extend([wzorzec, wzorzec])

    if only_favorites:
        query += " AND ulubione = 1"

    query += f" ORDER BY {sort_by} {kierunek}"
    return query, args


def get_history(sort_by="data_znalezienia", search=None, only_favorites=False):
    query, args = _build_history_query(sort_by, search, only_favorites)

    with get_cursor(dict_cursor=True) as cur:
        cur.execute(query, args)
        rows = cur.fetchall()

    wynik = []
    for row in rows:
        oferta = dict(row)
        # Frontend oczekuje daty jako tekstu "YYYY-MM-DD HH:MM:SS" (tak jak w SQLite),
        # a psycopg2 zwraca obiekt datetime.
        oferta["data_znalezienia"] = oferta["data_znalezienia"].strftime(FORMAT_DATY)
        wynik.append(oferta)
    return wynik


def get_offer_by_id(id):
    with get_cursor(dict_cursor=True) as cur:
        cur.execute("SELECT * FROM oferty WHERE id = %s", (id,))
        row = cur.fetchone()
    if row is None:
        return None
    oferta = dict(row)
    oferta["data_znalezienia"] = oferta["data_znalezienia"].strftime(FORMAT_DATY)
    return oferta


def toggle_favorite(id):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE oferty SET ulubione = CASE ulubione WHEN 1 THEN 0 ELSE 1 END WHERE id = %s",
            (id,),
        )


def update_status(id, status):
    if status not in DOZWOLONE_STATUSY:
        raise ValueError(f"Nieprawidłowy status: {status!r}")
    with get_cursor() as cur:
        cur.execute("UPDATE oferty SET status = %s WHERE id = %s", (status, id))


def update_notatka(id, notatka):
    with get_cursor() as cur:
        cur.execute("UPDATE oferty SET notatka = %s WHERE id = %s", (notatka, id))
