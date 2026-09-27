from datetime import datetime, timedelta, timezone

import search


def test_pelne_przeszukanie_gdy_baza_pusta(monkeypatch):
    monkeypatch.setattr(search, "get_last_search_time", lambda: None)
    assert search._dni_od_ostatniego_wyszukiwania() is None


def test_minimum_jeden_dzien_nawet_gdy_szukano_godzine_temu(monkeypatch):
    godzine_temu = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)).strftime(search.FORMAT_DATY)
    monkeypatch.setattr(search, "get_last_search_time", lambda: godzine_temu)
    assert search._dni_od_ostatniego_wyszukiwania() == 1


def test_okno_rosnie_z_liczba_dni_przerwy(monkeypatch):
    # To jest dokładnie błąd zgłoszony przez użytkownika: bez tej poprawki okno
    # było zawsze na sztywno 1 dzień, więc oferty z dni 2-3 przepadały.
    trzy_dni_temu = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=3, hours=2)).strftime(search.FORMAT_DATY)
    monkeypatch.setattr(search, "get_last_search_time", lambda: trzy_dni_temu)
    assert search._dni_od_ostatniego_wyszukiwania() == 4  # ceil(3.08...) = 4, z zapasem


def test_wykonaj_wyszukiwanie_pomija_id_spoza_zakresu(monkeypatch):
    monkeypatch.setattr(search, "get_last_search_time", lambda: None)
    monkeypatch.setattr(search, "get_jobs", lambda **kw: [
        {"title": "A", "company": {"display_name": "F1"}, "redirect_url": "https://x/1", "source": "adzuna"},
    ])
    monkeypatch.setattr(search, "get_jobs_jooble", lambda **kw: [])
    monkeypatch.setattr(search, "evaluate_jobs", lambda jobs: [
        {"id": 0, "pasuje": True, "powod": "ok", "kategoria": "informatyka"},
        {"id": 99, "pasuje": True, "powod": "id spoza zakresu", "kategoria": "informatyka"},
    ])
    zapisane = {}
    monkeypatch.setattr(search, "save_jobs", lambda wyniki: zapisane.setdefault("wyniki", wyniki))

    wynik = search.wykonaj_wyszukiwanie()

    assert len(wynik) == 1
    assert wynik[0]["title"] == "A"
    assert zapisane["wyniki"] == wynik


def test_wykonaj_wyszukiwanie_zapisuje_opis_oferty(monkeypatch):
    # /api/report deleguje do wykonaj_wyszukiwanie() - to ta funkcja musi dopisywać
    # opis_oferty (z pola "description" oferty) do słownika przekazywanego do save_jobs().
    monkeypatch.setattr(search, "get_last_search_time", lambda: None)
    monkeypatch.setattr(search, "get_jobs", lambda **kw: [
        {
            "title": "A", "company": {"display_name": "F1"}, "redirect_url": "https://x/1",
            "source": "adzuna", "description": "Pełny opis stanowiska z Adzuny",
        },
    ])
    monkeypatch.setattr(search, "get_jobs_jooble", lambda **kw: [])
    monkeypatch.setattr(search, "evaluate_jobs", lambda jobs: [
        {"id": 0, "pasuje": True, "powod": "ok", "kategoria": "informatyka"},
    ])
    monkeypatch.setattr(search, "save_jobs", lambda wyniki: None)

    wynik = search.wykonaj_wyszukiwanie()

    assert wynik[0]["opis_oferty"] == "Pełny opis stanowiska z Adzuny"


def test_wykonaj_wyszukiwanie_brak_opisu_daje_pusty_string(monkeypatch):
    # Stare wpisy / oferty bez pola "description" nie mogą wywalić zapisu -
    # opis_oferty ma być pustym stringiem, nie brakującym kluczem ani None.
    monkeypatch.setattr(search, "get_last_search_time", lambda: None)
    monkeypatch.setattr(search, "get_jobs", lambda **kw: [
        {"title": "A", "company": {"display_name": "F1"}, "redirect_url": "https://x/1", "source": "adzuna"},
    ])
    monkeypatch.setattr(search, "get_jobs_jooble", lambda **kw: [])
    monkeypatch.setattr(search, "evaluate_jobs", lambda jobs: [
        {"id": 0, "pasuje": True, "powod": "ok", "kategoria": "informatyka"},
    ])
    monkeypatch.setattr(search, "save_jobs", lambda wyniki: None)

    wynik = search.wykonaj_wyszukiwanie()

    assert wynik[0]["opis_oferty"] == ""


def test_wykonaj_wyszukiwanie_rzuca_gdy_oba_zrodla_padly(monkeypatch):
    monkeypatch.setattr(search, "get_last_search_time", lambda: None)

    def wybuchaj(**kw):
        raise RuntimeError("Adzuna API: HTTPError (HTTP 500)")

    monkeypatch.setattr(search, "get_jobs", wybuchaj)
    monkeypatch.setattr(search, "get_jobs_jooble", wybuchaj)

    try:
        search.wykonaj_wyszukiwanie()
        assert False, "oczekiwano wyjątku"
    except RuntimeError as e:
        assert "Żadne źródło" in str(e)
