from unittest.mock import MagicMock, patch

from fetch_jobs_jooble import get_jobs_jooble


def _fake_response(json_data):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@patch("fetch_jobs_jooble.requests.post")
def test_mapowanie_do_wspolnego_ksztaltu(mock_post):
    mock_post.return_value = _fake_response({
        "jobs": [
            {"title": "Junior Dev", "company": "Firma Z", "link": "https://x.pl/1", "snippet": "opis"},
        ]
    })

    jobs = get_jobs_jooble()

    assert jobs == [{
        "title": "Junior Dev",
        "company": {"display_name": "Firma Z"},
        "redirect_url": "https://x.pl/1",
        "description": "opis",
        "source": "jooble",
    }]


@patch("fetch_jobs_jooble.requests.post")
def test_brak_firmy_dostaje_fallback(mock_post):
    mock_post.return_value = _fake_response({
        "jobs": [{"title": "Staż", "company": None, "link": "https://x.pl/2"}]
    })

    jobs = get_jobs_jooble()

    assert jobs[0]["company"]["display_name"] == "?"


@patch("fetch_jobs_jooble.requests.post")
def test_respektuje_limit(mock_post):
    mock_post.return_value = _fake_response({
        "jobs": [{"title": f"Oferta {i}", "company": "F", "link": f"https://x.pl/{i}"} for i in range(10)]
    })

    jobs = get_jobs_jooble(limit=3)

    assert len(jobs) == 3
