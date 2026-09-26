import os

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DOZWOLONE_SORT = ("data_znalezienia", "title", "company")

FORMAT_DATY = "%Y-%m-%d %H:%M:%S"


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def init_db():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
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
                    kategoria TEXT DEFAULT 'pokrewna'
                )
            """)
    finally:
        conn.close()


def save_jobs(lista_ofert):
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO oferty (title, company, powod, link, source, kategoria)
                VALUES (%(title)s, %(company)s, %(powod)s, %(link)s, %(source)s, %(kategoria)s)
                ON CONFLICT(link) DO UPDATE SET
                    kategoria = excluded.kategoria,
                    powod = excluded.powod
                """,
                lista_ofert,
            )
    finally:
        conn.close()


def get_last_search_time():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT MAX(data_znalezienia) FROM oferty")
            wartosc = cur.fetchone()[0]
    finally:
        conn.close()
    return wartosc.strftime(FORMAT_DATY) if wartosc is not None else None


def get_history(sort_by="data_znalezienia", search=None, only_favorites=False):
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

    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, args)
            rows = cur.fetchall()
    finally:
        conn.close()

    wynik = []
    for row in rows:
        oferta = dict(row)
        # Frontend oczekuje daty jako tekstu "YYYY-MM-DD HH:MM:SS" (tak jak w SQLite),
        # a psycopg2 zwraca obiekt datetime.
        oferta["data_znalezienia"] = oferta["data_znalezienia"].strftime(FORMAT_DATY)
        wynik.append(oferta)
    return wynik


def toggle_favorite(id):
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE oferty SET ulubione = CASE ulubione WHEN 1 THEN 0 ELSE 1 END WHERE id = %s",
                (id,),
            )
    finally:
        conn.close()
