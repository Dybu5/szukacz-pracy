import pytest

import filter_jobs


def test_brak_pliku_profilu_daje_czytelny_blad(monkeypatch, tmp_path):
    monkeypatch.setattr(filter_jobs, "PROFIL_PATH", str(tmp_path / "nie-istnieje.txt"))

    with pytest.raises(RuntimeError, match="profil_kandydata"):
        filter_jobs.load_profil()


def test_wczytuje_tresc_profilu(monkeypatch, tmp_path):
    plik = tmp_path / "profil.txt"
    plik.write_text("Testowy profil kandydata", encoding="utf-8")
    monkeypatch.setattr(filter_jobs, "PROFIL_PATH", str(plik))

    assert filter_jobs.load_profil() == "Testowy profil kandydata"
