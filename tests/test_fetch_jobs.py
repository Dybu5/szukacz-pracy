from unittest.mock import MagicMock, patch

from fetch_jobs import get_jobs


def _fake_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@patch("fetch_jobs.requests.get")
def test_get_jobs_dodaje_pole_source(mock_get):
    mock_get.return_value = _fake_response({
        "results": [
            {"title": "Junior Python Developer", "company": {"display_name": "Firma X"}},
            {"title": "Staż w dziale IT", "company": {"display_name": "Firma Y"}},
        ]
    })

    jobs = get_jobs()

    assert len(jobs) == 2
    assert all(job["source"] == "adzuna" for job in jobs)


@patch("fetch_jobs.requests.get")
def test_get_jobs_przekazuje_max_days_old(mock_get):
    mock_get.return_value = _fake_response({"results": []})

    get_jobs(max_days_old=3)

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["max_days_old"] == 3


@patch("fetch_jobs.requests.get")
def test_get_jobs_bez_max_days_old_nie_wysyla_parametru(mock_get):
    mock_get.return_value = _fake_response({"results": []})

    get_jobs()

    _, kwargs = mock_get.call_args
    assert "max_days_old" not in kwargs["params"]


@patch("fetch_jobs.requests.get")
def test_blad_sieci_nie_ujawnia_klucza_api(mock_get):
    import requests

    fake_resp = MagicMock(status_code=401)
    mock_get.side_effect = requests.exceptions.HTTPError(
        "401 Client Error: url=.../?app_key=SEKRETNY_KLUCZ", response=fake_resp
    )

    try:
        get_jobs()
        assert False, "oczekiwano wyjątku"
    except RuntimeError as e:
        assert "SEKRETNY_KLUCZ" not in str(e)
        assert "401" in str(e)
