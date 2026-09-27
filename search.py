import math
from datetime import datetime, timezone

from fetch_jobs import get_jobs
from fetch_jobs_jooble import get_jobs_jooble
from filter_jobs import evaluate_jobs
from db import get_last_search_time, save_jobs

FORMAT_DATY = "%Y-%m-%d %H:%M:%S"


def _dni_od_ostatniego_wyszukiwania():
    """Ile dni wstecz trzeba szukać, żeby nie ominąć żadnej oferty od ostatniego
    udanego przeszukania. None = jeszcze nigdy nie szukano (pełne przeszukanie)."""
    ostatni = get_last_search_time()
    if ostatni is None:
        return None
    ostatni_dt = datetime.strptime(ostatni, FORMAT_DATY)
    teraz = datetime.now(timezone.utc).replace(tzinfo=None)
    delta_godziny = (teraz - ostatni_dt).total_seconds() / 3600
    return max(1, math.ceil(delta_godziny / 24))


def wykonaj_wyszukiwanie():
    """Pobiera oferty z Adzuny i Jooble, ocenia je przez AI i zapisuje pasujące
    do bazy. Zwraca listę pasujących ofert z TEGO przebiegu (nie całą historię)."""
    jobs = []

    dni = _dni_od_ostatniego_wyszukiwania()
    try:
        if dni is None:
            jobs += get_jobs()
        else:
            jobs += get_jobs(max_days_old=dni)
    except Exception as e:
        print(f"OSTRZEŻENIE: Adzuna nie odpowiedziała poprawnie: {e}")

    try:
        jobs += get_jobs_jooble()
    except Exception as e:
        print(f"OSTRZEŻENIE: Jooble nie odpowiedziało poprawnie: {e}")

    if not jobs:
        raise RuntimeError("Żadne źródło ofert nie odpowiedziało")

    oceny = evaluate_jobs(jobs)

    wyniki = []
    for ocena in oceny:
        # Model może zwrócić id spoza zakresu - pomijamy takie wpisy zamiast wywalać się.
        idx = ocena.get("id")
        if ocena.get("pasuje") and isinstance(idx, int) and 0 <= idx < len(jobs):
            job = jobs[idx]
            wyniki.append({
                "title": job["title"],
                "company": job.get("company", {}).get("display_name", "?"),
                "powod": ocena.get("powod", ""),
                "link": job["redirect_url"],
                "source": job.get("source", "adzuna"),
                "kategoria": ocena.get("kategoria", "pokrewna"),
                "opis_oferty": job.get("description", ""),
            })

    save_jobs(wyniki)
    return wyniki
