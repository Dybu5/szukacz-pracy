import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs.db")

DOZWOLONE_SORT = ("data_znalezienia", "title", "company")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS oferty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    # Migracja dla baz zapisanych przed dodaniem kolumn source/kategoria -
    # CREATE TABLE IF NOT EXISTS nie doda kolumny do istniejącej tabeli.
    try:
        conn.execute("ALTER TABLE oferty ADD COLUMN source TEXT DEFAULT 'adzuna'")
    except sqlite3.OperationalError:
        pass  # kolumna już istnieje
    try:
        conn.execute("ALTER TABLE oferty ADD COLUMN kategoria TEXT DEFAULT 'pokrewna'")
    except sqlite3.OperationalError:
        pass  # kolumna już istnieje
    conn.commit()
    conn.close()


def save_jobs(lista_ofert):
    conn = get_connection()
    conn.executemany(
        """
        INSERT INTO oferty (title, company, powod, link, source, kategoria)
        VALUES (:title, :company, :powod, :link, :source, :kategoria)
        ON CONFLICT(link) DO UPDATE SET
            kategoria = excluded.kategoria,
            powod = excluded.powod
        """,
        lista_ofert,
    )
    conn.commit()
    conn.close()


def get_last_search_time():
    conn = get_connection()
    row = conn.execute("SELECT MAX(data_znalezienia) FROM oferty").fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else None


def get_history(sort_by="data_znalezienia", search=None, only_favorites=False):
    if sort_by not in DOZWOLONE_SORT:
        sort_by = "data_znalezienia"
    kierunek = "DESC" if sort_by == "data_znalezienia" else "ASC"

    query = "SELECT * FROM oferty WHERE 1=1"
    args = []

    if search:
        query += " AND (title LIKE ? OR company LIKE ?)"
        wzorzec = f"%{search}%"
        args.extend([wzorzec, wzorzec])

    if only_favorites:
        query += " AND ulubione = 1"

    query += f" ORDER BY {sort_by} {kierunek}"

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, args).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def toggle_favorite(id):
    conn = get_connection()
    conn.execute(
        "UPDATE oferty SET ulubione = CASE ulubione WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
        (id,),
    )
    conn.commit()
    conn.close()
