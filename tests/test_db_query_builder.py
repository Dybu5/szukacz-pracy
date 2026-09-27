from db import _build_history_query, DOZWOLONE_SORT, DOZWOLONE_STATUSY


def test_domyslne_sortowanie_malejaco_po_dacie():
    query, args = _build_history_query()
    assert "ORDER BY data_znalezienia DESC" in query
    assert args == []


def test_sortowanie_po_tytule_rosnaco():
    query, _ = _build_history_query(sort_by="title")
    assert "ORDER BY title ASC" in query


def test_niedozwolona_kolumna_sortowania_wraca_do_domyslnej():
    # sort_by spoza whitelisty (np. próba SQL injection) nie trafia do zapytania
    query, _ = _build_history_query(sort_by="id; DROP TABLE oferty;")
    assert "DROP TABLE" not in query
    assert "ORDER BY data_znalezienia DESC" in query


def test_wyszukiwanie_dodaje_warunek_i_argumenty():
    query, args = _build_history_query(search="python")
    assert "title ILIKE %s OR company ILIKE %s" in query
    assert args == ["%python%", "%python%"]


def test_tylko_ulubione_dodaje_warunek():
    query, _ = _build_history_query(only_favorites=True)
    assert "ulubione = 1" in query


def test_dozwolone_sort_i_statusy_sa_niepuste():
    assert len(DOZWOLONE_SORT) > 0
    assert len(DOZWOLONE_STATUSY) > 0
    assert "nowa" in DOZWOLONE_STATUSY
